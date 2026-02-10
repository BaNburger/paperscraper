"""Pydantic schemas for ingestion pipeline APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.ingestion.models import IngestRunStatus


class IngestRunResponse(BaseModel):
    """Ingestion run response."""

    id: UUID
    source: str
    organization_id: UUID | None
    status: IngestRunStatus
    cursor_before: dict
    cursor_after: dict
    stats_json: dict
    idempotency_key: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestRunListResponse(BaseModel):
    """Paginated ingestion run list."""

    items: list[IngestRunResponse]
    total: int
    page: int
    page_size: int
    pages: int


class IngestRunListFilters(BaseModel):
    """Filter params for ingestion runs."""

    source: str | None = None
    status: IngestRunStatus | None = None


class IngestRunUpdateRequest(BaseModel):
    """Internal schema for updating run status."""

    status: IngestRunStatus
    cursor_after: dict = Field(default_factory=dict)
    stats_json: dict = Field(default_factory=dict)
    error_message: str | None = None
