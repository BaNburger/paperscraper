"""FastAPI router for ingestion run monitoring."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.jobs.payloads import SourceIngestionJobPayload
from paper_scraper.modules.ingestion.models import IngestRunStatus
from paper_scraper.modules.ingestion.schemas import IngestRunListResponse, IngestRunResponse
from paper_scraper.modules.ingestion.service import IngestionService
from paper_scraper.modules.papers.schemas import (
    IngestArxivRequest,
    IngestJobResponse,
    IngestOpenAlexRequest,
    IngestPubMedRequest,
    IngestSemanticScholarRequest,
)

router = APIRouter()

IngestionSource = Literal["openalex", "pubmed", "arxiv", "semantic_scholar"]


def get_ingestion_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionService:
    """Dependency provider for ingestion service."""
    return IngestionService(db)


async def _enqueue_ingestion_job(
    *,
    source: IngestionSource,
    query: str,
    max_results: int,
    filters: dict,
    current_user: CurrentUser,
    ingestion_service: IngestionService,
) -> IngestJobResponse:
    """Create queued run and enqueue unified source-ingestion worker job."""
    run = await ingestion_service.create_run(
        source=source,
        organization_id=current_user.organization_id,
        initiated_by_id=current_user.id,
        cursor_before={},
        status=IngestRunStatus.QUEUED,
    )

    # Persist queued run before enqueueing to avoid worker race conditions.
    await ingestion_service.db.commit()
    await ingestion_service.db.refresh(run)

    payload = SourceIngestionJobPayload(
        ingest_run_id=run.id,
        source=source,
        organization_id=current_user.organization_id,
        initiated_by_id=current_user.id,
        query=query,
        max_results=max_results,
        filters=filters,
    )

    try:
        from paper_scraper.jobs.worker import enqueue_job

        job = await enqueue_job(
            "ingest_source_task",
            payload.model_dump(mode="json"),
            job_id=str(run.id),
        )
    except Exception as exc:
        await ingestion_service.complete_run(
            run_id=run.id,
            status=IngestRunStatus.FAILED,
            cursor_after=run.cursor_after,
            stats_json={
                "papers_created": 0,
                "papers_matched": 0,
                "source_records_inserted": 0,
                "source_records_duplicates": 0,
                "errors": [str(exc)],
            },
            error_message=str(exc),
        )
        await ingestion_service.db.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to enqueue ingestion job",
        ) from exc

    return IngestJobResponse(
        job_id=job.job_id,
        ingest_run_id=run.id,
        source=source,
        status=IngestRunStatus.QUEUED.value,
        message="Ingestion job queued successfully",
    )


@router.get(
    "/runs",
    response_model=IngestRunListResponse,
    summary="List ingestion runs",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_ingestion_runs(
    current_user: CurrentUser,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source: str | None = Query(default=None),
    status: IngestRunStatus | None = Query(default=None),
) -> IngestRunListResponse:
    """List ingestion runs for the current organization."""
    return await ingestion_service.list_runs(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        source=source,
        status=status,
    )


@router.post(
    "/sources/openalex/runs",
    response_model=IngestJobResponse,
    status_code=202,
    summary="Start async OpenAlex ingestion run",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def enqueue_openalex_run(
    request: IngestOpenAlexRequest,
    current_user: CurrentUser,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestJobResponse:
    """Queue asynchronous OpenAlex source ingestion."""
    return await _enqueue_ingestion_job(
        source="openalex",
        query=request.query,
        max_results=request.max_results,
        filters={"filters": request.filters},
        current_user=current_user,
        ingestion_service=ingestion_service,
    )


@router.post(
    "/sources/pubmed/runs",
    response_model=IngestJobResponse,
    status_code=202,
    summary="Start async PubMed ingestion run",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def enqueue_pubmed_run(
    request: IngestPubMedRequest,
    current_user: CurrentUser,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestJobResponse:
    """Queue asynchronous PubMed source ingestion."""
    return await _enqueue_ingestion_job(
        source="pubmed",
        query=request.query,
        max_results=request.max_results,
        filters={},
        current_user=current_user,
        ingestion_service=ingestion_service,
    )


@router.post(
    "/sources/arxiv/runs",
    response_model=IngestJobResponse,
    status_code=202,
    summary="Start async arXiv ingestion run",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def enqueue_arxiv_run(
    request: IngestArxivRequest,
    current_user: CurrentUser,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestJobResponse:
    """Queue asynchronous arXiv source ingestion."""
    return await _enqueue_ingestion_job(
        source="arxiv",
        query=request.query,
        max_results=request.max_results,
        filters={"category": request.category} if request.category else {},
        current_user=current_user,
        ingestion_service=ingestion_service,
    )


@router.post(
    "/sources/semantic-scholar/runs",
    response_model=IngestJobResponse,
    status_code=202,
    summary="Start async Semantic Scholar ingestion run",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def enqueue_semantic_scholar_run(
    request: IngestSemanticScholarRequest,
    current_user: CurrentUser,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestJobResponse:
    """Queue asynchronous Semantic Scholar source ingestion."""
    return await _enqueue_ingestion_job(
        source="semantic_scholar",
        query=request.query,
        max_results=request.max_results,
        filters={},
        current_user=current_user,
        ingestion_service=ingestion_service,
    )


@router.get(
    "/runs/{run_id}",
    response_model=IngestRunResponse,
    summary="Get ingestion run",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_ingestion_run(
    run_id: UUID,
    current_user: CurrentUser,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestRunResponse:
    """Get details for a single ingestion run."""
    run = await ingestion_service.get_run(
        run_id=run_id,
        organization_id=current_user.organization_id,
    )
    return IngestRunResponse.model_validate(run)
