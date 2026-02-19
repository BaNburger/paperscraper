"""FastAPI router for authors endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.authors.schemas import (
    AuthorContactStats,
    AuthorDetailResponse,
    AuthorListResponse,
    AuthorProfileResponse,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    EnrichmentRequest,
    EnrichmentResult,
)
from paper_scraper.modules.authors.service import AuthorService

router = APIRouter()


def get_author_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthorService:
    """Dependency to get author service instance."""
    return AuthorService(db)


# =============================================================================
# Author Profile Endpoints
# =============================================================================


@router.get(
    "/",
    response_model=AuthorListResponse,
    summary="List authors",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_authors(
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> AuthorListResponse:
    """List all authors with papers in the organization."""
    return await author_service.list_authors(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{author_id}",
    response_model=AuthorProfileResponse,
    summary="Get author profile",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_author_profile(
    author_id: UUID,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> AuthorProfileResponse:
    """Get an author's profile with basic stats."""
    profile = await author_service.get_author_profile(
        author_id=author_id,
        organization_id=current_user.organization_id,
    )
    if not profile:
        raise NotFoundError("Author", author_id)
    return profile


@router.get(
    "/{author_id}/detail",
    response_model=AuthorDetailResponse,
    summary="Get author detail",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_author_detail(
    author_id: UUID,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> AuthorDetailResponse:
    """Get full author detail with papers and contact history."""
    detail = await author_service.get_author_detail(
        author_id=author_id,
        organization_id=current_user.organization_id,
    )
    if not detail:
        raise NotFoundError("Author", author_id)
    return detail


# =============================================================================
# Contact Tracking Endpoints
# =============================================================================


@router.post(
    "/{author_id}/contacts",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log contact",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def create_contact(
    author_id: UUID,
    data: ContactCreate,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> ContactResponse:
    """Log a contact/outreach attempt with an author."""
    contact = await author_service.create_contact(
        author_id=author_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
    )
    return ContactResponse.model_validate(contact)


@router.patch(
    "/{author_id}/contacts/{contact_id}",
    response_model=ContactResponse,
    summary="Update contact",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_contact(
    author_id: UUID,
    contact_id: UUID,
    data: ContactUpdate,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> ContactResponse:
    """Update an existing contact log."""
    contact = await author_service.update_contact(
        contact_id=contact_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return ContactResponse.model_validate(contact)


@router.delete(
    "/{author_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete contact",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def delete_contact(
    author_id: UUID,
    contact_id: UUID,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> None:
    """Delete a contact log."""
    await author_service.delete_contact(
        contact_id=contact_id,
        organization_id=current_user.organization_id,
    )


@router.get(
    "/{author_id}/contacts/stats",
    response_model=AuthorContactStats,
    summary="Get contact stats",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_contact_stats(
    author_id: UUID,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> AuthorContactStats:
    """Get contact statistics for an author."""
    return await author_service.get_contact_stats(
        author_id=author_id,
        organization_id=current_user.organization_id,
    )


# =============================================================================
# Enrichment Endpoints
# =============================================================================


@router.post(
    "/{author_id}/enrich",
    response_model=EnrichmentResult,
    summary="Enrich author data",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def enrich_author(
    author_id: UUID,
    current_user: CurrentUser,
    author_service: Annotated[AuthorService, Depends(get_author_service)],
    request: EnrichmentRequest = EnrichmentRequest(),
) -> EnrichmentResult:
    """Enrich author data from external sources (OpenAlex, ORCID, etc.)."""
    return await author_service.enrich_author(
        author_id=author_id,
        organization_id=current_user.organization_id,
        source=request.source,
        force_update=request.force_update,
    )
