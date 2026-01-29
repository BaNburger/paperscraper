"""Scoring orchestrator for coordinating multi-dimensional paper scoring."""

import asyncio
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from paper_scraper.modules.scoring.dimensions import (
    BaseDimension,
    CommercializationDimension,
    DimensionResult,
    FeasibilityDimension,
    IPPotentialDimension,
    MarketabilityDimension,
    NoveltyDimension,
)
from paper_scraper.modules.scoring.dimensions.base import PaperContext


@dataclass
class ScoringWeights:
    """Weights for aggregating dimension scores."""

    novelty: float = 0.20
    ip_potential: float = 0.20
    marketability: float = 0.20
    feasibility: float = 0.20
    commercialization: float = 0.20

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.novelty
            + self.ip_potential
            + self.marketability
            + self.feasibility
            + self.commercialization
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "novelty": self.novelty,
            "ip_potential": self.ip_potential,
            "marketability": self.marketability,
            "feasibility": self.feasibility,
            "commercialization": self.commercialization,
        }


@dataclass
class AggregatedScore:
    """Result of scoring a paper across all dimensions."""

    paper_id: UUID
    overall_score: float
    overall_confidence: float
    dimension_results: dict[str, DimensionResult]
    weights: ScoringWeights
    model_version: str
    errors: list[str] = field(default_factory=list)

    @property
    def novelty(self) -> float:
        """Get novelty score."""
        return self.dimension_results.get("novelty", DimensionResult("novelty", 0, 0, "")).score

    @property
    def ip_potential(self) -> float:
        """Get IP potential score."""
        return self.dimension_results.get("ip_potential", DimensionResult("ip_potential", 0, 0, "")).score

    @property
    def marketability(self) -> float:
        """Get marketability score."""
        return self.dimension_results.get("marketability", DimensionResult("marketability", 0, 0, "")).score

    @property
    def feasibility(self) -> float:
        """Get feasibility score."""
        return self.dimension_results.get("feasibility", DimensionResult("feasibility", 0, 0, "")).score

    @property
    def commercialization(self) -> float:
        """Get commercialization score."""
        return self.dimension_results.get("commercialization", DimensionResult("commercialization", 0, 0, "")).score


class ScoringOrchestrator:
    """
    Orchestrates multi-dimensional paper scoring.

    Runs all dimension scorers in parallel and aggregates results
    using configurable weights.
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        model_version: str = "v1.0.0",
    ):
        """
        Initialize the orchestrator.

        Args:
            weights: Scoring weights for each dimension
            model_version: Version identifier for scoring model
        """
        self.weights = weights or ScoringWeights()
        self.model_version = model_version

        # Initialize all dimension scorers
        self.dimensions: dict[str, BaseDimension] = {
            "novelty": NoveltyDimension(),
            "ip_potential": IPPotentialDimension(),
            "marketability": MarketabilityDimension(),
            "feasibility": FeasibilityDimension(),
            "commercialization": CommercializationDimension(),
        }

    async def score_paper(
        self,
        paper: PaperContext,
        similar_papers: list[PaperContext] | None = None,
        dimensions: list[str] | None = None,
    ) -> AggregatedScore:
        """
        Score a paper across all (or specified) dimensions.

        Args:
            paper: Paper context to score
            similar_papers: Optional list of similar papers for comparison
            dimensions: Optional list of specific dimensions to score

        Returns:
            AggregatedScore with all dimension results
        """
        # Determine which dimensions to score
        dims_to_score = dimensions or list(self.dimensions.keys())
        dims_to_score = [d for d in dims_to_score if d in self.dimensions]

        # Score all dimensions in parallel
        tasks = [
            self._score_dimension(name, paper, similar_papers)
            for name in dims_to_score
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        dimension_results: dict[str, DimensionResult] = {}
        errors: list[str] = []

        for name, result in zip(dims_to_score, results):
            if isinstance(result, Exception):
                errors.append(f"{name}: {str(result)}")
                # Use default score for failed dimensions
                dimension_results[name] = DimensionResult(
                    dimension=name,
                    score=5.0,  # Neutral score
                    confidence=0.0,  # Zero confidence
                    reasoning=f"Scoring failed: {str(result)}",
                )
            else:
                dimension_results[name] = result

        # Calculate weighted overall score
        overall_score, overall_confidence = self._calculate_overall(
            dimension_results, dims_to_score
        )

        return AggregatedScore(
            paper_id=paper.id,
            overall_score=overall_score,
            overall_confidence=overall_confidence,
            dimension_results=dimension_results,
            weights=self.weights,
            model_version=self.model_version,
            errors=errors,
        )

    async def _score_dimension(
        self,
        dimension_name: str,
        paper: PaperContext,
        similar_papers: list[PaperContext] | None,
    ) -> DimensionResult:
        """Score a single dimension."""
        dimension = self.dimensions[dimension_name]
        return await dimension.score(paper, similar_papers)

    def _calculate_overall(
        self,
        results: dict[str, DimensionResult],
        dimensions: list[str],
    ) -> tuple[float, float]:
        """
        Calculate weighted overall score and confidence.

        Args:
            results: Dimension results
            dimensions: Dimensions that were scored

        Returns:
            Tuple of (overall_score, overall_confidence)
        """
        weights_dict = self.weights.to_dict()

        # Calculate weighted sum
        weighted_score = 0.0
        weighted_confidence = 0.0
        total_weight = 0.0

        for dim in dimensions:
            if dim in results:
                weight = weights_dict.get(dim, 0.2)
                weighted_score += results[dim].score * weight
                weighted_confidence += results[dim].confidence * weight
                total_weight += weight

        # Normalize if not all dimensions were scored
        if total_weight > 0 and abs(total_weight - 1.0) > 0.001:
            weighted_score = weighted_score / total_weight
            weighted_confidence = weighted_confidence / total_weight

        return round(weighted_score, 2), round(weighted_confidence, 2)

    def with_weights(self, weights: ScoringWeights) -> "ScoringOrchestrator":
        """
        Create a new orchestrator with different weights.

        Args:
            weights: New scoring weights

        Returns:
            New orchestrator instance with specified weights
        """
        return ScoringOrchestrator(
            weights=weights,
            model_version=self.model_version,
        )
