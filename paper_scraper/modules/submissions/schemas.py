"""Pydantic schemas for research submissions module."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.submissions.models import (
    AttachmentType,
    SubmissionStatus,
)


# =============================================================================
# User Info (lightweight)
# =============================================================================


class SubmissionUserResponse(BaseModel):
    """User info for submission responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str | None
    email: str


# =============================================================================
# Attachment Schemas
# =============================================================================


class AttachmentResponse(BaseModel):
    """Attachment response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    file_size: int
    mime_type: str
    attachment_type: AttachmentType
    created_at: datetime


# =============================================================================
# Score Schemas
# =============================================================================


class SubmissionScoreResponse(BaseModel):
    """Submission score response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    novelty: float
    ip_potential: float
    marketability: float
    feasibility: float
    commercialization: float
    overall_score: float
    overall_confidence: float
    analysis_summary: str | None = None
    dimension_details: dict[str, Any] = Field(default_factory=dict)
    model_version: str
    created_at: datetime


# =============================================================================
# Submission Schemas
# =============================================================================


class SubmissionCreate(BaseModel):
    """Request to create a new submission."""

    title: str = Field(..., min_length=1, max_length=1000)
    abstract: str | None = Field(default=None, max_length=10000)
    research_field: str | None = Field(default=None, max_length=255)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    doi: str | None = Field(default=None, max_length=255)
    publication_venue: str | None = Field(default=None, max_length=500)
    commercial_potential: str | None = Field(default=None, max_length=5000)
    prior_art_notes: str | None = Field(default=None, max_length=5000)
    ip_disclosure: str | None = Field(default=None, max_length=5000)


class SubmissionUpdate(BaseModel):
    """Request to update a draft submission."""

    title: str | None = Field(default=None, min_length=1, max_length=1000)
    abstract: str | None = Field(default=None, max_length=10000)
    research_field: str | None = Field(default=None, max_length=255)
    keywords: list[str] | None = Field(default=None, max_length=20)
    doi: str | None = Field(default=None, max_length=255)
    publication_venue: str | None = Field(default=None, max_length=500)
    commercial_potential: str | None = Field(default=None, max_length=5000)
    prior_art_notes: str | None = Field(default=None, max_length=5000)
    ip_disclosure: str | None = Field(default=None, max_length=5000)


class SubmissionReview(BaseModel):
    """Request to review (approve/reject) a submission."""

    decision: Literal["approved", "rejected"]
    notes: str | None = Field(default=None, max_length=5000)


class SubmissionResponse(BaseModel):
    """Submission response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    title: str
    abstract: str | None = None
    research_field: str | None = None
    keywords: list[str] = Field(default_factory=list)
    status: SubmissionStatus
    doi: str | None = None
    publication_venue: str | None = None
    commercial_potential: str | None = None
    prior_art_notes: str | None = None
    ip_disclosure: str | None = None
    review_notes: str | None = None
    review_decision: str | None = None
    reviewed_at: datetime | None = None
    converted_paper_id: UUID | None = None
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    submitted_by: SubmissionUserResponse | None = None
    reviewed_by: SubmissionUserResponse | None = None


class SubmissionDetail(SubmissionResponse):
    """Detailed submission response with attachments and scores."""

    attachments: list[AttachmentResponse] = Field(default_factory=list)
    scores: list[SubmissionScoreResponse] = Field(default_factory=list)


class SubmissionListResponse(BaseModel):
    """Paginated submission list response."""

    items: list[SubmissionResponse]
    total: int
    page: int
    page_size: int
    pages: int
