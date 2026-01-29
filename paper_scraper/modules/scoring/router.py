"""FastAPI router for scoring endpoints."""

from typing import Annotated
from uuid import UUID

import arq
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.config import settings
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.scoring.schemas import (
    BatchScoreRequest,
    EmbeddingResponse,
    GenerateEmbeddingRequest,
    PaperScoreListResponse,
    PaperScoreResponse,
    ScoreRequest,
    ScoringJobListResponse,
    ScoringJobResponse,
)
from paper_scraper.modules.scoring.service import ScoringService

router = APIRouter()


def get_scoring_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ScoringService:
    """Dependency to get scoring service instance."""
    return ScoringService(db)


# =============================================================================
# Paper Scoring Endpoints
# =============================================================================


@router.post(
    "/papers/{paper_id}/score",
    response_model=PaperScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score a paper",
)
async def score_paper(
    paper_id: UUID,
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    request: ScoreRequest | None = None,
) -> PaperScoreResponse:
    """
    Score a paper across all AI dimensions.

    Triggers scoring for novelty, IP potential, marketability,
    feasibility, and commercialization dimensions.
    """
    request = request or ScoreRequest()
    score = await scoring_service.score_paper(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        weights=request.weights,
        dimensions=request.dimensions,
        force_rescore=request.force_rescore,
    )
    return PaperScoreResponse.model_validate(score)


@router.get(
    "/papers/{paper_id}/scores",
    response_model=PaperScoreListResponse,
    summary="Get paper score history",
)
async def get_paper_scores(
    paper_id: UUID,
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
) -> PaperScoreListResponse:
    """Get all scores for a paper with pagination."""
    return await scoring_service.get_paper_scores(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/papers/{paper_id}/scores/latest",
    response_model=PaperScoreResponse,
    summary="Get latest paper score",
)
async def get_latest_score(
    paper_id: UUID,
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
) -> PaperScoreResponse:
    """Get the most recent score for a paper."""
    score = await scoring_service.get_latest_score(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )
    if not score:
        raise NotFoundError("Score", paper_id)
    return PaperScoreResponse.model_validate(score)


# =============================================================================
# Organization Scores List
# =============================================================================


@router.get(
    "/",
    response_model=PaperScoreListResponse,
    summary="List all paper scores",
)
async def list_scores(
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    min_score: float | None = Query(default=None, ge=0.0, le=10.0),
    max_score: float | None = Query(default=None, ge=0.0, le=10.0),
) -> PaperScoreListResponse:
    """
    List all paper scores for the organization.

    Returns the latest score per paper, ordered by overall score descending.
    """
    return await scoring_service.list_org_scores(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        min_score=min_score,
        max_score=max_score,
    )


# =============================================================================
# Batch Scoring Endpoints
# =============================================================================


@router.post(
    "/batch",
    response_model=ScoringJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start batch scoring job",
)
async def batch_score(
    request: BatchScoreRequest,
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
) -> ScoringJobResponse:
    """
    Start a batch scoring job for multiple papers.

    Papers are scored asynchronously via background job queue.
    """
    # Create job record
    job = await scoring_service.create_batch_job(
        paper_ids=request.paper_ids,
        organization_id=current_user.organization_id,
        job_type="batch",
    )

    # Enqueue arq job
    redis = await arq.create_pool(settings.arq_redis_settings)
    arq_job = await redis.enqueue_job(
        "score_papers_batch_task",
        str(job.id),
        str(current_user.organization_id),
        [str(pid) for pid in request.paper_ids],
        request.weights.model_dump() if request.weights else None,
    )

    # Update job with arq reference
    job.arq_job_id = arq_job.job_id
    await scoring_service.db.commit()

    return ScoringJobResponse.model_validate(job)


@router.get(
    "/jobs",
    response_model=ScoringJobListResponse,
    summary="List scoring jobs",
)
async def list_jobs(
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
) -> ScoringJobListResponse:
    """List all scoring jobs for the organization."""
    return await scoring_service.list_jobs(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=ScoringJobResponse,
    summary="Get scoring job status",
)
async def get_job(
    job_id: UUID,
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
) -> ScoringJobResponse:
    """Get status of a scoring job."""
    job = await scoring_service.get_job(
        job_id=job_id,
        organization_id=current_user.organization_id,
    )
    if not job:
        raise NotFoundError("ScoringJob", job_id)
    return ScoringJobResponse.model_validate(job)


# =============================================================================
# Embedding Endpoints
# =============================================================================


@router.post(
    "/papers/{paper_id}/embedding",
    response_model=EmbeddingResponse,
    summary="Generate paper embedding",
)
async def generate_embedding(
    paper_id: UUID,
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    request: GenerateEmbeddingRequest | None = None,
) -> EmbeddingResponse:
    """
    Generate vector embedding for a paper.

    Embeddings are used for semantic similarity search to find
    related papers for scoring context.
    """
    request = request or GenerateEmbeddingRequest()
    generated = await scoring_service.generate_embedding(
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        force_regenerate=request.force_regenerate,
    )

    return EmbeddingResponse(
        paper_id=paper_id,
        has_embedding=True,
        embedding_dimensions=1536,
        message="Embedding generated" if generated else "Embedding already exists",
    )


@router.post(
    "/embeddings/backfill",
    response_model=dict,
    summary="Backfill embeddings for papers",
)
async def backfill_embeddings(
    current_user: CurrentUser,
    scoring_service: Annotated[ScoringService, Depends(get_scoring_service)],
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    """
    Generate embeddings for papers that don't have them.

    Useful for backfilling after bulk imports.
    """
    count = await scoring_service.batch_generate_embeddings(
        organization_id=current_user.organization_id,
        limit=limit,
    )
    return {
        "embeddings_generated": count,
        "message": f"Generated {count} embeddings",
    }
