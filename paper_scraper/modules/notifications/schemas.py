"""Pydantic schemas for notifications module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Response Schemas
# =============================================================================


class NotificationResponse(BaseModel):
    """Response schema for a single notification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    message: str | None
    is_read: bool
    resource_type: str | None
    resource_id: str | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with unread count."""

    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int
    unread_count: int  # Total unread for badge count (always global, not filtered)


# =============================================================================
# Request Schemas
# =============================================================================


class MarkReadRequest(BaseModel):
    """Request schema for marking specific notifications as read."""

    notification_ids: list[UUID] = Field(
        ..., min_length=1, max_length=100, description="IDs of notifications to mark as read"
    )
