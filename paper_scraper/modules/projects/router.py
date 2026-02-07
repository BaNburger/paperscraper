"""FastAPI router for projects endpoints."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.permissions import Permission
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.projects.schemas import (
    AddPaperToProjectRequest,
    BatchAddPapersRequest,
    KanBanBoardResponse,
    MovePaperRequest,
    PaperHistoryResponse,
    PaperInProjectResponse,
    PaperProjectStatusResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatistics,
    ProjectUpdate,
    RejectPaperRequest,
    UpdatePaperStatusRequest,
)
from paper_scraper.modules.projects.service import ProjectService

router = APIRouter()


def get_project_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProjectService:
    """Dependency to get project service instance."""
    return ProjectService(db)


# =============================================================================
# Project CRUD Endpoints
# =============================================================================


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def create_project(
    data: ProjectCreate,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Create a new project for managing papers in a KanBan pipeline."""
    project = await project_service.create_project(
        data=data,
        organization_id=current_user.organization_id,
    )
    return ProjectResponse.model_validate(project)


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List projects",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_projects(
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> ProjectListResponse:
    """List all projects for the organization."""
    return await project_service.list_projects(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Get a project by ID."""
    project = await project_service.get_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )
    if not project:
        raise NotFoundError("Project", project_id)
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Update a project's name, description, stages, or settings."""
    project = await project_service.update_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
        data=data,
    )
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Delete a project and all its paper associations."""
    await project_service.delete_project(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )


# =============================================================================
# KanBan Board Endpoints
# =============================================================================


@router.get(
    "/{project_id}/kanban",
    response_model=KanBanBoardResponse,
    summary="Get KanBan board",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_kanban_board(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    include_scores: bool = Query(default=True),
) -> KanBanBoardResponse:
    """
    Get the complete KanBan board view for a project.

    Returns all stages with their papers, including paper metadata,
    assignment info, and optionally the latest AI scores.
    """
    return await project_service.get_kanban_board(
        project_id=project_id,
        organization_id=current_user.organization_id,
        include_scores=include_scores,
    )


@router.get(
    "/{project_id}/statistics",
    response_model=ProjectStatistics,
    summary="Get project statistics",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_project_statistics(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectStatistics:
    """Get statistics for a project including paper counts by stage and rejection reasons."""
    return await project_service.get_project_statistics(
        project_id=project_id,
        organization_id=current_user.organization_id,
    )


# =============================================================================
# Paper Management Endpoints
# =============================================================================


@router.post(
    "/{project_id}/papers",
    response_model=PaperProjectStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add paper to project",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def add_paper_to_project(
    project_id: UUID,
    request: AddPaperToProjectRequest,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> PaperProjectStatusResponse:
    """Add a paper to a project at a specific stage."""
    status_obj = await project_service.add_paper_to_project(
        project_id=project_id,
        paper_id=request.paper_id,
        organization_id=current_user.organization_id,
        stage=request.stage,
        assigned_to_id=request.assigned_to_id,
        notes=request.notes,
        priority=request.priority,
        tags=request.tags,
        user_id=current_user.id,
    )
    return PaperProjectStatusResponse.model_validate(status_obj)


@router.post(
    "/{project_id}/papers/batch",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Batch add papers to project",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def batch_add_papers(
    project_id: UUID,
    request: BatchAddPapersRequest,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> dict[str, Any]:
    """Add multiple papers to a project at once."""
    return await project_service.batch_add_papers(
        project_id=project_id,
        organization_id=current_user.organization_id,
        request=request,
        user_id=current_user.id,
    )


@router.get(
    "/{project_id}/papers/{paper_id}",
    response_model=PaperInProjectResponse,
    summary="Get paper in project",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_paper_in_project(
    project_id: UUID,
    paper_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> PaperInProjectResponse:
    """Get a paper's status and details within a project."""
    result = await project_service.get_paper_in_project(
        project_id=project_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )
    if not result:
        raise NotFoundError("PaperProjectStatus", paper_id)
    return result


@router.delete(
    "/{project_id}/papers/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove paper from project",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def remove_paper_from_project(
    project_id: UUID,
    paper_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Remove a paper from a project (does not delete the paper itself)."""
    await project_service.remove_paper_from_project(
        project_id=project_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )


# =============================================================================
# Paper Movement Endpoints
# =============================================================================


@router.patch(
    "/{project_id}/papers/{paper_id}/move",
    response_model=PaperProjectStatusResponse,
    summary="Move paper to stage",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def move_paper(
    project_id: UUID,
    paper_id: UUID,
    request: MovePaperRequest,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> PaperProjectStatusResponse:
    """Move a paper to a different stage in the KanBan pipeline."""
    status_obj = await project_service.move_paper(
        project_id=project_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        stage=request.stage,
        position=request.position,
        comment=request.comment,
        user_id=current_user.id,
    )
    return PaperProjectStatusResponse.model_validate(status_obj)


@router.post(
    "/{project_id}/papers/{paper_id}/reject",
    response_model=PaperProjectStatusResponse,
    summary="Reject paper",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def reject_paper(
    project_id: UUID,
    paper_id: UUID,
    request: RejectPaperRequest,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> PaperProjectStatusResponse:
    """Reject a paper with a reason, moving it to the rejected stage."""
    status_obj = await project_service.reject_paper(
        project_id=project_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        reason=request.reason,
        notes=request.notes,
        comment=request.comment,
        user_id=current_user.id,
    )
    return PaperProjectStatusResponse.model_validate(status_obj)


@router.patch(
    "/{project_id}/papers/{paper_id}/status",
    response_model=PaperProjectStatusResponse,
    summary="Update paper status",
    dependencies=[Depends(require_permission(Permission.PAPERS_WRITE))],
)
async def update_paper_status(
    project_id: UUID,
    paper_id: UUID,
    request: UpdatePaperStatusRequest,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> PaperProjectStatusResponse:
    """Update paper metadata in project (assignment, notes, priority, tags)."""
    status_obj = await project_service.update_paper_status(
        project_id=project_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
        assigned_to_id=request.assigned_to_id,
        notes=request.notes,
        priority=request.priority,
        tags=request.tags,
    )
    return PaperProjectStatusResponse.model_validate(status_obj)


# =============================================================================
# History Endpoints
# =============================================================================


@router.get(
    "/{project_id}/papers/{paper_id}/history",
    response_model=PaperHistoryResponse,
    summary="Get paper history",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_paper_history(
    project_id: UUID,
    paper_id: UUID,
    current_user: CurrentUser,
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> PaperHistoryResponse:
    """Get the stage transition history for a paper in a project."""
    history = await project_service.get_paper_history(
        project_id=project_id,
        paper_id=paper_id,
        organization_id=current_user.organization_id,
    )
    return PaperHistoryResponse(
        paper_id=paper_id,
        project_id=project_id,
        history=history,
    )
