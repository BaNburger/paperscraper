"""Pydantic schemas for research groups module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# OpenAlex Search Schemas
# =============================================================================


class InstitutionSearchResult(BaseModel):
    """Result from OpenAlex institution search."""

    openalex_id: str
    display_name: str
    country_code: str | None = None
    type: str | None = None
    works_count: int = 0
    cited_by_count: int = 0


class AuthorSearchResult(BaseModel):
    """Result from OpenAlex author search."""

    openalex_id: str
    display_name: str
    works_count: int = 0
    cited_by_count: int = 0
    last_known_institution: str | None = None


# =============================================================================
# Research Group CRUD Schemas
# =============================================================================


class ProjectCreate(BaseModel):
    """Schema for creating a research group."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    openalex_institution_id: str | None = Field(
        default=None, max_length=100, description="OpenAlex institution ID"
    )
    openalex_author_id: str | None = Field(
        default=None, max_length=100, description="OpenAlex author ID"
    )
    institution_name: str | None = Field(
        default=None, max_length=255, description="Institution display name"
    )
    pi_name: str | None = Field(
        default=None, max_length=255, description="Principal investigator name"
    )
    max_papers: int = Field(
        default=100, ge=10, le=500, description="Maximum papers to import"
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a research group."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    """Research group response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    institution_name: str | None = None
    openalex_institution_id: str | None = None
    pi_name: str | None = None
    openalex_author_id: str | None = None
    paper_count: int = 0
    cluster_count: int = 0
    sync_status: str = "idle"
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated list of research groups."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Cluster Schemas
# =============================================================================


class ClusterPaperSummary(BaseModel):
    """Minimal paper info for cluster views."""

    id: UUID
    title: str
    authors_display: str = ""
    publication_date: str | None = None
    citations_count: int | None = None
    similarity_score: float | None = None


class ClusterResponse(BaseModel):
    """Cluster summary in research group view."""

    id: UUID
    label: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    paper_count: int = 0
    top_papers: list[ClusterPaperSummary] = Field(default_factory=list)


class ClusterDetailResponse(BaseModel):
    """Full cluster detail with all papers."""

    id: UUID
    label: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    paper_count: int = 0
    papers: list[ClusterPaperSummary] = Field(default_factory=list)


class ClusterUpdateRequest(BaseModel):
    """Request to update a cluster label."""

    label: str = Field(..., min_length=1, max_length=255)


# =============================================================================
# Sync Schemas
# =============================================================================


class SyncResponse(BaseModel):
    """Response after triggering a research group sync."""

    project_id: UUID
    status: str
    message: str
