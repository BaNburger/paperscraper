"""FastAPI router for papers endpoints."""

from typing import Annotated
from uuid import UUID

import arq
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.papers.note_service import NoteService
from paper_scraper.modules.papers.schemas import (
    IngestArxivRequest,
    IngestDOIRequest,
    IngestJobResponse,
    IngestOpenAlexRequest,
    IngestPubMedRequest,
    IngestResult,
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
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


def get_note_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteService:
    """Dependency to get note service instance."""
    return NoteService(db)


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


@router.post(
    "/ingest/pubmed",
    response_model=IngestResult,
    summary="Batch import from PubMed",
)
async def ingest_from_pubmed(
    request: IngestPubMedRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> IngestResult:
    """Batch import papers from PubMed search."""
    return await paper_service.ingest_from_pubmed(
        query=request.query,
        organization_id=current_user.organization_id,
        max_results=request.max_results,
    )


@router.post(
    "/ingest/arxiv",
    response_model=IngestResult,
    summary="Batch import from arXiv",
)
async def ingest_from_arxiv(
    request: IngestArxivRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> IngestResult:
    """Batch import papers from arXiv search."""
    return await paper_service.ingest_from_arxiv(
        query=request.query,
        organization_id=current_user.organization_id,
        max_results=request.max_results,
        category=request.category,
    )


@router.post(
    "/upload/pdf",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF file",
)
async def upload_pdf(
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
    file: UploadFile = File(...),
) -> PaperResponse:
    """
    Upload a PDF file and extract paper metadata.

    The PDF will be stored in S3 and text extracted for search/scoring.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF",
        )

    content = await file.read()
    if len(content) > 50_000_000:  # 50MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 50MB)",
        )

    paper = await paper_service.ingest_from_pdf(
        file_content=content,
        filename=file.filename,
        organization_id=current_user.organization_id,
    )
    return paper  # type: ignore


@router.post(
    "/{paper_id}/generate-pitch",
    response_model=PaperResponse,
    summary="Generate one-line pitch",
)
async def generate_pitch(
    paper_id: UUID,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperResponse:
    """Generate AI one-line pitch for paper.

    Uses LLM to create a compelling, business-friendly pitch
    that captures the core innovation (max 15 words).
    """
    paper = await paper_service.generate_pitch(paper_id, current_user.organization_id)
    return paper  # type: ignore


@router.post(
    "/{paper_id}/generate-simplified-abstract",
    response_model=PaperResponse,
    summary="Generate simplified abstract",
)
async def generate_simplified_abstract(
    paper_id: UUID,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperResponse:
    """Generate AI-simplified abstract for paper.

    Uses LLM to create a simplified version of the abstract
    that is accessible to general audiences (max 150 words).
    """
    paper = await paper_service.generate_simplified_abstract(
        paper_id, current_user.organization_id
    )
    return paper  # type: ignore


# =============================================================================
# Notes Endpoints
# =============================================================================


@router.get(
    "/{paper_id}/notes",
    response_model=NoteListResponse,
    summary="List notes for a paper",
)
async def list_notes(
    paper_id: UUID,
    current_user: CurrentUser,
    note_service: Annotated[NoteService, Depends(get_note_service)],
) -> NoteListResponse:
    """List all notes/comments for a paper."""
    return await note_service.list_notes(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )


@router.post(
    "/{paper_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add note to paper",
)
async def create_note(
    paper_id: UUID,
    request: NoteCreate,
    current_user: CurrentUser,
    note_service: Annotated[NoteService, Depends(get_note_service)],
) -> NoteResponse:
    """Add a new note/comment to a paper.

    Supports @mentions in format @{user-uuid}.
    """
    return await note_service.create_note(
        paper_id=paper_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        content=request.content,
    )


@router.get(
    "/{paper_id}/notes/{note_id}",
    response_model=NoteResponse,
    summary="Get a specific note",
)
async def get_note(
    paper_id: UUID,
    note_id: UUID,
    current_user: CurrentUser,
    note_service: Annotated[NoteService, Depends(get_note_service)],
) -> NoteResponse:
    """Get a specific note by ID."""
    return await note_service.get_note(
        paper_id=paper_id,
        note_id=note_id,
        organization_id=current_user.organization_id,
    )


@router.put(
    "/{paper_id}/notes/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
)
async def update_note(
    paper_id: UUID,
    note_id: UUID,
    request: NoteUpdate,
    current_user: CurrentUser,
    note_service: Annotated[NoteService, Depends(get_note_service)],
) -> NoteResponse:
    """Update a note (own notes only)."""
    return await note_service.update_note(
        paper_id=paper_id,
        note_id=note_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        content=request.content,
    )


@router.delete(
    "/{paper_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
)
async def delete_note(
    paper_id: UUID,
    note_id: UUID,
    current_user: CurrentUser,
    note_service: Annotated[NoteService, Depends(get_note_service)],
) -> None:
    """Delete a note (own notes only)."""
    await note_service.delete_note(
        paper_id=paper_id,
        note_id=note_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )
