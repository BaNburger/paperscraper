"""Pydantic schemas for projects module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.projects.models import RejectionReason


# =============================================================================
# Stage Schemas
# =============================================================================


class StageConfig(BaseModel):
    """Configuration for a pipeline stage."""

    name: str = Field(..., description="Stage identifier (snake_case)")
    label: str = Field(..., description="Display label for the stage")
    order: int = Field(..., ge=0, description="Order in the pipeline")


# =============================================================================
# Scoring Weights Schema
# =============================================================================


class ProjectScoringWeights(BaseModel):
    """Scoring weights configuration for a project."""

    novelty: float = Field(default=0.20, ge=0.0, le=1.0)
    ip_potential: float = Field(default=0.20, ge=0.0, le=1.0)
    marketability: float = Field(default=0.20, ge=0.0, le=1.0)
    feasibility: float = Field(default=0.20, ge=0.0, le=1.0)
    commercialization: float = Field(default=0.20, ge=0.0, le=1.0)


# =============================================================================
# Project Schemas
# =============================================================================


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    stages: list[StageConfig] | None = Field(
        default=None,
        description="Custom pipeline stages. If not provided, default stages are used.",
    )
    scoring_weights: ProjectScoringWeights | None = Field(
        default=None,
        description="Custom scoring weights for this project.",
    )
    settings: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    stages: list[StageConfig] | None = None
    scoring_weights: ProjectScoringWeights | None = None
    settings: dict[str, Any] | None = None


class ProjectResponse(ProjectBase):
    """Project response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    stages: list[dict[str, Any]]
    scoring_weights: dict[str, float]
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Paper in Project Schemas
# =============================================================================


class AddPaperToProjectRequest(BaseModel):
    """Request to add a paper to a project."""

    paper_id: UUID
    stage: str = Field(default="inbox", description="Initial stage for the paper")
    assigned_to_id: UUID | None = None
    notes: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)


class BatchAddPapersRequest(BaseModel):
    """Request to add multiple papers to a project."""

    paper_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    stage: str = Field(default="inbox")
    tags: list[str] = Field(default_factory=list)


class MovePaperRequest(BaseModel):
    """Request to move a paper to a different stage."""

    stage: str = Field(..., description="Target stage")
    position: int | None = Field(
        default=None, description="Position within stage (0 = top)"
    )
    comment: str | None = Field(
        default=None, description="Comment for the stage transition"
    )


class RejectPaperRequest(BaseModel):
    """Request to reject a paper."""

    reason: RejectionReason
    notes: str | None = None
    comment: str | None = Field(
        default=None, description="Comment for the stage transition"
    )


class UpdatePaperStatusRequest(BaseModel):
    """Request to update paper status in project."""

    assigned_to_id: UUID | None = None
    notes: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = None


# =============================================================================
# Paper Project Status Response Schemas
# =============================================================================


class PaperSummaryForProject(BaseModel):
    """Minimal paper info for project views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    journal: str | None = None
    publication_date: datetime | None = None


class UserSummary(BaseModel):
    """Minimal user info for assignments."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None = None


class PaperProjectStatusResponse(BaseModel):
    """Response for paper status in a project."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    paper_id: UUID
    project_id: UUID
    stage: str
    position: int
    assigned_to_id: UUID | None = None
    notes: str | None = None
    rejection_reason: RejectionReason | None = None
    rejection_notes: str | None = None
    priority: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    stage_entered_at: datetime


class PaperInProjectResponse(BaseModel):
    """Paper with its project status for KanBan view."""

    model_config = ConfigDict(from_attributes=True)

    status: PaperProjectStatusResponse
    paper: PaperSummaryForProject
    assigned_to: UserSummary | None = None

    # Include latest score if available
    latest_score: dict[str, Any] | None = None


# =============================================================================
# KanBan View Schemas
# =============================================================================


class KanBanStage(BaseModel):
    """A stage in the KanBan board with its papers."""

    name: str
    label: str
    order: int
    paper_count: int
    papers: list[PaperInProjectResponse]


class KanBanBoardResponse(BaseModel):
    """Full KanBan board view."""

    project: ProjectResponse
    stages: list[KanBanStage]
    total_papers: int


# =============================================================================
# Stage History Schemas
# =============================================================================


class StageHistoryEntry(BaseModel):
    """A single stage transition in history."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_stage: str | None
    to_stage: str
    comment: str | None
    changed_by: UserSummary | None = None
    created_at: datetime


class PaperHistoryResponse(BaseModel):
    """History of stage transitions for a paper in a project."""

    paper_id: UUID
    project_id: UUID
    history: list[StageHistoryEntry]


# =============================================================================
# Statistics Schemas
# =============================================================================


class ProjectStatistics(BaseModel):
    """Statistics for a project."""

    project_id: UUID
    total_papers: int
    papers_by_stage: dict[str, int]
    papers_by_priority: dict[int, int]
    avg_time_per_stage: dict[str, float]  # Average hours in each stage
    rejection_reasons: dict[str, int]
