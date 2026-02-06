"""Pydantic schemas for developer API keys, webhooks, and repository sources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator

from paper_scraper.modules.developer.models import RepositoryProvider, WebhookEvent


# =============================================================================
# API Key Schemas
# =============================================================================


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    name: str = Field(..., min_length=1, max_length=255)
    permissions: list[str] = Field(
        default_factory=lambda: ["papers:read", "search:query"],
        description="List of permission strings",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiration date. Null for no expiration.",
    )


class APIKeyResponse(BaseModel):
    """Response schema for API key (without the full key)."""

    id: UUID
    name: str
    key_prefix: str
    permissions: list[str]
    expires_at: datetime | None
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime
    created_by_id: UUID | None

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(BaseModel):
    """Response schema when creating a new API key (includes full key ONCE)."""

    id: UUID
    name: str
    key: str = Field(..., description="Full API key - only shown once!")
    key_prefix: str
    permissions: list[str]
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyListResponse(BaseModel):
    """List of API keys."""

    items: list[APIKeyResponse]
    total: int


# =============================================================================
# Webhook Schemas
# =============================================================================


class WebhookCreate(BaseModel):
    """Schema for creating a new webhook."""

    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    events: list[WebhookEvent] = Field(
        ...,
        min_length=1,
        description="List of events to subscribe to",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Optional custom headers to include in webhook requests",
    )

    @field_validator("events", mode="before")
    @classmethod
    def validate_events(cls, v: list) -> list[WebhookEvent]:
        """Convert string event names to WebhookEvent enums."""
        return [WebhookEvent(e) if isinstance(e, str) else e for e in v]


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""

    name: str | None = Field(None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    events: list[WebhookEvent] | None = Field(
        None,
        min_length=1,
        description="List of events to subscribe to",
    )
    headers: dict[str, str] | None = None
    is_active: bool | None = None

    @field_validator("events", mode="before")
    @classmethod
    def validate_events(cls, v: list | None) -> list[WebhookEvent] | None:
        """Convert string event names to WebhookEvent enums."""
        if v is None:
            return None
        return [WebhookEvent(e) if isinstance(e, str) else e for e in v]


class WebhookResponse(BaseModel):
    """Response schema for webhook."""

    id: UUID
    name: str
    url: str
    events: list[str]
    headers: dict[str, str]
    is_active: bool
    last_triggered_at: datetime | None
    failure_count: int
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID | None

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """List of webhooks."""

    items: list[WebhookResponse]
    total: int


class WebhookTestResult(BaseModel):
    """Result of testing a webhook."""

    success: bool
    status_code: int | None = None
    response_time_ms: int | None = None
    error: str | None = None


# =============================================================================
# Repository Source Schemas
# =============================================================================


class RepositorySourceConfig(BaseModel):
    """Configuration for a repository source."""

    query: str | None = Field(None, description="Search query for the provider")
    filters: dict[str, str] = Field(
        default_factory=dict,
        description="Provider-specific filters",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum results per sync",
    )


class RepositorySourceCreate(BaseModel):
    """Schema for creating a new repository source."""

    name: str = Field(..., min_length=1, max_length=255)
    provider: RepositoryProvider
    config: RepositorySourceConfig = Field(default_factory=RepositorySourceConfig)
    schedule: str | None = Field(
        None,
        description="Cron expression for auto-sync (e.g., '0 6 * * *' for daily at 6 AM)",
    )


class RepositorySourceUpdate(BaseModel):
    """Schema for updating a repository source."""

    name: str | None = Field(None, min_length=1, max_length=255)
    config: RepositorySourceConfig | None = None
    schedule: str | None = None
    is_active: bool | None = None


class RepositorySourceResponse(BaseModel):
    """Response schema for repository source."""

    id: UUID
    name: str
    provider: str
    config: dict
    schedule: str | None
    is_active: bool
    last_sync_at: datetime | None
    last_sync_result: dict | None
    papers_synced: int
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID | None

    model_config = {"from_attributes": True}


class RepositorySourceListResponse(BaseModel):
    """List of repository sources."""

    items: list[RepositorySourceResponse]
    total: int


class RepositorySyncStatus(BaseModel):
    """Status of a repository sync operation."""

    source_id: UUID
    status: str = Field(
        ...,
        description="Status: 'pending', 'running', 'completed', 'failed'",
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    papers_found: int = 0
    papers_imported: int = 0
    error: str | None = None


class RepositorySyncTriggerResponse(BaseModel):
    """Response when triggering a manual sync."""

    message: str
    source_id: UUID
    job_id: str | None = None
