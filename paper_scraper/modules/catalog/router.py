"""FastAPI router for global paper catalog endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.catalog.schemas import (
    CatalogListResponse,
    CatalogPaperDetail,
    CatalogStatsResponse,
    ClaimPaperResponse,
)
from paper_scraper.modules.catalog.service import CatalogService

router = APIRouter()


def get_catalog_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CatalogService:
    """Dependency to get catalog service instance."""
    return CatalogService(db)


@router.get(
    "/papers",
    response_model=CatalogListResponse,
    summary="Browse global paper catalog",
)
async def list_catalog_papers(
    current_user: CurrentUser,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    source: str | None = Query(default=None),
    has_embedding: bool | None = Query(default=None),
) -> CatalogListResponse:
    """Browse the global paper catalog with optional filters.

    Returns paginated results from the shared paper catalog.
    Papers are globally deduplicated across all sources.
    """
    return await catalog_service.list_papers(
        page=page,
        page_size=page_size,
        search=search,
        source=source,
        has_embedding=has_embedding,
    )


@router.get(
    "/papers/{paper_id}",
    response_model=CatalogPaperDetail,
    summary="Get catalog paper details",
)
async def get_catalog_paper(
    paper_id: UUID,
    current_user: CurrentUser,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> CatalogPaperDetail:
    """Get full details of a global catalog paper."""
    return await catalog_service.get_paper(paper_id)


@router.post(
    "/papers/{paper_id}/claim",
    response_model=ClaimPaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Claim paper to library",
)
async def claim_paper(
    paper_id: UUID,
    current_user: CurrentUser,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ClaimPaperResponse:
    """Add a global catalog paper to your organization's library.

    Creates a link between the global paper and your organization
    without duplicating the paper data.
    """
    await catalog_service.claim_paper(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ClaimPaperResponse(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        message="Paper added to your library.",
    )


@router.get(
    "/stats",
    response_model=CatalogStatsResponse,
    summary="Get catalog statistics",
)
async def get_catalog_stats(
    current_user: CurrentUser,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> CatalogStatsResponse:
    """Get statistics about the global paper catalog.

    Returns total papers, source breakdown, and date range.
    """
    return await catalog_service.get_stats()
