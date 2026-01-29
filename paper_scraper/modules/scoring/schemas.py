"""Pydantic schemas for scoring module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Scoring Weight Schemas
# =============================================================================


class ScoringWeightsSchema(BaseModel):
    """Schema for scoring dimension weights."""

    novelty: float = Field(default=0.20, ge=0.0, le=1.0)
    ip_potential: float = Field(default=0.20, ge=0.0, le=1.0)
    marketability: float = Field(default=0.20, ge=0.0, le=1.0)
    feasibility: float = Field(default=0.20, ge=0.0, le=1.0)
    commercialization: float = Field(default=0.20, ge=0.0, le=1.0)

    @field_validator("commercialization")
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """Validate that all weights sum to 1.0."""
        data = info.data
        total = (
            data.get("novelty", 0.2)
            + data.get("ip_potential", 0.2)
            + data.get("marketability", 0.2)
            + data.get("feasibility", 0.2)
            + v
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


# =============================================================================
# Dimension Result Schemas
# =============================================================================


class DimensionResultSchema(BaseModel):
    """Schema for a single dimension's scoring result."""

    dimension: str
    score: float = Field(ge=0.0, le=10.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


# =============================================================================
# Paper Score Schemas
# =============================================================================


class ScoreRequest(BaseModel):
    """Request to score a paper."""

    dimensions: list[str] | None = Field(
        default=None,
        description="Specific dimensions to score. If None, all dimensions are scored.",
    )
    weights: ScoringWeightsSchema | None = Field(
        default=None,
        description="Custom weights for scoring. Uses default equal weights if not provided.",
    )
    force_rescore: bool = Field(
        default=False,
        description="Force rescoring even if recent score exists.",
    )


class BatchScoreRequest(BaseModel):
    """Request to score multiple papers."""

    paper_ids: list[UUID] = Field(
        ...,
        description="List of paper IDs to score.",
        min_length=1,
        max_length=100,
    )
    weights: ScoringWeightsSchema | None = None
    async_mode: bool = Field(
        default=True,
        description="If True, returns job ID for async processing.",
    )


class PaperScoreResponse(BaseModel):
    """Response schema for paper score."""

    id: UUID
    paper_id: UUID
    organization_id: UUID

    # Dimension scores
    novelty: float
    ip_potential: float
    marketability: float
    feasibility: float
    commercialization: float

    # Aggregate
    overall_score: float
    overall_confidence: float

    # Metadata
    model_version: str
    weights: dict[str, float]
    dimension_details: dict[str, Any]
    errors: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperScoreSummary(BaseModel):
    """Summary schema for paper scores (used in lists)."""

    paper_id: UUID
    overall_score: float
    novelty: float
    ip_potential: float
    marketability: float
    feasibility: float
    commercialization: float
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperScoreListResponse(BaseModel):
    """Paginated list of paper scores."""

    items: list[PaperScoreSummary]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Scoring Job Schemas
# =============================================================================


class ScoringJobResponse(BaseModel):
    """Response schema for scoring job status."""

    id: UUID
    job_type: str
    status: str
    total_papers: int
    completed_papers: int
    failed_papers: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ScoringJobListResponse(BaseModel):
    """Paginated list of scoring jobs."""

    items: list[ScoringJobResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Embedding Schemas
# =============================================================================


class GenerateEmbeddingRequest(BaseModel):
    """Request to generate embedding for a paper."""

    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if embedding exists.",
    )


class EmbeddingResponse(BaseModel):
    """Response for embedding generation."""

    paper_id: UUID
    has_embedding: bool
    embedding_dimensions: int | None = None
    message: str
