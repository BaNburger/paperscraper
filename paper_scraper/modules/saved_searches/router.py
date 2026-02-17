"""API router for saved searches module."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, OrganizationId, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.saved_searches.schemas import (
    SavedSearchCreate,
    SavedSearchListResponse,
    SavedSearchResponse,
    SavedSearchUpdate,
    ShareTokenResponse,
)
from paper_scraper.modules.saved_searches.service import SavedSearchService
from paper_scraper.modules.search.schemas import SearchRequest, SearchResponse
from paper_scraper.modules.search.service import SearchService

router = APIRouter()


def get_saved_search_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SavedSearchService:
    """Dependency to get SavedSearchService instance."""
    return SavedSearchService(db)


def get_search_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SearchService:
    """Dependency to get SearchService instance."""
    return SearchService(db)


@router.post(
    "",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create saved search",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def create_saved_search(
    data: SavedSearchCreate,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> SavedSearchResponse:
    """Create a new saved search."""
    saved_search = await service.create(
        data=data,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return service.to_response(saved_search)


@router.get(
    "",
    response_model=SavedSearchListResponse,
    summary="List saved searches",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_saved_searches(
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_public: bool = Query(default=True, description="Include public searches from org"),
) -> SavedSearchListResponse:
    """List saved searches for the current user."""
    saved_searches, total = await service.list_searches(
        organization_id=organization_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        include_public=include_public,
    )

    return SavedSearchListResponse(
        items=[service.to_response(s) for s in saved_searches],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get(
    "/shared/{share_token}",
    response_model=SavedSearchResponse,
    summary="Get saved search by share token",
)
async def get_shared_saved_search(
    share_token: str,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
) -> SavedSearchResponse:
    """Get a saved search using its share token (no auth required)."""
    saved_search = await service.get_by_share_token(share_token)
    return service.to_response(saved_search)


@router.get(
    "/{search_id}",
    response_model=SavedSearchResponse,
    summary="Get saved search",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_saved_search(
    search_id: UUID,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> SavedSearchResponse:
    """Get a saved search by ID."""
    saved_search = await service.get(
        search_id=search_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return service.to_response(saved_search)


@router.patch(
    "/{search_id}",
    response_model=SavedSearchResponse,
    summary="Update saved search",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_saved_search(
    search_id: UUID,
    data: SavedSearchUpdate,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> SavedSearchResponse:
    """Update a saved search."""
    saved_search = await service.update(
        search_id=search_id,
        data=data,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return service.to_response(saved_search)


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete saved search",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def delete_saved_search(
    search_id: UUID,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> None:
    """Delete a saved search."""
    await service.delete(
        search_id=search_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )


@router.post(
    "/{search_id}/share",
    response_model=ShareTokenResponse,
    summary="Generate share link",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def generate_share_link(
    search_id: UUID,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> ShareTokenResponse:
    """Generate a shareable link for a saved search."""
    share_token, share_url = await service.generate_share_token(
        search_id=search_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    return ShareTokenResponse(share_token=share_token, share_url=share_url)


@router.delete(
    "/{search_id}/share",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke share link",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def revoke_share_link(
    search_id: UUID,
    service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
) -> None:
    """Revoke the share link for a saved search."""
    await service.revoke_share_token(
        search_id=search_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )


@router.post(
    "/{search_id}/run",
    response_model=SearchResponse,
    summary="Execute saved search",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def run_saved_search(
    search_id: UUID,
    saved_search_service: Annotated[SavedSearchService, Depends(get_saved_search_service)],
    search_service: Annotated[SearchService, Depends(get_search_service)],
    current_user: CurrentUser,
    organization_id: OrganizationId,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SearchResponse:
    """Execute a saved search and return results."""
    from paper_scraper.modules.search.schemas import SearchFilters, SearchMode

    # Get the saved search
    saved_search = await saved_search_service.get(
        search_id=search_id,
        organization_id=organization_id,
        user_id=current_user.id,
    )

    # Record the run
    await saved_search_service.record_run(search_id, organization_id)

    # Build search request from saved search
    filters = None
    if saved_search.filters:
        filters = SearchFilters(**saved_search.filters)

    search_request = SearchRequest(
        query=saved_search.query,
        mode=SearchMode(saved_search.mode),
        filters=filters,
        page=page,
        page_size=page_size,
    )

    # Execute search
    return await search_service.search(search_request, organization_id)
