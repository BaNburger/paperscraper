"""Pydantic schemas for discovery module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryRunResponse(BaseModel):
    """Response schema for a single discovery run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    saved_search_id: UUID
    organization_id: UUID
    status: str
    source: str
    ingest_run_id: UUID | None = None
    papers_found: int
    papers_imported: int
    papers_skipped: int
    papers_added_to_project: int
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime


class DiscoveryRunListResponse(BaseModel):
    """Paginated list of discovery runs."""

    items: list[DiscoveryRunResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DiscoveryProfileSummary(BaseModel):
    """Summary of a discovery profile (saved search with auto-import)."""

    id: UUID
    name: str
    query: str
    semantic_description: str | None = None
    import_sources: list[str] = Field(default_factory=list)
    target_project_id: UUID | None = None
    target_project_name: str | None = None
    discovery_frequency: str | None = None
    max_import_per_run: int = 20
    last_discovery_at: datetime | None = None
    auto_import_enabled: bool = True
    created_at: datetime
    # Last run summary
    last_run_status: str | None = None
    total_papers_imported: int = 0


class DiscoveryProfileListResponse(BaseModel):
    """List of active discovery profiles."""

    items: list[DiscoveryProfileSummary]
    total: int


class DiscoveryTriggerResponse(BaseModel):
    """Response after triggering a discovery run."""

    saved_search_id: UUID
    runs: list[DiscoveryRunResponse]
    total_papers_imported: int
    total_papers_added_to_project: int
    message: str
