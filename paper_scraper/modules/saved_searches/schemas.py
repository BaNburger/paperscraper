"""Pydantic schemas for saved searches module."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.search.schemas import SearchFilters, SearchMode


class AlertFrequency(str, Enum):
    """Alert frequency options."""

    IMMEDIATELY = "immediately"
    DAILY = "daily"
    WEEKLY = "weekly"


class DiscoveryFrequency(str, Enum):
    """Discovery run frequency options."""

    DAILY = "daily"
    WEEKLY = "weekly"


# =============================================================================
# Request Schemas
# =============================================================================


class SavedSearchCreate(BaseModel):
    """Schema for creating a saved search."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the saved search")
    description: str | None = Field(
        default=None, max_length=1000, description="Optional description"
    )
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search mode")
    filters: SearchFilters | None = Field(default=None, description="Search filters")
    is_public: bool = Field(
        default=False, description="Whether search is visible to all org members"
    )
    alert_enabled: bool = Field(
        default=False, description="Whether to receive alerts for new matches"
    )
    alert_frequency: AlertFrequency | None = Field(
        default=None, description="How often to send alerts"
    )
    # Discovery fields
    semantic_description: str | None = Field(
        default=None, max_length=5000, description="Semantic description for discovery matching"
    )
    target_project_id: UUID | None = Field(
        default=None, description="Project to auto-import papers into"
    )
    auto_import_enabled: bool = Field(
        default=False, description="Enable automated discovery and import"
    )
    import_sources: list[str] = Field(
        default_factory=list, description="Sources to scan: openalex, pubmed, arxiv"
    )
    max_import_per_run: int = Field(
        default=20, ge=1, le=200, description="Max papers to import per source per run"
    )
    discovery_frequency: DiscoveryFrequency | None = Field(
        default=None, description="How often to run discovery"
    )


class SavedSearchUpdate(BaseModel):
    """Schema for updating a saved search."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    query: str | None = Field(default=None, min_length=1, max_length=1000)
    mode: SearchMode | None = Field(default=None)
    filters: SearchFilters | None = Field(default=None)
    is_public: bool | None = Field(default=None)
    alert_enabled: bool | None = Field(default=None)
    alert_frequency: AlertFrequency | None = Field(default=None)
    # Discovery fields
    semantic_description: str | None = Field(default=None, max_length=5000)
    target_project_id: UUID | None = Field(default=None)
    auto_import_enabled: bool | None = Field(default=None)
    import_sources: list[str] | None = Field(default=None)
    max_import_per_run: int | None = Field(default=None, ge=1, le=200)
    discovery_frequency: DiscoveryFrequency | None = Field(default=None)


# =============================================================================
# Response Schemas
# =============================================================================


class SavedSearchCreator(BaseModel):
    """Brief creator info for saved search."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None = None


class SavedSearchResponse(BaseModel):
    """Response schema for a saved search."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    query: str
    mode: str
    filters: dict
    is_public: bool
    share_token: str | None
    share_url: str | None = None
    alert_enabled: bool
    alert_frequency: str | None
    last_alert_at: datetime | None
    # Discovery fields
    semantic_description: str | None = None
    target_project_id: UUID | None = None
    target_project_name: str | None = None
    auto_import_enabled: bool = False
    import_sources: list[str] = Field(default_factory=list)
    max_import_per_run: int = 20
    discovery_frequency: str | None = None
    last_discovery_at: datetime | None = None
    # Usage tracking
    run_count: int
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by: SavedSearchCreator | None = None


class SavedSearchListResponse(BaseModel):
    """Paginated list of saved searches."""

    items: list[SavedSearchResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ShareTokenResponse(BaseModel):
    """Response when generating a share token."""

    share_token: str
    share_url: str


class SavedSearchRunResponse(BaseModel):
    """Response when running a saved search."""

    saved_search_id: UUID
    run_count: int
    last_run_at: datetime
