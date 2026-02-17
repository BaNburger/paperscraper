"""Service layer for integration connectors and Zotero synchronization."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError, ValidationError
from paper_scraper.modules.integrations.connectors.zotero import (
    ZoteroConnector,
    ZoteroCredentials,
)
from paper_scraper.modules.integrations.models import (
    IntegrationConnector,
    ZoteroConnection,
    ZoteroConnectionStatus,
    ZoteroItemLink,
    ZoteroSyncDirection,
    ZoteroSyncRun,
    ZoteroSyncRunStatus,
)
from paper_scraper.modules.integrations.schemas import (
    IntegrationConnectorCreate,
    IntegrationConnectorListResponse,
    IntegrationConnectorResponse,
    IntegrationConnectorUpdate,
    ZoteroConnectionStatusResponse,
    ZoteroConnectRequest,
)
from paper_scraper.modules.library.models import (
    LibraryCollection,
    LibraryCollectionItem,
    PaperTag,
)
from paper_scraper.modules.papers.models import Paper, PaperAuthor, PaperSource


class IntegrationService:
    """Service for managing tenant-scoped external integrations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.zotero_connector = ZoteroConnector()

    # =========================================================================
    # Existing connector configuration APIs
    # =========================================================================

    async def create_connector(
        self,
        organization_id: UUID,
        data: IntegrationConnectorCreate,
    ) -> IntegrationConnector:
        """Create a connector."""
        connector = IntegrationConnector(
            organization_id=organization_id,
            connector_type=data.connector_type,
            config_json=data.config_json,
            status=data.status,
        )
        self.db.add(connector)
        await self.db.flush()
        await self.db.refresh(connector)
        return connector

    async def update_connector(
        self,
        connector_id: UUID,
        organization_id: UUID,
        data: IntegrationConnectorUpdate,
    ) -> IntegrationConnector:
        """Update an existing connector."""
        connector = await self.get_connector(connector_id, organization_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(connector, key, value)

        await self.db.flush()
        await self.db.refresh(connector)
        return connector

    async def get_connector(
        self,
        connector_id: UUID,
        organization_id: UUID,
    ) -> IntegrationConnector:
        """Get a connector with tenant isolation."""
        result = await self.db.execute(
            select(IntegrationConnector).where(
                IntegrationConnector.id == connector_id,
                IntegrationConnector.organization_id == organization_id,
            )
        )
        connector = result.scalar_one_or_none()
        if connector is None:
            raise NotFoundError("IntegrationConnector", str(connector_id))
        return connector

    async def list_connectors(
        self,
        organization_id: UUID,
    ) -> IntegrationConnectorListResponse:
        """List connectors for organization."""
        result = await self.db.execute(
            select(IntegrationConnector)
            .where(IntegrationConnector.organization_id == organization_id)
            .order_by(IntegrationConnector.created_at.desc())
        )
        items = [
            IntegrationConnectorResponse.model_validate(connector)
            for connector in result.scalars().all()
        ]
        return IntegrationConnectorListResponse(items=items, total=len(items))

    # =========================================================================
    # Zotero integration
    # =========================================================================

    async def connect_zotero(
        self,
        organization_id: UUID,
        data: ZoteroConnectRequest,
    ) -> ZoteroConnection:
        """Create or update Zotero credentials and verify connectivity."""
        creds = ZoteroCredentials(
            user_id=data.user_id.strip(),
            api_key=data.api_key.strip(),
            base_url=data.base_url.strip(),
            library_type=data.library_type.strip(),
        )
        if creds.library_type not in {"users", "groups"}:
            raise ValidationError("library_type must be either 'users' or 'groups'")

        try:
            await self.zotero_connector.verify_connection(creds)
        except Exception as exc:
            raise ValidationError(f"Failed to verify Zotero credentials: {exc}") from exc

        existing = await self.get_zotero_connection(organization_id)
        if existing:
            existing.user_id = creds.user_id
            existing.api_key = creds.api_key
            existing.base_url = creds.base_url
            existing.library_type = creds.library_type
            existing.status = ZoteroConnectionStatus.CONNECTED
            existing.last_error = None
            existing.updated_at = datetime.now(UTC)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        connection = ZoteroConnection(
            organization_id=organization_id,
            user_id=creds.user_id,
            api_key=creds.api_key,
            base_url=creds.base_url,
            library_type=creds.library_type,
            status=ZoteroConnectionStatus.CONNECTED,
        )
        self.db.add(connection)
        await self.db.flush()
        await self.db.refresh(connection)
        return connection

    async def get_zotero_connection(self, organization_id: UUID) -> ZoteroConnection | None:
        """Fetch Zotero connection for organization."""
        result = await self.db.execute(
            select(ZoteroConnection).where(ZoteroConnection.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_zotero_status(self, organization_id: UUID) -> ZoteroConnectionStatusResponse:
        """Return normalized connection status payload."""
        connection = await self.get_zotero_connection(organization_id)
        if not connection:
            return ZoteroConnectionStatusResponse(
                connected=False,
                status=ZoteroConnectionStatus.DISCONNECTED,
            )
        return ZoteroConnectionStatusResponse(
            connected=connection.status == ZoteroConnectionStatus.CONNECTED,
            status=connection.status,
            user_id=connection.user_id,
            base_url=connection.base_url,
            library_type=connection.library_type,
            last_error=connection.last_error,
            last_synced_at=connection.last_synced_at,
        )

    async def get_sync_run(self, run_id: UUID, organization_id: UUID) -> ZoteroSyncRun:
        """Fetch a sync run with tenant isolation."""
        result = await self.db.execute(
            select(ZoteroSyncRun).where(
                ZoteroSyncRun.id == run_id,
                ZoteroSyncRun.organization_id == organization_id,
            )
        )
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError("ZoteroSyncRun", str(run_id))
        return run

    async def sync_zotero_outbound(
        self,
        organization_id: UUID,
        triggered_by: UUID,
        paper_ids: list[UUID] | None = None,
    ) -> ZoteroSyncRun:
        """Push local papers to Zotero."""
        connection = await self.get_zotero_connection(organization_id)
        if not connection:
            raise ValidationError("Zotero is not connected for this organization")

        run = await self._create_run(
            organization_id=organization_id,
            direction=ZoteroSyncDirection.OUTBOUND,
            triggered_by=triggered_by,
        )

        try:
            creds = ZoteroCredentials(
                user_id=connection.user_id,
                api_key=connection.api_key,
                base_url=connection.base_url,
                library_type=connection.library_type,
            )
            query = (
                select(Paper)
                .options(selectinload(Paper.authors).selectinload(PaperAuthor.author))
                .where(Paper.organization_id == organization_id)
                .order_by(Paper.created_at.desc())
            )
            if paper_ids:
                query = query.where(Paper.id.in_(paper_ids))
            paper_result = await self.db.execute(query)
            papers = list(paper_result.scalars().all())

            link_result = await self.db.execute(
                select(ZoteroItemLink).where(ZoteroItemLink.organization_id == organization_id)
            )
            links = list(link_result.scalars().all())
            active_link_by_paper = {
                link.paper_id: link for link in links if link.is_active
            }

            stats = {
                "total": len(papers),
                "synced": 0,
                "failed": 0,
                "errors": [],
            }

            for paper in papers:
                tag_result = await self.db.execute(
                    select(PaperTag.tag).where(
                        PaperTag.organization_id == organization_id,
                        PaperTag.paper_id == paper.id,
                    )
                )
                tags = [row[0] for row in tag_result.all()]
                local_link = active_link_by_paper.get(paper.id)
                authors = [
                    entry.author.name
                    for entry in sorted(paper.authors, key=lambda a: a.position)
                    if entry.author and entry.author.name
                ]
                payload = self.zotero_connector.build_item_payload(
                    title=paper.title,
                    abstract=paper.abstract,
                    doi=paper.doi,
                    journal=paper.journal,
                    publication_date=paper.publication_date,
                    authors=authors,
                    tags=tags,
                )

                try:
                    response = await self.zotero_connector.upsert_item(
                        creds=creds,
                        item_payload=payload,
                        zotero_item_key=local_link.zotero_item_key if local_link else None,
                    )
                    item_key = response.get("item_key") or (local_link.zotero_item_key if local_link else None)
                    if not item_key:
                        raise ValidationError("Zotero API did not return an item key")

                    if local_link:
                        local_link.zotero_item_key = item_key
                        local_link.is_active = True
                        local_link.last_seen_at = datetime.now(UTC)
                    else:
                        self.db.add(
                            ZoteroItemLink(
                                organization_id=organization_id,
                                paper_id=paper.id,
                                zotero_item_key=item_key,
                                is_active=True,
                            )
                        )
                    stats["synced"] += 1
                except Exception as exc:
                    stats["failed"] += 1
                    stats["errors"].append({"paper_id": str(paper.id), "error": str(exc)[:300]})

            connection.last_synced_at = datetime.now(UTC)
            connection.status = ZoteroConnectionStatus.CONNECTED
            connection.last_error = None
            run.status = (
                ZoteroSyncRunStatus.SUCCEEDED
                if stats["failed"] == 0 or stats["synced"] > 0
                else ZoteroSyncRunStatus.FAILED
            )
            run.completed_at = datetime.now(UTC)
            run.stats_json = stats
            if stats["failed"] > 0 and stats["synced"] == 0:
                run.error_message = "Outbound sync failed for all selected papers"

            await self.db.flush()
            await self.db.refresh(run)
            return run
        except Exception as exc:
            run.status = ZoteroSyncRunStatus.FAILED
            run.completed_at = datetime.now(UTC)
            run.error_message = str(exc)[:2000]
            run.stats_json = {"total": 0, "synced": 0, "failed": 0, "errors": [str(exc)[:300]]}
            connection.status = ZoteroConnectionStatus.ERROR
            connection.last_error = str(exc)[:2000]
            await self.db.flush()
            await self.db.refresh(run)
            return run

    async def sync_zotero_inbound(
        self,
        organization_id: UUID,
        triggered_by: UUID,
    ) -> ZoteroSyncRun:
        """Pull Zotero updates and merge non-destructively into local entities."""
        connection = await self.get_zotero_connection(organization_id)
        if not connection:
            raise ValidationError("Zotero is not connected for this organization")

        run = await self._create_run(
            organization_id=organization_id,
            direction=ZoteroSyncDirection.INBOUND,
            triggered_by=triggered_by,
        )

        try:
            creds = ZoteroCredentials(
                user_id=connection.user_id,
                api_key=connection.api_key,
                base_url=connection.base_url,
                library_type=connection.library_type,
            )
            items = await self.zotero_connector.list_items(creds=creds, since=None, limit=100)
            seen_item_keys: set[str] = set()
            stats = {
                "total_items": len(items),
                "papers_created": 0,
                "papers_merged": 0,
                "tags_added": 0,
                "links_deactivated": 0,
                "errors": [],
            }

            link_result = await self.db.execute(
                select(ZoteroItemLink).where(ZoteroItemLink.organization_id == organization_id)
            )
            existing_links = list(link_result.scalars().all())
            link_by_key = {link.zotero_item_key: link for link in existing_links}

            for item in items:
                try:
                    item_key = str(item.get("key", ""))
                    if item_key:
                        seen_item_keys.add(item_key)

                    data = item.get("data", item)
                    if not isinstance(data, dict):
                        continue
                    item_type = str(data.get("itemType", "")).lower()
                    if item_type == "note":
                        continue

                    paper, was_created, was_merged = await self._find_or_create_paper_from_zotero(
                        organization_id=organization_id,
                        item_key=item_key,
                        data=data,
                    )
                    if was_created:
                        stats["papers_created"] += 1
                    elif was_merged:
                        stats["papers_merged"] += 1

                    # Merge tags (union)
                    for tag in self._extract_zotero_tags(data):
                        exists_result = await self.db.execute(
                            select(PaperTag).where(
                                PaperTag.organization_id == organization_id,
                                PaperTag.paper_id == paper.id,
                                PaperTag.tag == tag,
                            )
                        )
                        if not exists_result.scalar_one_or_none():
                            self.db.add(
                                PaperTag(
                                    organization_id=organization_id,
                                    paper_id=paper.id,
                                    tag=tag,
                                    created_by=triggered_by,
                                )
                            )
                            stats["tags_added"] += 1

                    # Merge collection memberships (union) using key-derived local collections.
                    collection_keys = data.get("collections") or []
                    if isinstance(collection_keys, list):
                        for key in collection_keys:
                            if not isinstance(key, str) or not key:
                                continue
                            collection = await self._get_or_create_zotero_collection(
                                organization_id=organization_id,
                                created_by=triggered_by,
                                collection_key=key,
                            )
                            membership = await self.db.execute(
                                select(LibraryCollectionItem).where(
                                    LibraryCollectionItem.organization_id == organization_id,
                                    LibraryCollectionItem.collection_id == collection.id,
                                    LibraryCollectionItem.paper_id == paper.id,
                                )
                            )
                            if not membership.scalar_one_or_none():
                                self.db.add(
                                    LibraryCollectionItem(
                                        organization_id=organization_id,
                                        collection_id=collection.id,
                                        paper_id=paper.id,
                                        created_by=triggered_by,
                                    )
                                )

                    # Upsert item link and mark active.
                    link = link_by_key.get(item_key)
                    if link:
                        link.paper_id = paper.id
                        link.is_active = True
                        link.last_seen_at = datetime.now(UTC)
                    else:
                        link = ZoteroItemLink(
                            organization_id=organization_id,
                            paper_id=paper.id,
                            zotero_item_key=item_key,
                            is_active=True,
                        )
                        self.db.add(link)
                        link_by_key[item_key] = link
                except Exception as exc:
                    stats["errors"].append(str(exc)[:300])

            # Deletions in Zotero -> mark links inactive (do not delete local papers).
            for link in existing_links:
                if link.zotero_item_key and link.zotero_item_key not in seen_item_keys and link.is_active:
                    link.is_active = False
                    stats["links_deactivated"] += 1

            connection.last_synced_at = datetime.now(UTC)
            connection.status = ZoteroConnectionStatus.CONNECTED
            connection.last_error = None

            run.status = ZoteroSyncRunStatus.SUCCEEDED
            run.completed_at = datetime.now(UTC)
            run.stats_json = stats
            await self.db.flush()
            await self.db.refresh(run)
            return run
        except Exception as exc:
            run.status = ZoteroSyncRunStatus.FAILED
            run.completed_at = datetime.now(UTC)
            run.error_message = str(exc)[:2000]
            run.stats_json = {"errors": [str(exc)[:300]]}
            connection.status = ZoteroConnectionStatus.ERROR
            connection.last_error = str(exc)[:2000]
            await self.db.flush()
            await self.db.refresh(run)
            return run

    # =========================================================================
    # Internal helpers
    # =========================================================================

    async def _create_run(
        self,
        organization_id: UUID,
        direction: ZoteroSyncDirection,
        triggered_by: UUID,
    ) -> ZoteroSyncRun:
        """Create and persist a new Zotero sync run."""
        run = ZoteroSyncRun(
            organization_id=organization_id,
            direction=direction,
            status=ZoteroSyncRunStatus.RUNNING,
            triggered_by=triggered_by,
            started_at=datetime.now(UTC),
            stats_json={},
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def _find_or_create_paper_from_zotero(
        self,
        organization_id: UUID,
        item_key: str,
        data: dict,
    ) -> tuple[Paper, bool, bool]:
        """Find a paper by DOI/title or create a new one from inbound Zotero item."""
        doi = str(data.get("DOI", "")).strip() or None
        title = str(data.get("title", "")).strip() or "Untitled Zotero Item"

        paper: Paper | None = None
        if doi:
            result = await self.db.execute(
                select(Paper).where(
                    Paper.organization_id == organization_id,
                    Paper.doi == doi,
                )
            )
            paper = result.scalar_one_or_none()

        if not paper and title:
            result = await self.db.execute(
                select(Paper).where(
                    Paper.organization_id == organization_id,
                    func.lower(Paper.title) == title.lower(),
                )
            )
            paper = result.scalar_one_or_none()

        if not paper:
            paper = Paper(
                organization_id=organization_id,
                source=PaperSource.MANUAL,
                source_id=f"zotero:{item_key}" if item_key else None,
                doi=doi,
                title=title,
                abstract=str(data.get("abstractNote", "")).strip() or None,
                journal=str(data.get("publicationTitle", "")).strip() or None,
                publication_date=self._parse_zotero_date(str(data.get("date", "")).strip()),
                raw_metadata={"zotero": data},
            )
            self.db.add(paper)
            await self.db.flush()
            return paper, True, False

        # Non-destructive merge: fill missing local values only.
        merged = False
        if not paper.doi and doi:
            paper.doi = doi
            merged = True
        if not paper.abstract and data.get("abstractNote"):
            paper.abstract = str(data.get("abstractNote")).strip() or paper.abstract
            merged = True
        if not paper.journal and data.get("publicationTitle"):
            paper.journal = str(data.get("publicationTitle")).strip() or paper.journal
            merged = True
        if not paper.publication_date and data.get("date"):
            parsed = self._parse_zotero_date(str(data.get("date")).strip())
            if parsed:
                paper.publication_date = parsed
                merged = True
        return paper, False, merged

    async def _get_or_create_zotero_collection(
        self,
        organization_id: UUID,
        created_by: UUID,
        collection_key: str,
    ) -> LibraryCollection:
        """Create deterministic local collection for Zotero collection key."""
        name = f"Zotero {collection_key}"
        result = await self.db.execute(
            select(LibraryCollection).where(
                LibraryCollection.organization_id == organization_id,
                LibraryCollection.name == name,
            )
        )
        collection = result.scalar_one_or_none()
        if collection:
            return collection

        collection = LibraryCollection(
            organization_id=organization_id,
            name=name,
            description="Auto-created from Zotero inbound sync",
            created_by=created_by,
        )
        self.db.add(collection)
        await self.db.flush()
        await self.db.refresh(collection)
        return collection

    def _extract_zotero_tags(self, data: dict) -> list[str]:
        """Extract normalized tags from Zotero item payload."""
        tags_raw = data.get("tags") or []
        if not isinstance(tags_raw, list):
            return []
        tags: list[str] = []
        for tag in tags_raw:
            if isinstance(tag, dict):
                value = str(tag.get("tag", "")).strip().lower()
            else:
                value = str(tag).strip().lower()
            if value:
                tags.append(value)
        return sorted(set(tags))

    def _parse_zotero_date(self, date_str: str) -> datetime | None:
        """Parse Zotero date strings into datetime when possible."""
        if not date_str:
            return None
        normalized = date_str.strip()
        if not normalized:
            return None

        # Normalize common separators first.
        normalized = normalized.replace("/", "-").replace(".", "-")

        # Handle full ISO-like strings.
        iso_candidate = normalized.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(iso_candidate)
        except ValueError:
            pass

        # Try common explicit formats.
        for fmt, length in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
            try:
                return datetime.strptime(normalized[:length], fmt)
            except ValueError:
                continue

        # Fallback: extract YYYY[-MM[-DD]] from free-form Zotero values.
        match = re.search(r"(?P<year>\d{4})(?:-(?P<month>\d{1,2}))?(?:-(?P<day>\d{1,2}))?", normalized)
        if not match:
            return None

        year = int(match.group("year"))
        month = int(match.group("month")) if match.group("month") else 1
        day = int(match.group("day")) if match.group("day") else 1
        try:
            return datetime(year=year, month=month, day=day)
        except ValueError:
            return None
