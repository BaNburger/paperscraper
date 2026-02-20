"""Pydantic schemas for the global paper catalog module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogPaperSummary(BaseModel):
    """Summary of a paper in the global catalog."""

    id: UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    source: str
    publication_date: datetime | None = None
    journal: str | None = None
    keywords: list[str] = Field(default_factory=list)
    citations_count: int | None = None
    has_embedding: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class CatalogPaperDetail(CatalogPaperSummary):
    """Full detail of a global catalog paper."""

    source_id: str | None = None
    raw_metadata: dict | None = None


class CatalogListResponse(BaseModel):
    """Paginated list of catalog papers."""

    items: list[CatalogPaperSummary]
    total: int
    page: int
    page_size: int
    pages: int


class CatalogStatsResponse(BaseModel):
    """Statistics about the global paper catalog."""

    total_papers: int
    total_with_embeddings: int
    sources: dict[str, int]  # source -> count
    date_range: dict[str, str | None]  # min_date, max_date


class ClaimPaperRequest(BaseModel):
    """Request to claim a global paper into an org's library."""

    paper_id: UUID


class ClaimPaperResponse(BaseModel):
    """Response from claiming a paper."""

    paper_id: UUID
    organization_id: UUID
    message: str
