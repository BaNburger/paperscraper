"""Service layer for saved searches module."""

import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import DuplicateError, ForbiddenError, NotFoundError, ValidationError
from paper_scraper.modules.projects.models import Project
from paper_scraper.modules.saved_searches.models import SavedSearch
from paper_scraper.modules.saved_searches.schemas import (
    SavedSearchCreate,
    SavedSearchResponse,
    SavedSearchUpdate,
)
from paper_scraper.modules.search.schemas import SearchFilters, SearchMode


class SavedSearchService:
    """Service for saved search operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: SavedSearchCreate,
        organization_id: UUID,
        user_id: UUID,
    ) -> SavedSearch:
        """
        Create a new saved search.

        Args:
            data: Saved search creation data.
            organization_id: Organization ID for tenant isolation.
            user_id: ID of the user creating the search.

        Returns:
            Created SavedSearch instance.

        Raises:
            DuplicateError: If a saved search with same name exists for user.
        """
        # Validate target project belongs to same org
        if data.target_project_id:
            await self._validate_target_project(data.target_project_id, organization_id)

        # Check for duplicate name
        existing = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.organization_id == organization_id,
                SavedSearch.created_by_id == user_id,
                SavedSearch.name == data.name,
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("SavedSearch", "name", data.name)

        saved_search = SavedSearch(
            organization_id=organization_id,
            created_by_id=user_id,
            name=data.name,
            description=data.description,
            query=data.query,
            mode=data.mode.value if isinstance(data.mode, SearchMode) else data.mode,
            filters=data.filters.model_dump() if data.filters else {},
            is_public=data.is_public,
            alert_enabled=data.alert_enabled,
            alert_frequency=data.alert_frequency.value if data.alert_frequency else None,
            # Discovery fields
            semantic_description=data.semantic_description,
            target_project_id=data.target_project_id,
            auto_import_enabled=data.auto_import_enabled,
            import_sources=data.import_sources,
            max_import_per_run=data.max_import_per_run,
            discovery_frequency=data.discovery_frequency.value if data.discovery_frequency else None,
        )

        self.db.add(saved_search)
        await self.db.flush()
        await self.db.refresh(saved_search, ["created_by"])

        return saved_search

    async def get(
        self,
        search_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> SavedSearch:
        """
        Get a saved search by ID.

        Args:
            search_id: Saved search ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID for ownership check.

        Returns:
            SavedSearch instance.

        Raises:
            NotFoundError: If saved search not found.
            ForbiddenError: If user doesn't have access.
        """
        result = await self.db.execute(
            select(SavedSearch)
            .options(selectinload(SavedSearch.created_by))
            .where(
                SavedSearch.id == search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", search_id)

        # Check access: owner or public within org
        if saved_search.created_by_id != user_id and not saved_search.is_public:
            raise ForbiddenError("You don't have access to this saved search")

        return saved_search

    async def get_by_share_token(
        self,
        share_token: str,
    ) -> SavedSearch:
        """
        Get a saved search by share token.

        Args:
            share_token: Unique share token.

        Returns:
            SavedSearch instance.

        Raises:
            NotFoundError: If saved search not found.
        """
        result = await self.db.execute(
            select(SavedSearch)
            .options(selectinload(SavedSearch.created_by))
            .where(SavedSearch.share_token == share_token)
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", share_token)

        return saved_search

    async def list_searches(
        self,
        organization_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_public: bool = True,
    ) -> tuple[list[SavedSearch], int]:
        """
        List saved searches for a user.

        Args:
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.
            page: Page number.
            page_size: Results per page.
            include_public: Whether to include public searches from org.

        Returns:
            Tuple of (saved searches list, total count).
        """
        # Base query: user's own searches
        conditions = [
            SavedSearch.organization_id == organization_id,
        ]

        if include_public:
            # Include user's own + public from org
            conditions.append(
                or_(
                    SavedSearch.created_by_id == user_id,
                    SavedSearch.is_public == True,  # noqa: E712
                )
            )
        else:
            # Only user's own
            conditions.append(SavedSearch.created_by_id == user_id)

        # Count query
        count_query = select(func.count()).select_from(SavedSearch).where(*conditions)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Data query
        query = (
            select(SavedSearch)
            .options(selectinload(SavedSearch.created_by))
            .where(*conditions)
            .order_by(SavedSearch.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        saved_searches = list(result.scalars().all())

        return saved_searches, total

    async def update(
        self,
        search_id: UUID,
        data: SavedSearchUpdate,
        organization_id: UUID,
        user_id: UUID,
    ) -> SavedSearch:
        """
        Update a saved search.

        Args:
            search_id: Saved search ID.
            data: Update data.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Returns:
            Updated SavedSearch instance.

        Raises:
            NotFoundError: If saved search not found.
            ForbiddenError: If user is not the owner.
            DuplicateError: If new name conflicts.
        """
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", search_id)

        if saved_search.created_by_id != user_id:
            raise ForbiddenError("Only the owner can update this saved search")

        # Validate target project belongs to same org
        if data.target_project_id is not None:
            await self._validate_target_project(data.target_project_id, organization_id)

        # Check for name conflict if updating name
        if data.name and data.name != saved_search.name:
            existing = await self.db.execute(
                select(SavedSearch).where(
                    SavedSearch.organization_id == organization_id,
                    SavedSearch.created_by_id == user_id,
                    SavedSearch.name == data.name,
                    SavedSearch.id != search_id,
                )
            )
            if existing.scalar_one_or_none():
                raise DuplicateError("SavedSearch", "name", data.name)

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "mode" and value:
                value = value.value if hasattr(value, "value") else value
            if field == "filters" and value:
                value = value.model_dump() if hasattr(value, "model_dump") else value
            if field == "alert_frequency" and value:
                value = value.value if hasattr(value, "value") else value
            if field == "discovery_frequency" and value:
                value = value.value if hasattr(value, "value") else value
            setattr(saved_search, field, value)

        await self.db.flush()
        # Re-query to get fresh column values (updated_at from onupdate) + relationship
        result = await self.db.execute(
            select(SavedSearch)
            .options(selectinload(SavedSearch.created_by))
            .where(SavedSearch.id == search_id)
        )
        saved_search = result.scalar_one()

        return saved_search

    async def delete(
        self,
        search_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete a saved search.

        Args:
            search_id: Saved search ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Raises:
            NotFoundError: If saved search not found.
            ForbiddenError: If user is not the owner.
        """
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", search_id)

        if saved_search.created_by_id != user_id:
            raise ForbiddenError("Only the owner can delete this saved search")

        await self.db.delete(saved_search)
        await self.db.flush()

    async def generate_share_token(
        self,
        search_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> tuple[str, str]:
        """
        Generate a share token for a saved search.

        Args:
            search_id: Saved search ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Returns:
            Tuple of (share_token, share_url).

        Raises:
            NotFoundError: If saved search not found.
            ForbiddenError: If user is not the owner.
        """
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", search_id)

        if saved_search.created_by_id != user_id:
            raise ForbiddenError("Only the owner can generate a share link")

        # Generate unique token
        share_token = secrets.token_urlsafe(32)
        saved_search.share_token = share_token

        await self.db.flush()

        share_url = f"{settings.FRONTEND_URL}/search/shared/{share_token}"
        return share_token, share_url

    async def revoke_share_token(
        self,
        search_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Revoke the share token for a saved search.

        Args:
            search_id: Saved search ID.
            organization_id: Organization ID for tenant isolation.
            user_id: Current user ID.

        Raises:
            NotFoundError: If saved search not found.
            ForbiddenError: If user is not the owner.
        """
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            raise NotFoundError("SavedSearch", search_id)

        if saved_search.created_by_id != user_id:
            raise ForbiddenError("Only the owner can revoke the share link")

        saved_search.share_token = None
        await self.db.flush()

    async def record_run(
        self,
        search_id: UUID,
        organization_id: UUID,
    ) -> SavedSearch:
        """
        Record that a saved search was executed.

        Args:
            search_id: Saved search ID.
            organization_id: Organization ID for tenant isolation.

        Returns:
            Updated SavedSearch instance.
        """
        result = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.organization_id == organization_id,
            )
        )
        saved_search = result.scalar_one_or_none()

        if saved_search:
            saved_search.run_count += 1
            saved_search.last_run_at = datetime.now(timezone.utc)
            await self.db.flush()

        return saved_search

    async def get_searches_needing_alerts(
        self,
        frequency: str,
    ) -> list[SavedSearch]:
        """
        Get saved searches that need alerts processed.

        Args:
            frequency: Alert frequency to filter by (daily, weekly).

        Returns:
            List of saved searches needing alerts.
        """
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(SavedSearch)
            .options(selectinload(SavedSearch.created_by))
            .where(
                SavedSearch.alert_enabled == True,  # noqa: E712
                SavedSearch.alert_frequency == frequency,
            )
        )

        return list(result.scalars().all())

    async def _validate_target_project(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Validate that the target project belongs to the same organization."""
        result = await self.db.execute(
            select(Project.id).where(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValidationError(
                "Target project not found or belongs to a different organization"
            )

    def to_response(
        self,
        saved_search: SavedSearch,
    ) -> SavedSearchResponse:
        """
        Convert a SavedSearch model to response schema.

        Args:
            saved_search: SavedSearch model instance.

        Returns:
            SavedSearchResponse schema.
        """
        share_url = None
        if saved_search.share_token:
            share_url = f"{settings.FRONTEND_URL}/search/shared/{saved_search.share_token}"

        creator = None
        if saved_search.created_by:
            from paper_scraper.modules.saved_searches.schemas import SavedSearchCreator
            creator = SavedSearchCreator(
                id=saved_search.created_by.id,
                email=saved_search.created_by.email,
                full_name=saved_search.created_by.full_name,
            )

        # Get target project name if available
        target_project_name = None
        if saved_search.target_project and hasattr(saved_search.target_project, "name"):
            target_project_name = saved_search.target_project.name

        return SavedSearchResponse(
            id=saved_search.id,
            name=saved_search.name,
            description=saved_search.description,
            query=saved_search.query,
            mode=saved_search.mode,
            filters=saved_search.filters,
            is_public=saved_search.is_public,
            share_token=saved_search.share_token,
            share_url=share_url,
            alert_enabled=saved_search.alert_enabled,
            alert_frequency=saved_search.alert_frequency,
            last_alert_at=saved_search.last_alert_at,
            # Discovery fields
            semantic_description=saved_search.semantic_description,
            target_project_id=saved_search.target_project_id,
            target_project_name=target_project_name,
            auto_import_enabled=saved_search.auto_import_enabled,
            import_sources=saved_search.import_sources,
            max_import_per_run=saved_search.max_import_per_run,
            discovery_frequency=saved_search.discovery_frequency,
            last_discovery_at=saved_search.last_discovery_at,
            # Usage
            run_count=saved_search.run_count,
            last_run_at=saved_search.last_run_at,
            created_at=saved_search.created_at,
            updated_at=saved_search.updated_at,
            created_by=creator,
        )
