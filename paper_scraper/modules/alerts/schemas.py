"""Pydantic schemas for alerts module."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertFrequency(str, Enum):
    """Alert frequency options."""

    IMMEDIATELY = "immediately"
    DAILY = "daily"
    WEEKLY = "weekly"


class AlertChannel(str, Enum):
    """Alert channel options."""

    EMAIL = "email"
    IN_APP = "in_app"


class AlertStatus(str, Enum):
    """Alert result status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


# =============================================================================
# Request Schemas
# =============================================================================


class AlertCreate(BaseModel):
    """Schema for creating an alert."""

    name: str = Field(..., min_length=1, max_length=255, description="Alert name")
    description: str | None = Field(default=None, max_length=1000)
    saved_search_id: UUID = Field(..., description="Saved search to monitor")
    channel: AlertChannel = Field(default=AlertChannel.EMAIL)
    frequency: AlertFrequency = Field(default=AlertFrequency.DAILY)
    min_results: int = Field(
        default=1, ge=1, le=100, description="Minimum new results to trigger alert"
    )


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    channel: AlertChannel | None = Field(default=None)
    frequency: AlertFrequency | None = Field(default=None)
    min_results: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = Field(default=None)


# =============================================================================
# Response Schemas
# =============================================================================


class SavedSearchBrief(BaseModel):
    """Brief saved search info for alert response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    query: str


class AlertResponse(BaseModel):
    """Response schema for an alert."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    channel: str
    frequency: str
    min_results: int
    is_active: bool
    last_triggered_at: datetime | None
    trigger_count: int
    saved_search: SavedSearchBrief | None
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AlertResultResponse(BaseModel):
    """Response schema for an alert result."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    status: str
    papers_found: int
    new_papers: int
    paper_ids: list[str]
    delivered_at: datetime | None
    error_message: str | None
    created_at: datetime


class AlertResultListResponse(BaseModel):
    """Paginated list of alert results."""

    items: list[AlertResultResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AlertTestResponse(BaseModel):
    """Response for testing an alert."""

    success: bool
    message: str
    papers_found: int
    sample_papers: list[dict]
