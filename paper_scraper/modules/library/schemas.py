"""Pydantic schemas for library module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.library.models import HighlightSource


class LibraryCollectionCreate(BaseModel):
    """Create request for library collection."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None


class LibraryCollectionUpdate(BaseModel):
    """Partial update request for library collection."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None


class LibraryCollectionResponse(BaseModel):
    """Collection response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    parent_id: UUID | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    item_count: int = 0


class LibraryCollectionListResponse(BaseModel):
    """Collection list response."""

    items: list[LibraryCollectionResponse]
    total: int


class CollectionPaperResponse(BaseModel):
    """Response when adding/removing a paper in a collection."""

    collection_id: UUID
    paper_id: UUID
    added: bool


class TagCreate(BaseModel):
    """Create request for a user paper tag."""

    tag: str = Field(min_length=1, max_length=64)


class PaperTagResponse(BaseModel):
    """Paper tag response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    paper_id: UUID
    tag: str
    created_by: UUID | None
    created_at: datetime


class PaperTagAggregate(BaseModel):
    """Aggregated tag item with usage count."""

    tag: str
    usage_count: int


class PaperTagListResponse(BaseModel):
    """List response for tags."""

    items: list[PaperTagAggregate]
    total: int


class ReaderChunkResponse(BaseModel):
    """Chunk in full-text reader response."""

    id: UUID
    chunk_index: int
    page_number: int | None = None
    text: str
    char_start: int
    char_end: int


class FullTextStatusResponse(BaseModel):
    """Current full-text status for a paper."""

    available: bool
    source: str | None = None
    chunk_count: int = 0
    hydrated_at: datetime | None = None


class ReaderResponse(BaseModel):
    """Reader payload with chunked full text."""

    paper_id: UUID
    title: str
    status: FullTextStatusResponse
    chunks: list[ReaderChunkResponse]


class HydrateFullTextResponse(BaseModel):
    """Hydration response payload."""

    paper_id: UUID
    hydrated: bool
    source: str | None = None
    chunks_created: int = 0
    message: str


class HighlightCreate(BaseModel):
    """Create request for manual highlight."""

    chunk_id: UUID | None = None
    chunk_ref: str | None = Field(default=None, max_length=128)
    quote: str = Field(min_length=1, max_length=5000)
    insight_summary: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class HighlightUpdate(BaseModel):
    """Update request for highlight."""

    quote: str | None = Field(default=None, min_length=1, max_length=5000)
    insight_summary: str | None = Field(default=None, min_length=1, max_length=5000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_active: bool | None = None


class PaperHighlightResponse(BaseModel):
    """Highlight response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    paper_id: UUID
    chunk_id: UUID | None
    chunk_ref: str
    quote: str
    insight_summary: str
    confidence: float
    source: HighlightSource
    generation_id: UUID
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class PaperHighlightListResponse(BaseModel):
    """List response for highlights."""

    items: list[PaperHighlightResponse]
    total: int


class GenerateHighlightsRequest(BaseModel):
    """Request to generate AI highlights for a paper."""

    target_count: int = Field(default=8, ge=5, le=12)
