"""API routes for discovery module."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, get_db, require_permission
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.discovery.schemas import (
    DiscoveryProfileListResponse,
    DiscoveryRunListResponse,
    DiscoveryRunResponse,
    DiscoveryTriggerResponse,
)
from paper_scraper.modules.discovery.service import DiscoveryService

router = APIRouter()


@router.get(
    "/profiles/",
    response_model=DiscoveryProfileListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_profiles(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryProfileListResponse:
    """List all active discovery profiles for the organization."""
    service = DiscoveryService(db)
    return await service.list_active_profiles(current_user.organization_id)


@router.post(
    "/{saved_search_id}/run/",
    response_model=DiscoveryTriggerResponse,
    status_code=200,
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def trigger_discovery(
    saved_search_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryTriggerResponse:
    """Manually trigger discovery for a saved search profile."""
    service = DiscoveryService(db)
    return await service.run_discovery(
        saved_search_id=saved_search_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.get(
    "/{saved_search_id}/runs/",
    response_model=DiscoveryRunListResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_runs(
    saved_search_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DiscoveryRunListResponse:
    """List discovery run history for a saved search."""
    service = DiscoveryService(db)
    return await service.list_runs(
        saved_search_id=saved_search_id,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/runs/{run_id}",
    response_model=DiscoveryRunResponse,
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_run(
    run_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryRunResponse:
    """Get a single discovery run by ID."""
    service = DiscoveryService(db)
    return await service.get_run(
        run_id=run_id,
        organization_id=current_user.organization_id,
    )
