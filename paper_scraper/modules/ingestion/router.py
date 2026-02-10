"""FastAPI router for ingestion run monitoring."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.ingestion.models import IngestRunStatus
from paper_scraper.modules.ingestion.schemas import IngestRunListResponse, IngestRunResponse
from paper_scraper.modules.ingestion.service import IngestionService

router = APIRouter()


def get_ingestion_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionService:
    """Dependency provider for ingestion service."""
    return IngestionService(db)


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
