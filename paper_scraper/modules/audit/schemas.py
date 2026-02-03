"""Pydantic schemas for audit logging module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from paper_scraper.modules.audit.models import AuditAction


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    organization_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: UUID | None
    details: dict
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditLogFilters(BaseModel):
    """Schema for filtering audit logs."""

    action: AuditAction | None = None
    user_id: UUID | None = None
    resource_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
