"""API routes for model settings module."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import AdminUser, get_current_user, get_db
from paper_scraper.modules.auth.models import User
from paper_scraper.modules.model_settings.schemas import (
    HostingInfoResponse,
    ModelConfigurationCreate,
    ModelConfigurationListResponse,
    ModelConfigurationResponse,
    ModelConfigurationUpdate,
    UsageAggregation,
)
from paper_scraper.modules.model_settings.service import ModelSettingsService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> ModelSettingsService:
    return ModelSettingsService(db)


@router.get(
    "/models",
    response_model=ModelConfigurationListResponse,
    summary="List configured models",
)
async def list_models(
    current_user: User = Depends(get_current_user),
    service: ModelSettingsService = Depends(get_service),
):
    """List all AI model configurations for the organization."""
    return await service.list_configurations(current_user.organization_id)


@router.get(
    "/models/usage",
    response_model=UsageAggregation,
    summary="Get usage statistics",
)
async def get_usage(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to aggregate"),
    current_user: User = Depends(get_current_user),
    service: ModelSettingsService = Depends(get_service),
):
    """Get aggregated model usage statistics."""
    return await service.get_usage_stats(current_user.organization_id, days=days)


@router.post(
    "/models",
    response_model=ModelConfigurationResponse,
    status_code=201,
    summary="Add model configuration",
)
async def create_model(
    data: ModelConfigurationCreate,
    current_user: AdminUser,
    service: ModelSettingsService = Depends(get_service),
):
    """Create a new AI model configuration. Admin only."""
    return await service.create_configuration(current_user.organization_id, data)


@router.patch(
    "/models/{config_id}",
    response_model=ModelConfigurationResponse,
    summary="Update model configuration",
)
async def update_model(
    config_id: UUID,
    data: ModelConfigurationUpdate,
    current_user: AdminUser,
    service: ModelSettingsService = Depends(get_service),
):
    """Update a model configuration. Admin only."""
    return await service.update_configuration(config_id, current_user.organization_id, data)


@router.delete(
    "/models/{config_id}",
    status_code=204,
    summary="Remove model configuration",
)
async def delete_model(
    config_id: UUID,
    current_user: AdminUser,
    service: ModelSettingsService = Depends(get_service),
):
    """Delete a model configuration. Admin only."""
    await service.delete_configuration(config_id, current_user.organization_id)


@router.get(
    "/models/{config_id}/hosting",
    response_model=HostingInfoResponse,
    summary="Get hosting information",
)
async def get_hosting(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ModelSettingsService = Depends(get_service),
):
    """Get hosting and compliance information for a model configuration."""
    config = await service.get_hosting_info(config_id, current_user.organization_id)
    return HostingInfoResponse(
        model_configuration_id=config.id,
        provider=config.provider,
        model_name=config.model_name,
        hosting_info=config.hosting_info,
        data_processing_region=config.hosting_info.get("region"),
        compliance_certifications=config.hosting_info.get("certifications", []),
    )
