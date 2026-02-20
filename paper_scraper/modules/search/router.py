"""FastAPI router for search endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.jobs.payloads import EmbeddingBackfillJobPayload
from paper_scraper.jobs.worker import enqueue_job
from paper_scraper.modules.search.schemas import (
    EmbeddingBackfillRequest,
    EmbeddingBackfillResponse,
    EmbeddingStats,
    SearchMode,
    SearchRequest,
    SearchResponse,
    SearchScope,
    SimilarPapersRequest,
    SimilarPapersResponse,
)
from paper_scraper.modules.search.service import SearchService

router = APIRouter()


def get_search_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SearchService:
    """Dependency to get search service instance."""
    return SearchService(db)


# =============================================================================
# Search Endpoints
# =============================================================================


@router.post(
    "/",
    response_model=SearchResponse,
    summary="Unified search",
    description="Search papers using full-text, semantic, or hybrid mode.",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def search(
    request: SearchRequest,
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    """
    Execute a unified search across papers.

    Supports three search modes:
    - **fulltext**: PostgreSQL trigram-based text search on title and abstract
    - **semantic**: Vector similarity search using paper embeddings
    - **hybrid**: Combines both using Reciprocal Rank Fusion (RRF)

    The hybrid mode is recommended for most use cases as it balances
    keyword matching with semantic understanding.
    """
    return await search_service.search(
        request=request,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.get(
    "/fulltext",
    response_model=SearchResponse,
    summary="Full-text search",
    description="Search papers using PostgreSQL trigram similarity.",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def fulltext_search(
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    scope: SearchScope = Query(default=SearchScope.LIBRARY, description="Search scope"),
) -> SearchResponse:
    """
    Perform full-text search using Typesense BM25 ranking.

    Use scope='catalog' to search the global paper catalog instead of your library.
    """
    request = SearchRequest(
        query=q,
        mode=SearchMode.FULLTEXT,
        scope=scope,
        page=page,
        page_size=page_size,
    )
    return await search_service.search(
        request=request,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.get(
    "/semantic",
    response_model=SearchResponse,
    summary="Semantic search",
    description="Search papers using embedding similarity.",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def semantic_search(
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    q: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    scope: SearchScope = Query(default=SearchScope.LIBRARY, description="Search scope"),
) -> SearchResponse:
    """
    Perform semantic search using vector embeddings.

    The query is embedded and compared to paper embeddings using
    cosine similarity. Only papers with embeddings are returned.
    Use scope='catalog' to search the global paper catalog.
    """
    request = SearchRequest(
        query=q,
        mode=SearchMode.SEMANTIC,
        scope=scope,
        page=page,
        page_size=page_size,
    )
    return await search_service.search(
        request=request,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.post(
    "/similar",
    response_model=SimilarPapersResponse,
    summary="Find similar papers",
    description="Find papers similar to a given paper using embedding similarity.",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def find_similar_papers(
    request: SimilarPapersRequest,
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> SimilarPapersResponse:
    """
    Find papers similar to a reference paper.

    Uses cosine similarity between paper embeddings.
    The reference paper must have an embedding generated.
    """
    return await search_service.find_similar_papers(
        paper_id=request.paper_id,
        organization_id=current_user.organization_id,
        limit=request.limit,
        min_similarity=request.min_similarity,
        filters=request.filters,
    )


@router.get(
    "/similar/{paper_id}",
    response_model=SimilarPapersResponse,
    summary="Find similar papers (GET)",
    description="Find papers similar to a given paper (simplified GET endpoint).",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def find_similar_papers_get(
    paper_id: UUID,
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    limit: int = Query(default=10, ge=1, le=50),
    min_similarity: float = Query(default=0.0, ge=0.0, le=1.0),
) -> SimilarPapersResponse:
    """
    Find papers similar to a reference paper (GET version).

    Simplified endpoint for quick similarity lookups.
    """
    return await search_service.find_similar_papers(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        limit=limit,
        min_similarity=min_similarity,
    )


# =============================================================================
# Embedding Management Endpoints
# =============================================================================


@router.get(
    "/embeddings/stats",
    response_model=EmbeddingStats,
    summary="Get embedding statistics",
    description="Get statistics about paper embeddings.",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_embedding_stats(
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> EmbeddingStats:
    """
    Get embedding statistics for the organization.

    Returns count of papers with and without embeddings.
    """
    return await search_service.get_embedding_stats(current_user.organization_id)


@router.post(
    "/embeddings/backfill",
    response_model=EmbeddingBackfillResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start embedding backfill job",
    description="Start a background job to generate embeddings for papers without them.",
    dependencies=[Depends(require_permission(Permission.SCORING_TRIGGER))],
)
async def start_embedding_backfill(
    request: EmbeddingBackfillRequest,
    current_user: CurrentUser,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> EmbeddingBackfillResponse:
    """
    Start an async job to backfill embeddings for papers that don't have them.

    This is useful after bulk importing papers or when embeddings need regeneration.
    """
    # Count papers needing embeddings
    papers_to_process = await search_service.count_papers_without_embeddings(
        current_user.organization_id
    )

    if request.max_papers:
        papers_to_process = min(papers_to_process, request.max_papers)

    if papers_to_process == 0:
        return EmbeddingBackfillResponse(
            job_id="",
            status="completed",
            papers_to_process=0,
            message="All papers already have embeddings",
        )

    # Queue the job
    payload = EmbeddingBackfillJobPayload(
        organization_id=current_user.organization_id,
        batch_size=request.batch_size,
        max_papers=request.max_papers,
    )

    job = await enqueue_job(
        "backfill_embeddings_task",
        str(payload.organization_id),
        payload.batch_size,
        payload.max_papers,
    )

    return EmbeddingBackfillResponse(
        job_id=job.job_id if job else "",
        status="queued",
        papers_to_process=papers_to_process,
        message=f"Backfill job queued for {papers_to_process} papers",
    )
