"""Service layer for knowledge sources."""

import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import ForbiddenError, NotFoundError
from paper_scraper.modules.knowledge.models import (
    KnowledgeScope,
    KnowledgeSource,
    KnowledgeType,
)
from paper_scraper.modules.knowledge.schemas import (
    KnowledgeSourceCreate,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
    KnowledgeSourceUpdate,
)
from paper_scraper.modules.scoring.llm_client import sanitize_text_for_prompt

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing knowledge sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_personal(
        self,
        user_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> KnowledgeSourceListResponse:
        """List personal knowledge sources for a user."""
        query = select(KnowledgeSource).where(
            KnowledgeSource.organization_id == organization_id,
            KnowledgeSource.user_id == user_id,
            KnowledgeSource.scope == KnowledgeScope.PERSONAL,
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(
            query.order_by(KnowledgeSource.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        sources = list(result.scalars().all())

        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.model_validate(s) for s in sources],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def list_organization(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> KnowledgeSourceListResponse:
        """List organization-level knowledge sources."""
        query = select(KnowledgeSource).where(
            KnowledgeSource.organization_id == organization_id,
            KnowledgeSource.scope == KnowledgeScope.ORGANIZATION,
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(
            query.order_by(KnowledgeSource.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        sources = list(result.scalars().all())

        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.model_validate(s) for s in sources],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def create_personal(
        self,
        user_id: UUID,
        organization_id: UUID,
        data: KnowledgeSourceCreate,
    ) -> KnowledgeSource:
        """Create a personal knowledge source."""
        source = KnowledgeSource(
            organization_id=organization_id,
            user_id=user_id,
            scope=KnowledgeScope.PERSONAL,
            **data.model_dump(),
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def create_organization(
        self,
        organization_id: UUID,
        data: KnowledgeSourceCreate,
    ) -> KnowledgeSource:
        """Create an organization-level knowledge source (admin only)."""
        source = KnowledgeSource(
            organization_id=organization_id,
            user_id=None,
            scope=KnowledgeScope.ORGANIZATION,
            **data.model_dump(),
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def _get_source(
        self, source_id: UUID, organization_id: UUID
    ) -> KnowledgeSource:
        """Get a knowledge source by ID with tenant isolation."""
        result = await self.db.execute(
            select(KnowledgeSource).where(
                KnowledgeSource.id == source_id,
                KnowledgeSource.organization_id == organization_id,
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundError("KnowledgeSource", str(source_id))
        return source

    async def update_personal(
        self,
        source_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        data: KnowledgeSourceUpdate,
    ) -> KnowledgeSource:
        """Update a personal knowledge source."""
        source = await self._get_source(source_id, organization_id)
        if source.scope != KnowledgeScope.PERSONAL or source.user_id != user_id:
            raise ForbiddenError("You can only update your own personal knowledge sources")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)

        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def update_organization(
        self,
        source_id: UUID,
        organization_id: UUID,
        data: KnowledgeSourceUpdate,
    ) -> KnowledgeSource:
        """Update an organization-level knowledge source (admin only)."""
        source = await self._get_source(source_id, organization_id)
        if source.scope != KnowledgeScope.ORGANIZATION:
            raise ForbiddenError("This is not an organization knowledge source")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)

        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def delete_personal(
        self,
        source_id: UUID,
        user_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a personal knowledge source."""
        source = await self._get_source(source_id, organization_id)
        if source.scope != KnowledgeScope.PERSONAL or source.user_id != user_id:
            raise ForbiddenError("You can only delete your own personal knowledge sources")

        await self.db.delete(source)
        await self.db.flush()

    async def delete_organization(
        self,
        source_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete an organization-level knowledge source (admin only)."""
        source = await self._get_source(source_id, organization_id)
        if source.scope != KnowledgeScope.ORGANIZATION:
            raise ForbiddenError("This is not an organization knowledge source")

        await self.db.delete(source)
        await self.db.flush()

    # =========================================================================
    # Knowledge-Enhanced Scoring Support
    # =========================================================================

    async def get_relevant_sources_for_scoring(
        self,
        organization_id: UUID,
        user_id: UUID | None = None,
        keywords: list[str] | None = None,
        knowledge_types: list[KnowledgeType] | None = None,
        limit: int = 10,
    ) -> list[KnowledgeSource]:
        """Get knowledge sources relevant for AI scoring context.

        Retrieves organization-level and optionally personal knowledge sources
        that can be injected into scoring prompts to personalize analysis.

        Args:
            organization_id: Organization UUID for tenant isolation.
            user_id: Optional user ID to include personal sources.
            keywords: Optional keywords to filter by tags.
            knowledge_types: Optional list of types to filter by.
            limit: Maximum sources to return.

        Returns:
            List of KnowledgeSource objects relevant for scoring.
        """
        # Build query for organization-level sources
        query = select(KnowledgeSource).where(
            KnowledgeSource.organization_id == organization_id,
        )

        # Include both organization and personal sources if user_id provided
        if user_id:
            query = query.where(
                or_(
                    KnowledgeSource.scope == KnowledgeScope.ORGANIZATION,
                    (KnowledgeSource.scope == KnowledgeScope.PERSONAL)
                    & (KnowledgeSource.user_id == user_id),
                )
            )
        else:
            query = query.where(KnowledgeSource.scope == KnowledgeScope.ORGANIZATION)

        # Filter by knowledge types if specified
        if knowledge_types:
            query = query.where(KnowledgeSource.type.in_(knowledge_types))

        # Order by relevance to scoring
        # Prioritize types that are most useful for scoring
        query = query.order_by(
            # Put evaluation_criteria first, then industry_context
            KnowledgeSource.type.desc(),
            KnowledgeSource.updated_at.desc(),
        )

        query = query.limit(limit)

        result = await self.db.execute(query)
        sources = list(result.scalars().all())

        # If keywords provided, try to filter by relevance
        if keywords and sources:
            # Simple keyword matching against tags
            keywords_lower = {k.lower() for k in keywords}
            scored_sources = []
            for source in sources:
                source_tags = {t.lower() for t in source.tags} if source.tags else set()
                match_count = len(keywords_lower & source_tags)
                scored_sources.append((source, match_count))

            # Sort by match count (descending) while preserving type ordering
            scored_sources.sort(key=lambda x: x[1], reverse=True)
            sources = [s for s, _ in scored_sources]

        return sources

    def format_knowledge_for_prompt(
        self,
        sources: list[KnowledgeSource],
        dimension: str | None = None,
    ) -> str:
        """Format knowledge sources for injection into scoring prompts.

        Args:
            sources: List of knowledge sources to format.
            dimension: Optional dimension name to filter relevant sources.

        Returns:
            Formatted string for prompt injection.
        """
        if not sources:
            return ""

        # Map dimensions to relevant knowledge types
        dimension_type_map = {
            "novelty": [KnowledgeType.RESEARCH_FOCUS, KnowledgeType.DOMAIN_EXPERTISE],
            "ip_potential": [KnowledgeType.EVALUATION_CRITERIA, KnowledgeType.INDUSTRY_CONTEXT],
            "marketability": [KnowledgeType.INDUSTRY_CONTEXT, KnowledgeType.EVALUATION_CRITERIA],
            "feasibility": [KnowledgeType.DOMAIN_EXPERTISE, KnowledgeType.RESEARCH_FOCUS],
            "commercialization": [KnowledgeType.INDUSTRY_CONTEXT, KnowledgeType.EVALUATION_CRITERIA],
            "team_readiness": [KnowledgeType.EVALUATION_CRITERIA, KnowledgeType.DOMAIN_EXPERTISE],
        }

        # Filter sources by dimension if specified
        if dimension and dimension in dimension_type_map:
            relevant_types = dimension_type_map[dimension]
            filtered_sources = [s for s in sources if s.type in relevant_types]
            # Fall back to all sources if no matches
            sources = filtered_sources if filtered_sources else sources

        # Format for prompt with sanitization to prevent prompt injection
        parts = ["## Organization Knowledge Context\n"]
        for source in sources[:5]:  # Limit to 5 sources per prompt
            type_label = source.type.value.replace("_", " ").title()
            # Sanitize title and content to prevent prompt injection
            safe_title = sanitize_text_for_prompt(source.title, max_length=200)
            safe_content = sanitize_text_for_prompt(source.content, max_length=1000)
            parts.append(f"### {safe_title} ({type_label})")
            parts.append(safe_content)
            parts.append("")

        return "\n".join(parts)
