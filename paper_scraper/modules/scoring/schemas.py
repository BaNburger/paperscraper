"""Pydantic schemas for scoring module."""

from datetime import datetime
from typing import Any, Literal
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


class ScoreEvidence(BaseModel):
    """Evidence supporting a score."""

    factor: str = Field(..., description="The factor being evaluated")
    description: str = Field(..., description="Description of how this factor affects the score")
    impact: Literal["positive", "negative", "neutral"] = Field(
        ..., description="Whether this factor positively or negatively impacts the score"
    )
    source: str | None = Field(
        default=None, description="Quote or reference from the paper supporting this evidence"
    )


class DimensionScoreDetail(BaseModel):
    """Detailed breakdown of a dimension score."""

    score: float = Field(ge=0.0, le=10.0)
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(..., description="Brief summary of the score rationale")
    key_factors: list[str] = Field(
        default_factory=list, description="Key factors that influenced the score"
    )
    evidence: list[ScoreEvidence] = Field(
        default_factory=list, description="Evidence supporting the score"
    )
    comparison_to_field: str | None = Field(
        default=None, description="How this paper compares to similar work in the field"
    )


class EnhancedPaperScoreResponse(BaseModel):
    """Enhanced score response with detailed evidence and breakdowns."""

    id: UUID
    paper_id: UUID
    overall_score: float = Field(ge=0.0, le=10.0)

    # Dimension scores with details
    novelty: DimensionScoreDetail
    ip_potential: DimensionScoreDetail
    marketability: DimensionScoreDetail
    feasibility: DimensionScoreDetail
    commercialization: DimensionScoreDetail

    model_version: str
    created_at: datetime

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


# =============================================================================
# Classification Schemas
# =============================================================================


class ClassificationResponse(BaseModel):
    """Response for paper classification."""

    paper_id: str
    paper_type: str = Field(
        ...,
        description="Classification category: ORIGINAL_RESEARCH, REVIEW, CASE_STUDY, METHODOLOGY, THEORETICAL, COMMENTARY, PREPRINT, OTHER",
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    indicators: list[str] = Field(default_factory=list)


# =============================================================================
# LLM Response Validation Helpers
# =============================================================================


def _coerce_to_string_list(value: Any) -> list[str]:
    """Convert a value to a list of non-empty strings.

    Used by validators to normalize LLM responses into string lists.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


# =============================================================================
# LLM Response Validation Schemas
# =============================================================================


class BaseLLMScoringResponse(BaseModel):
    """Base schema for all dimension scoring LLM responses."""

    score: float = Field(ge=0.0, le=10.0, description="Score from 0-10")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level 0-1")
    reasoning: str = Field(min_length=1, description="Explanation of the score")

    @field_validator("score", mode="before")
    @classmethod
    def clamp_score(cls, v: Any) -> float:
        """Ensure score is within valid range."""
        if isinstance(v, (int, float)):
            return max(0.0, min(10.0, float(v)))
        return 5.0  # Default fallback

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        """Ensure confidence is within valid range."""
        if isinstance(v, (int, float)):
            return max(0.0, min(1.0, float(v)))
        return 0.5  # Default fallback

    @field_validator("reasoning", mode="before")
    @classmethod
    def ensure_reasoning(cls, v: Any) -> str:
        """Ensure reasoning is a non-empty string."""
        if not v or not isinstance(v, str):
            return "No reasoning provided."
        return v


class NoveltyLLMResponse(BaseLLMScoringResponse):
    """Schema for novelty dimension LLM response."""

    key_factors: list[str] = Field(default_factory=list, description="Key novelty factors")
    comparison_to_sota: str = Field(default="", description="Comparison to state-of-the-art")

    @field_validator("key_factors", mode="before")
    @classmethod
    def validate_key_factors(cls, v: Any) -> list[str]:
        """Ensure key_factors is a list."""
        return _coerce_to_string_list(v)


class IPPotentialLLMResponse(BaseLLMScoringResponse):
    """Schema for IP potential dimension LLM response."""

    patentability_factors: list[str] = Field(
        default_factory=list, description="Factors affecting patentability"
    )
    prior_art_concerns: str = Field(default="", description="Prior art analysis")
    white_space_opportunities: str = Field(
        default="", description="Identified white space opportunities"
    )

    @field_validator("patentability_factors", mode="before")
    @classmethod
    def validate_patentability_factors(cls, v: Any) -> list[str]:
        return _coerce_to_string_list(v)


class MarketabilityLLMResponse(BaseLLMScoringResponse):
    """Schema for marketability dimension LLM response."""

    target_industries: list[str] = Field(
        default_factory=list, description="Target industries"
    )
    market_size_estimate: str = Field(default="", description="Market size estimate")
    competitive_landscape: str = Field(default="", description="Competitive landscape analysis")

    @field_validator("target_industries", mode="before")
    @classmethod
    def validate_target_industries(cls, v: Any) -> list[str]:
        return _coerce_to_string_list(v)


class FeasibilityLLMResponse(BaseLLMScoringResponse):
    """Schema for feasibility dimension LLM response."""

    trl_level: int | None = Field(
        default=None, ge=1, le=9, description="Technology Readiness Level"
    )
    development_challenges: list[str] = Field(
        default_factory=list, description="Key development challenges"
    )
    resource_requirements: str = Field(default="", description="Resource requirements")
    time_to_market_estimate: str = Field(default="", description="Time to market estimate")

    @field_validator("trl_level", mode="before")
    @classmethod
    def validate_trl_level(cls, v: Any) -> int | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return max(1, min(9, int(v)))
        return None

    @field_validator("development_challenges", mode="before")
    @classmethod
    def validate_development_challenges(cls, v: Any) -> list[str]:
        return _coerce_to_string_list(v)


class CommercializationLLMResponse(BaseLLMScoringResponse):
    """Schema for commercialization dimension LLM response."""

    recommended_path: str = Field(default="", description="Recommended commercialization path")
    entry_barriers: list[str] = Field(default_factory=list, description="Entry barriers")
    partnership_opportunities: list[str] = Field(
        default_factory=list, description="Potential partnership opportunities"
    )
    risk_factors: list[str] = Field(default_factory=list, description="Key risk factors")

    @field_validator("entry_barriers", "partnership_opportunities", "risk_factors", mode="before")
    @classmethod
    def validate_list_fields(cls, v: Any) -> list[str]:
        return _coerce_to_string_list(v)


class ClassificationLLMResponse(BaseModel):
    """Schema for paper classification LLM response."""

    paper_type: str = Field(description="Classified paper type")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")
    reasoning: str = Field(description="Explanation of classification")
    indicators: list[str] = Field(default_factory=list, description="Supporting indicators")

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return max(0.0, min(1.0, float(v)))
        return 0.5

    @field_validator("indicators", mode="before")
    @classmethod
    def validate_indicators(cls, v: Any) -> list[str]:
        return _coerce_to_string_list(v)


class PitchLLMResponse(BaseModel):
    """Schema for one-line pitch LLM response."""

    pitch: str = Field(max_length=150, description="One-line pitch (max 15 words)")

    @field_validator("pitch", mode="before")
    @classmethod
    def clean_pitch(cls, v: Any) -> str:
        """Clean up pitch formatting."""
        if not isinstance(v, str):
            return ""
        # Remove quotes and common artifacts
        pitch = v.strip().strip('"\'')
        if pitch.startswith("- "):
            pitch = pitch[2:]
        return pitch[:150]  # Hard limit


class SimplifiedAbstractLLMResponse(BaseModel):
    """Schema for simplified abstract LLM response."""

    abstract: str = Field(max_length=1000, description="Simplified abstract (max 150 words)")

    @field_validator("abstract", mode="before")
    @classmethod
    def clean_abstract(cls, v: Any) -> str:
        """Clean up abstract formatting."""
        if not isinstance(v, str):
            return ""
        return v.strip()[:1000]


# =============================================================================
# LLM Response Schema Registry
# =============================================================================

LLM_DIMENSION_SCHEMAS: dict[str, type[BaseLLMScoringResponse]] = {
    "novelty": NoveltyLLMResponse,
    "ip_potential": IPPotentialLLMResponse,
    "marketability": MarketabilityLLMResponse,
    "feasibility": FeasibilityLLMResponse,
    "commercialization": CommercializationLLMResponse,
}


def get_llm_dimension_schema(dimension: str) -> type[BaseLLMScoringResponse]:
    """Get the Pydantic schema for validating a dimension's LLM response."""
    return LLM_DIMENSION_SCHEMAS.get(dimension, BaseLLMScoringResponse)


def validate_llm_dimension_response(
    dimension: str, response: dict[str, Any]
) -> BaseLLMScoringResponse:
    """
    Validate and parse a dimension's LLM response using the appropriate schema.

    Args:
        dimension: Dimension name
        response: Raw response dict from LLM

    Returns:
        Validated response object

    Raises:
        ValidationError: If response doesn't match schema
    """
    schema = get_llm_dimension_schema(dimension)
    return schema.model_validate(response)
