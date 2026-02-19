"""Pydantic schemas for authors module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.authors.models import ContactOutcome, ContactType

# =============================================================================
# Contact Schemas
# =============================================================================


class ContactBase(BaseModel):
    """Base schema for author contact."""

    contact_type: ContactType = Field(default=ContactType.EMAIL)
    contact_date: datetime | None = Field(default=None)
    subject: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    outcome: ContactOutcome | None = None
    follow_up_date: datetime | None = None
    paper_id: UUID | None = None


class ContactCreate(ContactBase):
    """Schema for creating a contact log."""


class ContactUpdate(BaseModel):
    """Schema for updating a contact log."""

    contact_type: ContactType | None = None
    contact_date: datetime | None = None
    subject: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    outcome: ContactOutcome | None = None
    follow_up_date: datetime | None = None


class ContactResponse(ContactBase):
    """Response schema for author contact."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    organization_id: UUID
    contacted_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ContactWithUserResponse(ContactResponse):
    """Contact response with user details."""

    contacted_by_name: str | None = None
    contacted_by_email: str | None = None


# =============================================================================
# Author Profile Schemas
# =============================================================================


class AuthorBase(BaseModel):
    """Base author schema."""

    name: str
    orcid: str | None = None
    openalex_id: str | None = None
    affiliations: list[str] = Field(default_factory=list)


class AuthorProfileResponse(AuthorBase):
    """Full author profile response with metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    h_index: int | None = None
    citation_count: int | None = None
    works_count: int | None = None
    created_at: datetime
    updated_at: datetime

    # Computed fields
    paper_count: int = 0
    recent_contacts_count: int = 0
    last_contact_date: datetime | None = None


class AuthorDetailResponse(AuthorProfileResponse):
    """Author profile with papers and contact history."""

    papers: list["AuthorPaperSummary"] = Field(default_factory=list)
    contacts: list[ContactWithUserResponse] = Field(default_factory=list)


class AuthorPaperSummary(BaseModel):
    """Summary of a paper for author profile view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    doi: str | None = None
    publication_date: datetime | None = None
    journal: str | None = None
    is_corresponding: bool = False


class AuthorListResponse(BaseModel):
    """Paginated list of authors."""

    items: list[AuthorProfileResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Enrichment Schemas
# =============================================================================


class EnrichmentRequest(BaseModel):
    """Request to enrich author data from external sources."""

    source: str = Field(
        default="openalex",
        description="Data source for enrichment (openalex, orcid, semantic_scholar)",
    )
    force_update: bool = Field(default=False, description="Update even if data already exists")


class EnrichmentResult(BaseModel):
    """Result of author enrichment."""

    author_id: UUID
    source: str
    updated_fields: list[str]
    success: bool
    message: str | None = None


# =============================================================================
# Contact Statistics
# =============================================================================


class AuthorContactStats(BaseModel):
    """Statistics about contacts for an author."""

    author_id: UUID
    total_contacts: int
    contacts_by_type: dict[str, int]
    contacts_by_outcome: dict[str, int]
    last_contact_date: datetime | None = None
    next_follow_up: datetime | None = None


# Resolve forward reference
AuthorDetailResponse.model_rebuild()
