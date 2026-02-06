"""Pydantic schemas for scheduled reports."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from paper_scraper.modules.reports.models import (
    ReportFormat,
    ReportSchedule,
    ReportType,
)


class ScheduledReportBase(BaseModel):
    """Base schema for scheduled reports."""

    name: str = Field(..., min_length=1, max_length=255)
    report_type: ReportType
    schedule: ReportSchedule
    recipients: list[EmailStr] = Field(default_factory=list, min_length=1)
    filters: dict = Field(default_factory=dict)
    format: ReportFormat = ReportFormat.PDF
    is_active: bool = True


class CreateScheduledReportRequest(ScheduledReportBase):
    """Schema for creating a scheduled report."""

    pass


class UpdateScheduledReportRequest(BaseModel):
    """Schema for updating a scheduled report."""

    name: str | None = Field(None, min_length=1, max_length=255)
    schedule: ReportSchedule | None = None
    recipients: list[EmailStr] | None = Field(None, min_length=1)
    filters: dict | None = None
    format: ReportFormat | None = None
    is_active: bool | None = None


class ScheduledReportResponse(BaseModel):
    """Schema for scheduled report response."""

    id: UUID
    organization_id: UUID
    name: str
    report_type: ReportType
    schedule: ReportSchedule
    recipients: list[str]
    filters: dict
    format: ReportFormat
    is_active: bool
    last_sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledReportListResponse(BaseModel):
    """Schema for listing scheduled reports."""

    items: list[ScheduledReportResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ReportRunResult(BaseModel):
    """Schema for report run result."""

    success: bool
    message: str
    report_id: UUID
    sent_to: list[str] = Field(default_factory=list)
