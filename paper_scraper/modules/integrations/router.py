"""FastAPI router for integration connector APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.integrations.schemas import (
    IntegrationConnectorCreate,
    IntegrationConnectorListResponse,
    IntegrationConnectorResponse,
    IntegrationConnectorUpdate,
)
from paper_scraper.modules.integrations.service import IntegrationService

router = APIRouter()


def get_integration_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IntegrationService:
    """Dependency provider for IntegrationService."""
    return IntegrationService(db)


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
