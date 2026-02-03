"""Pydantic schemas for papers module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.papers.models import PaperSource


# =============================================================================
# Author Schemas
# =============================================================================


class AuthorBase(BaseModel):
    """Base author schema."""

    name: str
    orcid: str | None = None
    affiliations: list[str] = Field(default_factory=list)


class AuthorResponse(AuthorBase):
    """Author response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    openalex_id: str | None = None
    h_index: int | None = None
    citation_count: int | None = None
    works_count: int | None = None


class PaperAuthorResponse(BaseModel):
    """Paper-author relationship response."""

    model_config = ConfigDict(from_attributes=True)

    author: AuthorResponse
    position: int
    is_corresponding: bool


# =============================================================================
# Paper Schemas
# =============================================================================


class PaperBase(BaseModel):
    """Base paper schema."""

    title: str
    abstract: str | None = None
    doi: str | None = None
    publication_date: datetime | None = None
    journal: str | None = None
    keywords: list[str] = Field(default_factory=list)


class PaperCreate(PaperBase):
    """Schema for manual paper creation."""


class PaperResponse(BaseModel):
    """Paper response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    source: PaperSource
    source_id: str | None = None
    publication_date: datetime | None = None
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    keywords: list[str] = Field(default_factory=list)
    references_count: int | None = None
    citations_count: int | None = None
    one_line_pitch: str | None = None
    simplified_abstract: str | None = None
    has_pdf: bool = False
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime


class PaperDetail(PaperResponse):
    """Detailed paper response with authors."""

    authors: list[PaperAuthorResponse] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)


class PaperListResponse(BaseModel):
    """Paginated paper list response."""

    items: list[PaperResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Ingestion Schemas
# =============================================================================


class IngestDOIRequest(BaseModel):
    """Request to ingest paper by DOI."""

    doi: str = Field(..., description="DOI of the paper to import")


class IngestOpenAlexRequest(BaseModel):
    """Request to batch ingest from OpenAlex."""

    query: str = Field(..., description="Search query for OpenAlex")
    max_results: int = Field(default=100, ge=1, le=1000)
    filters: dict = Field(default_factory=dict)


class IngestPubMedRequest(BaseModel):
    """Request to batch ingest from PubMed."""

    query: str = Field(..., description="PubMed search query")
    max_results: int = Field(default=100, ge=1, le=1000)


class IngestArxivRequest(BaseModel):
    """Request to batch ingest from arXiv."""

    query: str = Field(..., description="arXiv search query")
    max_results: int = Field(default=100, ge=1, le=1000)
    category: str | None = Field(
        default=None,
        description="Optional arXiv category filter (e.g., 'cs.AI', 'physics.med-ph')",
    )


class IngestJobResponse(BaseModel):
    """Response for async ingestion job."""

    job_id: str
    status: str = "queued"
    message: str


class IngestResult(BaseModel):
    """Result of ingestion operation."""

    papers_created: int
    papers_updated: int
    papers_skipped: int
    errors: list[str] = Field(default_factory=list)


# =============================================================================
# Note Schemas
# =============================================================================


class NoteUserResponse(BaseModel):
    """User info for note responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str | None
    email: str


class NoteCreate(BaseModel):
    """Request to create a note."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Note content. Supports @mentions in format @{user_id}",
    )


class NoteUpdate(BaseModel):
    """Request to update a note."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Updated note content",
    )


class NoteResponse(BaseModel):
    """Response schema for a note."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    paper_id: UUID
    user_id: UUID
    content: str
    mentions: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    user: NoteUserResponse | None = None


class NoteListResponse(BaseModel):
    """List of notes for a paper."""

    items: list[NoteResponse]
    total: int
