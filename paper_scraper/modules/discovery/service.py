"""Service layer for discovery module."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError, ValidationError
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.discovery.models import DiscoveryRun, DiscoveryRunStatus
from paper_scraper.modules.discovery.schemas import (
    DiscoveryProfileListResponse,
    DiscoveryProfileSummary,
    DiscoveryRunListResponse,
    DiscoveryRunResponse,
    DiscoveryTriggerResponse,
)
from paper_scraper.modules.notifications.models import NotificationType
from paper_scraper.modules.notifications.service import NotificationService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.service import PaperService
from paper_scraper.modules.projects.service import ProjectService
from paper_scraper.modules.saved_searches.models import SavedSearch

logger = logging.getLogger(__name__)

VALID_SOURCES = {"openalex", "pubmed", "arxiv"}


class DiscoveryService:
    """Service for discovery profile operations and paper auto-import."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Profile Listing
    # =========================================================================

    async def list_active_profiles(
        self,
        organization_id: UUID,
    ) -> DiscoveryProfileListResponse:
        """List all active discovery profiles for an organization."""
        query = (
            select(SavedSearch)
            .options(selectinload(SavedSearch.target_project))
            .where(
                SavedSearch.organization_id == organization_id,
                SavedSearch.auto_import_enabled.is_(True),
            )
            .order_by(desc(SavedSearch.updated_at))
        )
        result = await self.db.execute(query)
        searches = result.scalars().all()

        # Batch-fetch latest run + total imported for each profile
        search_ids = [s.id for s in searches]
        latest_runs = await self._get_latest_runs(search_ids)
        import_totals = await self._get_import_totals(search_ids)

        items = []
        for search in searches:
            latest_run = latest_runs.get(search.id)
            items.append(
                DiscoveryProfileSummary(
                    id=search.id,
                    name=search.name,
                    query=search.query,
                    semantic_description=search.semantic_description,
                    import_sources=search.import_sources or [],
                    target_project_id=search.target_project_id,
                    target_project_name=(
                        search.target_project.name
                        if search.target_project
                        else None
                    ),
                    discovery_frequency=search.discovery_frequency,
                    max_import_per_run=search.max_import_per_run,
                    last_discovery_at=search.last_discovery_at,
                    auto_import_enabled=search.auto_import_enabled,
                    created_at=search.created_at,
                    last_run_status=(
                        latest_run.status.value if latest_run else None
                    ),
                    total_papers_imported=import_totals.get(search.id, 0),
                )
            )

        return DiscoveryProfileListResponse(items=items, total=len(items))

    # =========================================================================
    # Discovery Execution
    # =========================================================================

    async def run_discovery(
        self,
        saved_search_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> DiscoveryTriggerResponse:
        """Run discovery for a saved search across configured sources.

        For each source in import_sources, ingests papers from the external API
        and optionally adds them to the target project.
        """
        # Load saved search with tenant isolation
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == saved_search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()
        if not saved_search:
            raise NotFoundError("SavedSearch", str(saved_search_id))

        sources = saved_search.import_sources or []
        if not sources:
            raise ValidationError("No import sources configured for this discovery profile")

        # Validate sources
        invalid = set(sources) - VALID_SOURCES
        if invalid:
            raise ValidationError(f"Invalid sources: {', '.join(invalid)}")

        paper_service = PaperService(self.db)
        runs: list[DiscoveryRun] = []
        total_imported = 0
        total_added = 0

        for source in sources:
            run = await self._run_single_source(
                saved_search=saved_search,
                source=source,
                organization_id=organization_id,
                user_id=user_id,
                paper_service=paper_service,
            )
            runs.append(run)
            total_imported += run.papers_imported
            total_added += run.papers_added_to_project

        # Update last_discovery_at
        saved_search.last_discovery_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Send notification
        try:
            notification_service = NotificationService(self.db)
            await notification_service.create(
                user_id=user_id,
                organization_id=organization_id,
                type=NotificationType.SYSTEM,
                title=f"Discovery: {saved_search.name}",
                message=(
                    f"Imported {total_imported} papers from {len(sources)} source(s). "
                    f"{total_added} added to project."
                ),
                resource_type="saved_search",
                resource_id=str(saved_search.id),
            )
        except Exception as exc:
            logger.warning("Failed to send discovery notification: %s", exc)

        run_responses = [
            DiscoveryRunResponse.model_validate(r) for r in runs
        ]
        return DiscoveryTriggerResponse(
            saved_search_id=saved_search_id,
            runs=run_responses,
            total_papers_imported=total_imported,
            total_papers_added_to_project=total_added,
            message=f"Discovery completed: {total_imported} papers imported from {len(sources)} source(s)",
        )

    async def _run_single_source(
        self,
        saved_search: SavedSearch,
        source: str,
        organization_id: UUID,
        user_id: UUID,
        paper_service: PaperService,
    ) -> DiscoveryRun:
        """Run discovery for a single external source."""
        run = DiscoveryRun(
            saved_search_id=saved_search.id,
            organization_id=organization_id,
            source=source,
            status=DiscoveryRunStatus.RUNNING,
        )
        self.db.add(run)
        await self.db.flush()

        try:
            # Build query — use the saved search query text
            query = saved_search.query
            max_results = saved_search.max_import_per_run

            # Call appropriate ingestion method
            if source == "openalex":
                ingest_result = await paper_service.ingest_from_openalex(
                    query=query,
                    organization_id=organization_id,
                    max_results=max_results,
                    created_by_id=user_id,
                )
            elif source == "pubmed":
                ingest_result = await paper_service.ingest_from_pubmed(
                    query=query,
                    organization_id=organization_id,
                    max_results=max_results,
                    created_by_id=user_id,
                )
            elif source == "arxiv":
                ingest_result = await paper_service.ingest_from_arxiv(
                    query=query,
                    organization_id=organization_id,
                    max_results=max_results,
                    created_by_id=user_id,
                )
            else:
                raise ValidationError(f"Unknown source: {source}")

            run.papers_found = ingest_result.papers_created + ingest_result.papers_skipped
            run.papers_imported = ingest_result.papers_created
            run.papers_skipped = ingest_result.papers_skipped

            # Add new papers to target project if configured
            added_to_project = 0
            if saved_search.target_project_id and ingest_result.papers_created > 0:
                # Identify newly created papers by querying those added after our snapshot
                new_papers_result = await self.db.execute(
                    select(Paper.id)
                    .where(
                        Paper.organization_id == organization_id,
                        Paper.created_by_id == user_id,
                    )
                    .order_by(desc(Paper.created_at))
                    .limit(ingest_result.papers_created)
                )
                new_paper_ids = [row[0] for row in new_papers_result.all()]

                added_to_project = await self._add_papers_to_project(
                    organization_id=organization_id,
                    project_id=saved_search.target_project_id,
                    paper_ids=new_paper_ids,
                    user_id=user_id,
                )

            run.papers_added_to_project = added_to_project

            if ingest_result.errors:
                run.status = DiscoveryRunStatus.COMPLETED_WITH_ERRORS
                run.error_message = "; ".join(ingest_result.errors[:3])
            else:
                run.status = DiscoveryRunStatus.COMPLETED

            run.completed_at = datetime.now(timezone.utc)

        except Exception as exc:
            logger.exception("Discovery run failed for source %s: %s", source, exc)
            run.status = DiscoveryRunStatus.FAILED
            run.error_message = str(exc)[:500]
            run.completed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def _add_papers_to_project(
        self,
        organization_id: UUID,
        project_id: UUID,
        paper_ids: list[UUID],
        user_id: UUID,
    ) -> int:
        """Add newly imported papers to the target project inbox.

        Args:
            organization_id: Tenant org.
            project_id: Target project.
            paper_ids: Explicit list of paper UUIDs to add.
            user_id: User performing the action.

        Returns:
            Number of papers successfully added to the project.
        """
        if not paper_ids:
            return 0

        try:
            project_service = ProjectService(self.db)
            added = 0
            for paper_id in paper_ids:
                try:
                    await project_service.add_paper_to_project(
                        project_id=project_id,
                        paper_id=paper_id,
                        organization_id=organization_id,
                        stage="inbox",
                        user_id=user_id,
                    )
                    added += 1
                except Exception:
                    # Paper might already be in project (DuplicateError)
                    pass

            return added

        except Exception as exc:
            logger.warning("Failed to add papers to project: %s", exc)
            return 0

    # =========================================================================
    # Run History
    # =========================================================================

    async def list_runs(
        self,
        saved_search_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> DiscoveryRunListResponse:
        """List discovery runs for a saved search."""
        conditions = [
            DiscoveryRun.saved_search_id == saved_search_id,
            DiscoveryRun.organization_id == organization_id,
        ]

        count_query = (
            select(func.count()).select_from(DiscoveryRun).where(*conditions)
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            select(DiscoveryRun)
            .where(*conditions)
            .order_by(desc(DiscoveryRun.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        runs = result.scalars().all()

        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return DiscoveryRunListResponse(
            items=[DiscoveryRunResponse.model_validate(r) for r in runs],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_run(
        self,
        run_id: UUID,
        organization_id: UUID,
    ) -> DiscoveryRunResponse:
        """Get a single discovery run by ID."""
        result = await self.db.execute(
            select(DiscoveryRun).where(
                DiscoveryRun.id == run_id,
                DiscoveryRun.organization_id == organization_id,
            )
        )
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError("DiscoveryRun", str(run_id))
        return DiscoveryRunResponse.model_validate(run)

    # =========================================================================
    # Batch Processing (for cron)
    # =========================================================================

    async def process_all_profiles(
        self,
        frequency: str,
    ) -> dict:
        """Process all active discovery profiles for a given frequency.

        Called by background cron jobs. Skips profiles whose creator is
        inactive to avoid running imports for deactivated accounts.
        """
        result = await self.db.execute(
            select(SavedSearch)
            .join(User, SavedSearch.created_by_id == User.id)
            .where(
                SavedSearch.auto_import_enabled.is_(True),
                SavedSearch.discovery_frequency == frequency,
                User.is_active.is_(True),
            )
        )
        searches = result.scalars().all()

        processed = 0
        succeeded = 0
        failed = 0

        for search in searches:
            try:
                await self.run_discovery(
                    saved_search_id=search.id,
                    organization_id=search.organization_id,
                    user_id=search.created_by_id,
                )
                processed += 1
                succeeded += 1
            except Exception as exc:
                logger.exception(
                    "Failed to process discovery profile %s: %s", search.id, exc
                )
                processed += 1
                failed += 1

        return {
            "frequency": frequency,
            "total_profiles": len(searches),
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
        }

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_latest_runs(
        self,
        search_ids: list[UUID],
    ) -> dict[UUID, DiscoveryRun]:
        """Batch-fetch latest run for each saved search.

        Uses a window function (ROW_NUMBER) to reliably pick the most recent
        run per saved_search_id, avoiding DISTINCT ON ordering pitfalls.
        """
        if not search_ids:
            return {}

        # Subquery: rank runs per saved_search_id by created_at descending
        row_num = (
            func.row_number()
            .over(
                partition_by=DiscoveryRun.saved_search_id,
                order_by=desc(DiscoveryRun.created_at),
            )
            .label("rn")
        )
        subq = (
            select(DiscoveryRun.id, row_num)
            .where(DiscoveryRun.saved_search_id.in_(search_ids))
            .subquery()
        )

        query = (
            select(DiscoveryRun)
            .join(subq, DiscoveryRun.id == subq.c.id)
            .where(subq.c.rn == 1)
        )
        result = await self.db.execute(query)
        runs = result.scalars().all()
        return {r.saved_search_id: r for r in runs}

    async def _get_import_totals(
        self,
        search_ids: list[UUID],
    ) -> dict[UUID, int]:
        """Get total papers imported per saved search."""
        if not search_ids:
            return {}

        query = (
            select(
                DiscoveryRun.saved_search_id,
                func.sum(DiscoveryRun.papers_imported).label("total"),
            )
            .where(DiscoveryRun.saved_search_id.in_(search_ids))
            .group_by(DiscoveryRun.saved_search_id)
        )
        result = await self.db.execute(query)
        return {row.saved_search_id: row.total or 0 for row in result.all()}
