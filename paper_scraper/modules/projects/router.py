"""FastAPI router for research groups endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.projects.models import SyncStatus
from paper_scraper.modules.projects.schemas import (
    AuthorSearchResult,
    ClusterDetailResponse,
    ClusterPaperSummary,
    ClusterResponse,
    ClusterUpdateRequest,
    InstitutionSearchResult,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    SyncResponse,
)
from paper_scraper.modules.projects.service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_project_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProjectService:
    """Dependency to get project service instance."""
    return ProjectService(db)


# =============================================================================
# OpenAlex Search Endpoints
# =============================================================================


@router.get(
    "/search/institutions",
    response_model=list[InstitutionSearchResult],
    summary="Search institutions",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def search_institutions(
    query: str = Query(..., min_length=2, max_length=200),
    max_results: int = Query(default=10, ge=1, le=25),
) -> list[InstitutionSearchResult]:
    """Search OpenAlex for institutions."""
    async with OpenAlexClient() as client:
        results = await client.search_institutions(query, max_results=max_results)
    return [InstitutionSearchResult(**r) for r in results]


@router.get(
    "/search/authors",
    response_model=list[AuthorSearchResult],
    summary="Search authors",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def search_authors(
    query: str = Query(..., min_length=2, max_length=200),
    max_results: int = Query(default=10, ge=1, le=25),
) -> list[AuthorSearchResult]:
    """Search OpenAlex for authors/researchers."""
    async with OpenAlexClient() as client:
        results = await client.search_authors(query, max_results=max_results)
    return [AuthorSearchResult(**r) for r in results]


# =============================================================================
# Research Group CRUD Endpoints
# =============================================================================


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create research group",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def create_project(
    data: ProjectCreate,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Create a new research group and optionally trigger paper import."""
    project = await project_service.create_project(
        data=data,
        organization_id=current_user.organization_id,
    )

    # Trigger background sync if OpenAlex IDs are provided
    if data.openalex_institution_id or data.openalex_author_id:
        try:
            from paper_scraper.jobs.worker import enqueue_job

            await enqueue_job(
                "sync_research_group_task",
                organization_id=str(current_user.organization_id),
                project_id=str(project.id),
                max_papers=data.max_papers,
                job_id=f"sync_rg_{project.id}",
            )
            project.sync_status = SyncStatus.IMPORTING.value
            await project_service.db.flush()
            await project_service.db.refresh(project)
        except Exception:
            logger.warning(
                "Failed to enqueue sync for research group %s", project.id
            )

    return ProjectResponse.model_validate(project)


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List research groups",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_projects(
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> ProjectListResponse:
    """List all research groups for the organization."""
    return await project_service.list_projects(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get research group",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Get a research group by ID."""
    project = await project_service.get_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )
    if not project:
        raise NotFoundError("Project", str(project_id))
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update research group",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Update a research group's name or description."""
    project = await project_service.update_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete research group",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Delete a research group and all its clusters."""
    await project_service.delete_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )


# =============================================================================
# Sync Endpoint
# =============================================================================


@router.post(
    "/{project_id}/sync",
    response_model=SyncResponse,
    summary="Sync research group",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def sync_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> SyncResponse:
    """Re-sync papers from OpenAlex and recluster."""
    project = await project_service.get_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )
    if not project:
        raise NotFoundError("Project", str(project_id))

    max_papers = (project.settings or {}).get("max_papers", 100)

    try:
        from paper_scraper.jobs.worker import enqueue_job

        await enqueue_job(
            "sync_research_group_task",
            organization_id=str(current_user.organization_id),
            project_id=str(project.id),
            max_papers=max_papers,
            job_id=f"sync_rg_{project.id}",
        )
        project.sync_status = SyncStatus.IMPORTING.value
        await project_service.db.flush()
    except Exception:
        logger.warning(
            "Failed to enqueue sync for research group %s", project.id
        )
        return SyncResponse(
            project_id=project.id,
            status=project.sync_status,
            message="Failed to start sync. Please try again later.",
        )

    return SyncResponse(
        project_id=project.id,
        status=SyncStatus.IMPORTING.value,
        message="Sync started. Papers will be imported and clustered in the background.",
    )


# =============================================================================
# Cluster Endpoints
# =============================================================================


@router.get(
    "/{project_id}/clusters",
    response_model=list[ClusterResponse],
    summary="List clusters",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_clusters(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ClusterResponse]:
    """List all topic clusters for a research group."""
    return await project_service.list_clusters(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )


@router.get(
    "/{project_id}/clusters/{cluster_id}",
    response_model=ClusterDetailResponse,
    summary="Get cluster detail",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_cluster(
    project_id: UUID,
    cluster_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ClusterDetailResponse:
    """Get a cluster with all its papers."""
    return await project_service.get_cluster_detail(
        project_id=project_id,
        cluster_id=cluster_id,
        organization_id=current_user.organization_id,
    )


@router.patch(
    "/{project_id}/clusters/{cluster_id}",
    response_model=ClusterResponse,
    summary="Update cluster label",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_cluster(
    project_id: UUID,
    cluster_id: UUID,
    data: ClusterUpdateRequest,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ClusterResponse:
    """Update a cluster's label."""
    cluster = await project_service.update_cluster_label(
        project_id=project_id,
        cluster_id=cluster_id,
        organization_id=current_user.organization_id,
        label=data.label,
    )
    return ClusterResponse(
        id=cluster.id,
        label=cluster.label,
        description=cluster.description,
        keywords=cluster.keywords or [],
        paper_count=cluster.paper_count,
        top_papers=[],
    )


# =============================================================================
# Papers Endpoint
# =============================================================================


@router.get(
    "/{project_id}/papers",
    response_model=list[ClusterPaperSummary],
    summary="List all papers",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_project_papers(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ClusterPaperSummary]:
    """List all papers in a research group (flat list)."""
    return await project_service.list_project_papers(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )
