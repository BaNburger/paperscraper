"""Service layer for authors module."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.authors.models import AuthorContact, ContactOutcome
from paper_scraper.modules.authors.schemas import (
    AuthorContactStats,
    AuthorDetailResponse,
    AuthorListResponse,
    AuthorPaperSummary,
    AuthorProfileResponse,
    ContactCreate,
    ContactUpdate,
    ContactWithUserResponse,
    EnrichmentResult,
)
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor


class AuthorService:
    """Service for author management and contact tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Author Profile
    # =========================================================================

    async def get_author(
        self,
        author_id: UUID,
    ) -> Author | None:
        """Get an author by ID."""
        result = await self.db.execute(select(Author).where(Author.id == author_id))
        return result.scalar_one_or_none()

    async def get_author_profile(
        self,
        author_id: UUID,
        organization_id: UUID,
    ) -> AuthorProfileResponse | None:
        """Get author profile with computed stats."""
        author = await self.get_author(author_id)
        if not author:
            return None

        # Get paper count
        paper_count_result = await self.db.execute(
            select(func.count())
            .select_from(PaperAuthor)
            .join(Paper)
            .where(
                PaperAuthor.author_id == author_id,
                Paper.organization_id == organization_id,
            )
        )
        paper_count = paper_count_result.scalar() or 0

        # Get contact stats for this org
        contact_stats = await self._get_contact_stats(author_id, organization_id)

        return AuthorProfileResponse(
            id=author.id,
            name=author.name,
            orcid=author.orcid,
            openalex_id=author.openalex_id,
            affiliations=author.affiliations,
            h_index=author.h_index,
            citation_count=author.citation_count,
            works_count=author.works_count,
            created_at=author.created_at,
            updated_at=author.updated_at,
            paper_count=paper_count,
            recent_contacts_count=contact_stats.get("recent_count", 0),
            last_contact_date=contact_stats.get("last_contact_date"),
        )

    async def get_author_detail(
        self,
        author_id: UUID,
        organization_id: UUID,
    ) -> AuthorDetailResponse | None:
        """Get full author detail with papers and contacts."""
        author = await self.get_author(author_id)
        if not author:
            return None

        # Get papers for this author in this org
        papers_result = await self.db.execute(
            select(Paper, PaperAuthor.is_corresponding)
            .join(PaperAuthor)
            .where(
                PaperAuthor.author_id == author_id,
                Paper.organization_id == organization_id,
            )
            .order_by(Paper.publication_date.desc().nullslast())
        )
        papers_data = papers_result.all()

        papers = [
            AuthorPaperSummary(
                id=paper.id,
                title=paper.title,
                doi=paper.doi,
                publication_date=paper.publication_date,
                journal=paper.journal,
                is_corresponding=is_corresponding,
            )
            for paper, is_corresponding in papers_data
        ]

        # Get contacts
        contacts_result = await self.db.execute(
            select(AuthorContact)
            .options(selectinload(AuthorContact.contacted_by))
            .where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
            )
            .order_by(AuthorContact.contact_date.desc())
        )
        contacts_data = contacts_result.scalars().all()

        contacts = [
            ContactWithUserResponse(
                id=c.id,
                author_id=c.author_id,
                organization_id=c.organization_id,
                contacted_by_id=c.contacted_by_id,
                contact_type=c.contact_type,
                contact_date=c.contact_date,
                subject=c.subject,
                notes=c.notes,
                outcome=c.outcome,
                follow_up_date=c.follow_up_date,
                paper_id=c.paper_id,
                created_at=c.created_at,
                updated_at=c.updated_at,
                contacted_by_name=c.contacted_by.full_name if c.contacted_by else None,
                contacted_by_email=c.contacted_by.email if c.contacted_by else None,
            )
            for c in contacts_data
        ]

        # Get contact stats
        contact_stats = await self._get_contact_stats(author_id, organization_id)

        return AuthorDetailResponse(
            id=author.id,
            name=author.name,
            orcid=author.orcid,
            openalex_id=author.openalex_id,
            affiliations=author.affiliations,
            h_index=author.h_index,
            citation_count=author.citation_count,
            works_count=author.works_count,
            created_at=author.created_at,
            updated_at=author.updated_at,
            paper_count=len(papers),
            recent_contacts_count=contact_stats.get("recent_count", 0),
            last_contact_date=contact_stats.get("last_contact_date"),
            papers=papers,
            contacts=contacts,
        )

    async def list_authors(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> AuthorListResponse:
        """List authors with papers in this organization."""
        # Base query - authors who have papers in this org
        base_query = (
            select(Author)
            .join(PaperAuthor)
            .join(Paper)
            .where(Paper.organization_id == organization_id)
            .distinct()
        )

        if search:
            search_filter = f"%{search}%"
            base_query = base_query.where(Author.name.ilike(search_filter))

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = base_query.order_by(Author.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        authors = list(result.scalars().all())

        # Build response with stats
        items = []
        for author in authors:
            # Get paper count for this org
            paper_count_result = await self.db.execute(
                select(func.count())
                .select_from(PaperAuthor)
                .join(Paper)
                .where(
                    PaperAuthor.author_id == author.id,
                    Paper.organization_id == organization_id,
                )
            )
            paper_count = paper_count_result.scalar() or 0

            contact_stats = await self._get_contact_stats(author.id, organization_id)

            items.append(
                AuthorProfileResponse(
                    id=author.id,
                    name=author.name,
                    orcid=author.orcid,
                    openalex_id=author.openalex_id,
                    affiliations=author.affiliations,
                    h_index=author.h_index,
                    citation_count=author.citation_count,
                    works_count=author.works_count,
                    created_at=author.created_at,
                    updated_at=author.updated_at,
                    paper_count=paper_count,
                    recent_contacts_count=contact_stats.get("recent_count", 0),
                    last_contact_date=contact_stats.get("last_contact_date"),
                )
            )

        return AuthorListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    # =========================================================================
    # Contact Tracking
    # =========================================================================

    async def create_contact(
        self,
        author_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        data: ContactCreate,
    ) -> AuthorContact:
        """Log a contact with an author."""
        # Verify author exists
        author = await self.get_author(author_id)
        if not author:
            raise NotFoundError("Author", author_id)

        contact = AuthorContact(
            author_id=author_id,
            organization_id=organization_id,
            contacted_by_id=user_id,
            contact_type=data.contact_type,
            contact_date=data.contact_date or datetime.utcnow(),
            subject=data.subject,
            notes=data.notes,
            outcome=data.outcome,
            follow_up_date=data.follow_up_date,
            paper_id=data.paper_id,
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self,
        contact_id: UUID,
        organization_id: UUID,
        data: ContactUpdate,
    ) -> AuthorContact:
        """Update a contact log."""
        result = await self.db.execute(
            select(AuthorContact).where(
                AuthorContact.id == contact_id,
                AuthorContact.organization_id == organization_id,
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundError("AuthorContact", contact_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(
        self,
        contact_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a contact log."""
        result = await self.db.execute(
            select(AuthorContact).where(
                AuthorContact.id == contact_id,
                AuthorContact.organization_id == organization_id,
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundError("AuthorContact", contact_id)

        await self.db.delete(contact)
        await self.db.commit()

    async def get_contact_stats(
        self,
        author_id: UUID,
        organization_id: UUID,
    ) -> AuthorContactStats:
        """Get contact statistics for an author."""
        # Verify author exists
        author = await self.get_author(author_id)
        if not author:
            raise NotFoundError("Author", author_id)

        # Total contacts
        total_result = await self.db.execute(
            select(func.count()).where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
            )
        )
        total_contacts = total_result.scalar() or 0

        # Contacts by type
        type_result = await self.db.execute(
            select(AuthorContact.contact_type, func.count())
            .where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
            )
            .group_by(AuthorContact.contact_type)
        )
        contacts_by_type = {row[0].value: row[1] for row in type_result.all()}

        # Contacts by outcome
        outcome_result = await self.db.execute(
            select(AuthorContact.outcome, func.count())
            .where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
                AuthorContact.outcome.isnot(None),
            )
            .group_by(AuthorContact.outcome)
        )
        contacts_by_outcome = {
            row[0].value: row[1] for row in outcome_result.all() if row[0]
        }

        # Last contact date
        last_contact_result = await self.db.execute(
            select(func.max(AuthorContact.contact_date)).where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
            )
        )
        last_contact_date = last_contact_result.scalar()

        # Next follow-up
        follow_up_result = await self.db.execute(
            select(func.min(AuthorContact.follow_up_date)).where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
                AuthorContact.follow_up_date >= func.now(),
                AuthorContact.outcome != ContactOutcome.SUCCESSFUL,
                AuthorContact.outcome != ContactOutcome.DECLINED,
            )
        )
        next_follow_up = follow_up_result.scalar()

        return AuthorContactStats(
            author_id=author_id,
            total_contacts=total_contacts,
            contacts_by_type=contacts_by_type,
            contacts_by_outcome=contacts_by_outcome,
            last_contact_date=last_contact_date,
            next_follow_up=next_follow_up,
        )

    # =========================================================================
    # Author Enrichment
    # =========================================================================

    async def enrich_author(
        self,
        author_id: UUID,
        source: str = "openalex",
        force_update: bool = False,
    ) -> EnrichmentResult:
        """Enrich author data from external sources."""
        author = await self.get_author(author_id)
        if not author:
            raise NotFoundError("Author", author_id)

        updated_fields: list[str] = []

        if source == "openalex":
            updated_fields = await self._enrich_from_openalex(author, force_update)
        elif source == "orcid":
            updated_fields = await self._enrich_from_orcid(author, force_update)
        elif source == "semantic_scholar":
            updated_fields = await self._enrich_from_semantic_scholar(
                author, force_update
            )
        else:
            return EnrichmentResult(
                author_id=author_id,
                source=source,
                updated_fields=[],
                success=False,
                message=f"Unknown source: {source}",
            )

        if updated_fields:
            await self.db.commit()
            await self.db.refresh(author)

        return EnrichmentResult(
            author_id=author_id,
            source=source,
            updated_fields=updated_fields,
            success=True,
            message=f"Updated {len(updated_fields)} fields"
            if updated_fields
            else "No updates needed",
        )

    async def _enrich_from_openalex(
        self, author: Author, force_update: bool
    ) -> list[str]:
        """Enrich author from OpenAlex API."""
        import httpx

        updated_fields = []

        if not author.openalex_id:
            # Try to find by name/ORCID
            return updated_fields

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.OPENALEX_BASE_URL}/authors/{author.openalex_id}",
                    params={"mailto": settings.OPENALEX_EMAIL},
                    timeout=30.0,
                )
                if response.status_code != 200:
                    return updated_fields

                data = response.json()

                # Update metrics
                if force_update or author.h_index is None:
                    new_h_index = data.get("summary_stats", {}).get("h_index")
                    if new_h_index is not None and new_h_index != author.h_index:
                        author.h_index = new_h_index
                        updated_fields.append("h_index")

                if force_update or author.citation_count is None:
                    new_citations = data.get("cited_by_count")
                    if new_citations is not None and new_citations != author.citation_count:
                        author.citation_count = new_citations
                        updated_fields.append("citation_count")

                if force_update or author.works_count is None:
                    new_works = data.get("works_count")
                    if new_works is not None and new_works != author.works_count:
                        author.works_count = new_works
                        updated_fields.append("works_count")

                # Update ORCID if available
                if force_update or author.orcid is None:
                    orcid = data.get("orcid")
                    if orcid and orcid != author.orcid:
                        author.orcid = orcid
                        updated_fields.append("orcid")

                # Update affiliations
                if force_update or not author.affiliations:
                    affiliations = [
                        inst.get("display_name")
                        for inst in data.get("last_known_institutions", [])
                        if inst.get("display_name")
                    ]
                    if affiliations and affiliations != author.affiliations:
                        author.affiliations = affiliations
                        updated_fields.append("affiliations")

        except Exception:
            pass

        return updated_fields

    async def _enrich_from_orcid(
        self, author: Author, force_update: bool
    ) -> list[str]:
        """Enrich author from ORCID API."""
        # ORCID enrichment implementation
        # For now, return empty - can be implemented with ORCID API
        return []

    async def _enrich_from_semantic_scholar(
        self, author: Author, force_update: bool
    ) -> list[str]:
        """Enrich author from Semantic Scholar API."""
        # Semantic Scholar enrichment implementation
        # For now, return empty - can be implemented with Semantic Scholar API
        return []

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_contact_stats(
        self, author_id: UUID, organization_id: UUID
    ) -> dict:
        """Get basic contact stats for author profile."""
        # Recent contacts (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_result = await self.db.execute(
            select(func.count()).where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
                AuthorContact.contact_date >= thirty_days_ago,
            )
        )
        recent_count = recent_result.scalar() or 0

        # Last contact date
        last_contact_result = await self.db.execute(
            select(func.max(AuthorContact.contact_date)).where(
                AuthorContact.author_id == author_id,
                AuthorContact.organization_id == organization_id,
            )
        )
        last_contact_date = last_contact_result.scalar()

        return {
            "recent_count": recent_count,
            "last_contact_date": last_contact_date,
        }
