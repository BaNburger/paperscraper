"""Pydantic schemas for analytics module."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Time Series Data
# =============================================================================


class TimeSeriesDataPoint(BaseModel):
    """A single data point in a time series."""

    date: date
    count: int


class ScoreDistributionBucket(BaseModel):
    """Score distribution bucket."""

    range_start: float = Field(..., ge=0, le=10)
    range_end: float = Field(..., ge=0, le=10)
    count: int


# =============================================================================
# Team Analytics
# =============================================================================


class UserActivityStats(BaseModel):
    """User activity statistics."""

    user_id: UUID
    email: str
    full_name: str | None
    papers_imported: int
    papers_scored: int
    notes_created: int
    last_active: datetime | None


class TeamOverviewResponse(BaseModel):
    """Team overview statistics."""

    total_users: int
    active_users_last_7_days: int
    active_users_last_30_days: int
    total_papers: int
    total_scores: int
    total_projects: int
    user_activity: list[UserActivityStats] = Field(default_factory=list)


# =============================================================================
# Paper Analytics
# =============================================================================


class SourceDistribution(BaseModel):
    """Distribution of papers by source."""

    source: str
    count: int
    percentage: float


class PaperImportTrends(BaseModel):
    """Paper import trends over time."""

    daily: list[TimeSeriesDataPoint] = Field(default_factory=list)
    weekly: list[TimeSeriesDataPoint] = Field(default_factory=list)
    monthly: list[TimeSeriesDataPoint] = Field(default_factory=list)
    by_source: list[SourceDistribution] = Field(default_factory=list)


class ScoringStats(BaseModel):
    """Scoring statistics."""

    total_scored: int
    total_unscored: int
    average_overall_score: float | None
    average_novelty: float | None
    average_ip_potential: float | None
    average_marketability: float | None
    average_feasibility: float | None
    average_commercialization: float | None
    score_distribution: list[ScoreDistributionBucket] = Field(default_factory=list)


class TopPaperResponse(BaseModel):
    """Top paper response for analytics."""

    id: UUID
    title: str
    doi: str | None
    source: str
    overall_score: float | None
    created_at: datetime


class PaperAnalyticsResponse(BaseModel):
    """Complete paper analytics response."""

    import_trends: PaperImportTrends
    scoring_stats: ScoringStats
    top_papers: list[TopPaperResponse] = Field(default_factory=list)
    papers_with_embeddings: int
    papers_without_embeddings: int
    embedding_coverage_percent: float


# =============================================================================
# Dashboard Summary
# =============================================================================


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary combining key metrics."""

    # Paper metrics
    total_papers: int
    papers_this_week: int
    papers_this_month: int

    # Scoring metrics
    scored_papers: int
    average_score: float | None

    # Project metrics
    total_projects: int
    active_projects: int

    # Team metrics
    total_users: int
    active_users: int

    # Trends
    import_trend: list[TimeSeriesDataPoint] = Field(default_factory=list)
    scoring_trend: list[TimeSeriesDataPoint] = Field(default_factory=list)


# =============================================================================
# Innovation Funnel
# =============================================================================


class FunnelStage(BaseModel):
    """A stage in the innovation funnel."""

    stage: str
    label: str
    count: int
    percentage: float = Field(..., ge=0, le=100)


class FunnelResponse(BaseModel):
    """Innovation funnel analytics response."""

    stages: list[FunnelStage] = Field(default_factory=list)
    total_papers: int
    conversion_rates: dict[str, float] = Field(default_factory=dict)
    period_start: date | None = None
    period_end: date | None = None
    project_id: UUID | None = None


# =============================================================================
# Benchmarks
# =============================================================================


class BenchmarkMetric(BaseModel):
    """A single benchmark metric comparison."""

    metric: str
    label: str
    org_value: float
    benchmark_value: float
    unit: str = ""
    higher_is_better: bool = True


class BenchmarkResponse(BaseModel):
    """Benchmark comparison response."""

    metrics: list[BenchmarkMetric] = Field(default_factory=list)
    org_percentile: float | None = None
    benchmark_data_points: int = 0
