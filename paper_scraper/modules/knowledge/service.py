"""Service layer for knowledge sources."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import ForbiddenError, NotFoundError
from paper_scraper.modules.knowledge.models import (
    KnowledgeScope,
    KnowledgeSource,
)
from paper_scraper.modules.knowledge.schemas import (
    KnowledgeSourceCreate,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
    KnowledgeSourceUpdate,
)


class KnowledgeService:
    """Service for managing knowledge sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_personal(
        self, user_id: UUID, organization_id: UUID
    ) -> KnowledgeSourceListResponse:
        """List personal knowledge sources for a user."""
        query = select(KnowledgeSource).where(
            KnowledgeSource.organization_id == organization_id,
            KnowledgeSource.user_id == user_id,
            KnowledgeSource.scope == KnowledgeScope.PERSONAL,
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(query.order_by(KnowledgeSource.updated_at.desc()))
        sources = list(result.scalars().all())

        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.model_validate(s) for s in sources],
            total=total,
        )

    async def list_organization(
        self, organization_id: UUID
    ) -> KnowledgeSourceListResponse:
        """List organization-level knowledge sources."""
        query = select(KnowledgeSource).where(
            KnowledgeSource.organization_id == organization_id,
            KnowledgeSource.scope == KnowledgeScope.ORGANIZATION,
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(query.order_by(KnowledgeSource.updated_at.desc()))
        sources = list(result.scalars().all())

        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.model_validate(s) for s in sources],
            total=total,
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
