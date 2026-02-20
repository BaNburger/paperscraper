"""Service layer for the global paper catalog."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.sql_utils import escape_like
from paper_scraper.modules.catalog.schemas import (
    CatalogListResponse,
    CatalogPaperDetail,
    CatalogPaperSummary,
    CatalogStatsResponse,
)
from paper_scraper.modules.papers.models import OrganizationPaper, Paper

logger = logging.getLogger(__name__)


class CatalogService:
    """Service for browsing and claiming global catalog papers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_papers(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        source: str | None = None,
        has_embedding: bool | None = None,
    ) -> CatalogListResponse:
        """List global catalog papers with optional filters.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.
            search: Optional text search on title.
            source: Optional source filter (e.g., 'openalex', 'lens').
            has_embedding: Optional filter for papers with/without embeddings.

        Returns:
            Paginated catalog response.
        """
        query = select(Paper).where(Paper.is_global.is_(True))

        if search:
            search_filter = f"%{escape_like(search)}%"
            query = query.where(Paper.title.ilike(search_filter, escape="\\"))

        if source:
            query = query.where(Paper.source == source)

        if has_embedding is True:
            query = query.where(Paper.has_embedding.is_(True))
        elif has_embedding is False:
            query = query.where(Paper.has_embedding.is_(False))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Paper.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())

        return CatalogListResponse(
            items=[CatalogPaperSummary.model_validate(p) for p in papers],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def get_paper(self, paper_id: UUID) -> CatalogPaperDetail:
        """Get a global catalog paper by ID.

        Args:
            paper_id: Paper UUID.

        Returns:
            Paper detail.

        Raises:
            NotFoundError: If paper not found or not global.
        """
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.is_global.is_(True),
            )
        )
        paper = result.scalar_one_or_none()
        if not paper:
            raise NotFoundError("CatalogPaper", str(paper_id))

        return CatalogPaperDetail.model_validate(paper)

    async def claim_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> OrganizationPaper:
        """Claim a global paper into an organization's library.

        Creates an OrganizationPaper junction record linking the global
        paper to the organization. Does not duplicate the paper row.

        Args:
            paper_id: Global paper UUID.
            organization_id: Organization UUID.
            user_id: Optional user who claimed the paper.

        Returns:
            Created OrganizationPaper record.

        Raises:
            NotFoundError: If paper not found or not global.
            ValueError: If paper already claimed by this org.
        """
        # Verify paper exists and is global
        paper = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.is_global.is_(True),
            )
        )
        if not paper.scalar_one_or_none():
            raise NotFoundError("CatalogPaper", str(paper_id))

        # Check if already claimed
        existing = await self.db.execute(
            select(OrganizationPaper).where(
                OrganizationPaper.paper_id == paper_id,
                OrganizationPaper.organization_id == organization_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Paper already in your library")

        org_paper = OrganizationPaper(
            organization_id=organization_id,
            paper_id=paper_id,
            added_by_id=user_id,
            source="catalog",
        )
        self.db.add(org_paper)
        await self.db.flush()
        await self.db.refresh(org_paper)
        return org_paper

    async def get_stats(self) -> CatalogStatsResponse:
        """Get global catalog statistics.

        Returns:
            Stats including total papers, source breakdown, date range.
        """
        # Total papers
        total = (
            await self.db.execute(select(func.count()).where(Paper.is_global.is_(True)))
        ).scalar() or 0

        # Papers with embeddings
        total_embedded = (
            await self.db.execute(
                select(func.count()).where(
                    Paper.is_global.is_(True),
                    Paper.has_embedding.is_(True),
                )
            )
        ).scalar() or 0

        # Source breakdown
        source_result = await self.db.execute(
            select(Paper.source, func.count())
            .where(Paper.is_global.is_(True))
            .group_by(Paper.source)
        )
        sources = {str(row[0]): row[1] for row in source_result.all()}

        # Date range
        date_result = await self.db.execute(
            select(
                func.min(Paper.publication_date),
                func.max(Paper.publication_date),
            ).where(Paper.is_global.is_(True))
        )
        row = date_result.one_or_none()
        min_date = row[0].isoformat() if row and row[0] else None
        max_date = row[1].isoformat() if row and row[1] else None

        return CatalogStatsResponse(
            total_papers=total,
            total_with_embeddings=total_embedded,
            sources=sources,
            date_range={"min_date": min_date, "max_date": max_date},
        )
