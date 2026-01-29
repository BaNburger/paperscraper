"""FastAPI router for papers endpoints."""

from typing import Annotated
from uuid import UUID

import arq
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.papers.schemas import (
    IngestDOIRequest,
    IngestJobResponse,
    IngestOpenAlexRequest,
    IngestResult,
    PaperDetail,
    PaperListResponse,
    PaperResponse,
)
from paper_scraper.modules.papers.service import PaperService

router = APIRouter()


def get_paper_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaperService:
    """Dependency to get paper service instance."""
    return PaperService(db)


@router.get(
    "/",
    response_model=PaperListResponse,
    summary="List papers",
)
async def list_papers(
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> PaperListResponse:
    """List papers with pagination and optional full-text search."""
    return await paper_service.list_papers(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{paper_id}",
    response_model=PaperDetail,
    summary="Get paper details",
)
async def get_paper(
    paper_id: UUID,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperDetail:
    """Get detailed paper information including authors."""
    paper = await paper_service.get_paper(paper_id, current_user.organization_id)
    if not paper:
        raise NotFoundError("Paper", "id", str(paper_id))
    return paper  # type: ignore


@router.delete(
    "/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete paper",
)
async def delete_paper(
    paper_id: UUID,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> None:
    """Delete a paper by ID."""
    deleted = await paper_service.delete_paper(paper_id, current_user.organization_id)
    if not deleted:
        raise NotFoundError("Paper", "id", str(paper_id))


@router.post(
    "/ingest/doi",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import paper by DOI",
)
async def ingest_by_doi(
    request: IngestDOIRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperResponse:
    """Import a single paper by DOI.

    Fetches metadata from OpenAlex (primary) or Crossref (fallback).
    """
    paper = await paper_service.ingest_by_doi(
        doi=request.doi,
        organization_id=current_user.organization_id,
    )
    return paper  # type: ignore


@router.post(
    "/ingest/openalex",
    response_model=IngestResult,
    status_code=status.HTTP_200_OK,
    summary="Batch import from OpenAlex",
)
async def ingest_from_openalex(
    request: IngestOpenAlexRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> IngestResult:
    """Synchronous batch import from OpenAlex.

    For large imports (>100 papers), use the async job endpoint.
    """
    return await paper_service.ingest_from_openalex(
        query=request.query,
        organization_id=current_user.organization_id,
        max_results=request.max_results,
        filters=request.filters,
    )


@router.post(
    "/ingest/openalex/async",
    response_model=IngestJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Async batch import from OpenAlex",
)
async def ingest_from_openalex_async(
    request: IngestOpenAlexRequest,
    current_user: CurrentUser,
) -> IngestJobResponse:
    """Start async batch import from OpenAlex via arq job queue.

    Returns job ID for progress tracking.
    """
    redis = await arq.create_pool(settings.arq_redis_settings)
    job = await redis.enqueue_job(
        "ingest_openalex_task",
        str(current_user.organization_id),
        request.query,
        request.max_results,
        request.filters,
    )

    return IngestJobResponse(
        job_id=job.job_id,
        status="queued",
        message=f"Ingestion job queued for query: {request.query}",
    )
