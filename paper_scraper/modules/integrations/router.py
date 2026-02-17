"""FastAPI router for integration connector APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.integrations.schemas import (
    IntegrationConnectorCreate,
    IntegrationConnectorListResponse,
    IntegrationConnectorResponse,
    IntegrationConnectorUpdate,
    ZoteroConnectionStatusResponse,
    ZoteroConnectRequest,
    ZoteroSyncRequest,
    ZoteroSyncRunResponse,
)
from paper_scraper.modules.integrations.service import IntegrationService

router = APIRouter()


def get_integration_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IntegrationService:
    """Dependency provider for IntegrationService."""
    return IntegrationService(db)


def require_zotero_sync_enabled() -> None:
    """Gate Zotero sync endpoints behind feature flag."""
    if not settings.ZOTERO_SYNC_ENABLED:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zotero sync feature is disabled",
        )


def require_zotero_inbound_enabled() -> None:
    """Gate inbound sync separately."""
    if not settings.LIBRARY_INBOUND_SYNC_ENABLED:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zotero inbound sync feature is disabled",
        )


@router.post(
    "/connectors",
    response_model=IntegrationConnectorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create integration connector",
    dependencies=[Depends(require_permission(Permission.DEVELOPER_MANAGE))],
)
async def create_connector(
    data: IntegrationConnectorCreate,
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> IntegrationConnectorResponse:
    """Create a new integration connector for the current organization."""
    connector = await service.create_connector(
        organization_id=current_user.organization_id,
        data=data,
    )
    return IntegrationConnectorResponse.model_validate(connector)


@router.patch(
    "/connectors/{connector_id}",
    response_model=IntegrationConnectorResponse,
    summary="Update integration connector",
    dependencies=[Depends(require_permission(Permission.DEVELOPER_MANAGE))],
)
async def update_connector(
    connector_id: UUID,
    data: IntegrationConnectorUpdate,
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> IntegrationConnectorResponse:
    """Update an existing integration connector."""
    connector = await service.update_connector(
        connector_id=connector_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return IntegrationConnectorResponse.model_validate(connector)


@router.get(
    "/connectors",
    response_model=IntegrationConnectorListResponse,
    summary="List integration connectors",
    dependencies=[Depends(require_permission(Permission.DEVELOPER_MANAGE))],
)
async def list_connectors(
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> IntegrationConnectorListResponse:
    """List all configured integration connectors."""
    return await service.list_connectors(current_user.organization_id)


@router.post(
    "/zotero/connect",
    response_model=ZoteroConnectionStatusResponse,
    summary="Connect Zotero integration",
    dependencies=[
        Depends(require_zotero_sync_enabled),
        Depends(require_permission(Permission.TRANSFER_MANAGE)),
    ],
)
async def connect_zotero(
    data: ZoteroConnectRequest,
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ZoteroConnectionStatusResponse:
    """Connect or update Zotero credentials for the organization."""
    await service.connect_zotero(
        organization_id=current_user.organization_id,
        data=data,
    )
    return await service.get_zotero_status(current_user.organization_id)


@router.get(
    "/zotero/status",
    response_model=ZoteroConnectionStatusResponse,
    summary="Get Zotero connection status",
    dependencies=[
        Depends(require_zotero_sync_enabled),
        Depends(require_permission(Permission.TRANSFER_READ)),
    ],
)
async def get_zotero_status(
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ZoteroConnectionStatusResponse:
    """Get current Zotero connection status."""
    return await service.get_zotero_status(current_user.organization_id)


@router.post(
    "/zotero/sync/outbound",
    response_model=ZoteroSyncRunResponse,
    summary="Run outbound Zotero sync",
    dependencies=[
        Depends(require_zotero_sync_enabled),
        Depends(require_permission(Permission.TRANSFER_MANAGE)),
    ],
)
async def sync_zotero_outbound(
    data: ZoteroSyncRequest,
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ZoteroSyncRunResponse:
    """Push local papers to Zotero."""
    run = await service.sync_zotero_outbound(
        organization_id=current_user.organization_id,
        triggered_by=current_user.id,
        paper_ids=data.paper_ids,
    )
    return ZoteroSyncRunResponse.model_validate(run)


@router.post(
    "/zotero/sync/inbound",
    response_model=ZoteroSyncRunResponse,
    summary="Run inbound Zotero sync",
    dependencies=[
        Depends(require_zotero_sync_enabled),
        Depends(require_zotero_inbound_enabled),
        Depends(require_permission(Permission.TRANSFER_MANAGE)),
    ],
)
async def sync_zotero_inbound(
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ZoteroSyncRunResponse:
    """Pull Zotero updates and merge non-destructively."""
    run = await service.sync_zotero_inbound(
        organization_id=current_user.organization_id,
        triggered_by=current_user.id,
    )
    return ZoteroSyncRunResponse.model_validate(run)


@router.get(
    "/zotero/sync-runs/{run_id}",
    response_model=ZoteroSyncRunResponse,
    summary="Get Zotero sync run",
    dependencies=[
        Depends(require_zotero_sync_enabled),
        Depends(require_permission(Permission.TRANSFER_READ)),
    ],
)
async def get_zotero_sync_run(
    run_id: UUID,
    current_user: CurrentUser,
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ZoteroSyncRunResponse:
    """Get details for a specific Zotero sync run."""
    run = await service.get_sync_run(
        run_id=run_id,
        organization_id=current_user.organization_id,
    )
    return ZoteroSyncRunResponse.model_validate(run)
