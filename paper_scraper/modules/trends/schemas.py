"""Pydantic schemas for trends module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Trend Topic Schemas
# =============================================================================


class TrendTopicCreate(BaseModel):
    """Schema for creating a trend topic."""

    name: str = Field(..., min_length=1, max_length=200, description="Topic name")
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Semantic description for paper matching",
    )
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color for UI")


class TrendTopicUpdate(BaseModel):
    """Schema for updating a trend topic."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=5000)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_active: bool | None = None


class TrendTopicResponse(BaseModel):
    """Response schema for a trend topic."""

    id: UUID
    organization_id: UUID
    created_by_id: UUID | None
    name: str
    description: str
    color: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed fields from latest snapshot
    matched_papers_count: int = 0
    avg_overall_score: float | None = None
    patent_count: int = 0
    last_analyzed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TrendTopicListResponse(BaseModel):
    """List of trend topics."""

    items: list[TrendTopicResponse]
    total: int


# =============================================================================
# Snapshot Schemas
# =============================================================================


class KeywordCount(BaseModel):
    """Keyword with occurrence count."""

    keyword: str
    count: int


class TimelineDataPoint(BaseModel):
    """Timeline data point."""

    date: str  # YYYY-MM format
    count: int


class PatentResult(BaseModel):
    """Patent search result."""

    patent_number: str
    title: str
    abstract: str | None = None
    applicant: str | None = None
    filing_date: str | None = None
    publication_date: str | None = None
    espacenet_url: str


class TrendSnapshotResponse(BaseModel):
    """Response schema for a trend snapshot."""

    id: UUID
    trend_topic_id: UUID

    # Aggregate metrics
    matched_papers_count: int
    avg_novelty: float | None = None
    avg_ip_potential: float | None = None
    avg_marketability: float | None = None
    avg_feasibility: float | None = None
    avg_commercialization: float | None = None
    avg_team_readiness: float | None = None
    avg_overall_score: float | None = None

    # Patents
    patent_count: int
    patent_results: list[PatentResult]

    # AI insights
    summary: str | None = None
    key_insights: list[str]
    top_keywords: list[KeywordCount]

    # Timeline
    timeline_data: list[TimelineDataPoint]

    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Matched Paper Schemas
# =============================================================================


class TrendPaperResponse(BaseModel):
    """Schema for a matched paper in a trend."""

    id: UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    journal: str | None = None
    publication_date: datetime | None = None
    relevance_score: float

    # Scoring data (if available)
    overall_score: float | None = None
    novelty: float | None = None
    ip_potential: float | None = None

    model_config = {"from_attributes": True}


class TrendPaperListResponse(BaseModel):
    """Paginated list of matched papers."""

    items: list[TrendPaperResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Dashboard Schema
# =============================================================================


class TrendDashboardResponse(BaseModel):
    """Complete dashboard data for a trend topic."""

    topic: TrendTopicResponse
    snapshot: TrendSnapshotResponse | None = None
    top_papers: list[TrendPaperResponse]
