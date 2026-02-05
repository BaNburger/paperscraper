"""FastAPI router for knowledge sources."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import AdminUser, CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.knowledge.schemas import (
    KnowledgeSourceCreate,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
    KnowledgeSourceUpdate,
)
from paper_scraper.modules.knowledge.service import KnowledgeService

router = APIRouter()


def get_knowledge_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeService:
    return KnowledgeService(db)


# --- Personal knowledge sources ---


@router.get("/personal", response_model=KnowledgeSourceListResponse)
async def list_personal_sources(
    current_user: CurrentUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """List current user's personal knowledge sources."""
    return await service.list_personal(
        current_user.id, current_user.organization_id
    )


@router.post(
    "/personal",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_personal_source(
    data: KnowledgeSourceCreate,
    current_user: CurrentUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """Create a personal knowledge source."""
    source = await service.create_personal(
        current_user.id, current_user.organization_id, data
    )
    return KnowledgeSourceResponse.model_validate(source)


@router.patch("/personal/{source_id}", response_model=KnowledgeSourceResponse)
async def update_personal_source(
    source_id: UUID,
    data: KnowledgeSourceUpdate,
    current_user: CurrentUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """Update a personal knowledge source."""
    source = await service.update_personal(
        source_id, current_user.id, current_user.organization_id, data
    )
    return KnowledgeSourceResponse.model_validate(source)


@router.delete(
    "/personal/{source_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_personal_source(
    source_id: UUID,
    current_user: CurrentUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """Delete a personal knowledge source."""
    await service.delete_personal(
        source_id, current_user.id, current_user.organization_id
    )


# --- Organization knowledge sources (admin only) ---


@router.get("/organization", response_model=KnowledgeSourceListResponse)
async def list_organization_sources(
    current_user: AdminUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """List organization-level knowledge sources (admin only)."""
    return await service.list_organization(current_user.organization_id)


@router.post(
    "/organization",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization_source(
    data: KnowledgeSourceCreate,
    current_user: AdminUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """Create an organization-level knowledge source (admin only)."""
    source = await service.create_organization(
        current_user.organization_id, data
    )
    return KnowledgeSourceResponse.model_validate(source)


@router.patch(
    "/organization/{source_id}", response_model=KnowledgeSourceResponse
)
async def update_organization_source(
    source_id: UUID,
    data: KnowledgeSourceUpdate,
    current_user: AdminUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """Update an organization-level knowledge source (admin only)."""
    source = await service.update_organization(
        source_id, current_user.organization_id, data
    )
    return KnowledgeSourceResponse.model_validate(source)


@router.delete(
    "/organization/{source_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_organization_source(
    source_id: UUID,
    current_user: AdminUser,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    """Delete an organization-level knowledge source (admin only)."""
    await service.delete_organization(
        source_id, current_user.organization_id
    )
