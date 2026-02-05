"""Scoring orchestrator for coordinating multi-dimensional paper scoring."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable
from uuid import UUID

from paper_scraper.modules.scoring.dimensions import (
    BaseDimension,
    CommercializationDimension,
    DimensionResult,
    FeasibilityDimension,
    IPPotentialDimension,
    MarketabilityDimension,
    NoveltyDimension,
    TeamReadinessDimension,
)
from paper_scraper.modules.scoring.dimensions.base import PaperContext
from paper_scraper.modules.scoring.llm_client import TokenUsage

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Weights for aggregating dimension scores."""

    novelty: float = 1.0 / 6
    ip_potential: float = 1.0 / 6
    marketability: float = 1.0 / 6
    feasibility: float = 1.0 / 6
    commercialization: float = 1.0 / 6
    team_readiness: float = 1.0 / 6

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.novelty
            + self.ip_potential
            + self.marketability
            + self.feasibility
            + self.commercialization
            + self.team_readiness
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
            "team_readiness": self.team_readiness,
        }


@dataclass
class ScoringUsage:
    """Aggregated token usage from scoring operation."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    dimension_usage: dict[str, TokenUsage] = field(default_factory=dict)

    def add_dimension_usage(self, dimension: str, usage: TokenUsage | None):
        """Add usage from a dimension scoring."""
        if usage:
            self.total_prompt_tokens += usage.prompt_tokens
            self.total_completion_tokens += usage.completion_tokens
            self.total_tokens += usage.total_tokens
            self.estimated_cost_usd += usage.estimated_cost_usd
            self.dimension_usage[dimension] = usage


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
    usage: ScoringUsage | None = None

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

    @property
    def team_readiness(self) -> float:
        """Get team readiness score."""
        return self.dimension_results.get("team_readiness", DimensionResult("team_readiness", 0, 0, "")).score


# Default concurrency limit for LLM calls (across all scoring dimensions)
DEFAULT_CONCURRENCY_LIMIT = 5


class ScoringOrchestrator:
    """
    Orchestrates multi-dimensional paper scoring.

    Runs all dimension scorers in parallel (with concurrency limits) and
    aggregates results using configurable weights.
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        model_version: str = "v1.0.0",
        max_concurrent_llm_calls: int = DEFAULT_CONCURRENCY_LIMIT,
    ):
        """
        Initialize the orchestrator.

        Args:
            weights: Scoring weights for each dimension
            model_version: Version identifier for scoring model
            max_concurrent_llm_calls: Maximum concurrent LLM calls (default: 5)
        """
        self.weights = weights or ScoringWeights()
        self.model_version = model_version
        self._semaphore = asyncio.Semaphore(max_concurrent_llm_calls)

        # Initialize all dimension scorers
        self.dimensions: dict[str, BaseDimension] = {
            "novelty": NoveltyDimension(),
            "ip_potential": IPPotentialDimension(),
            "marketability": MarketabilityDimension(),
            "feasibility": FeasibilityDimension(),
            "commercialization": CommercializationDimension(),
            "team_readiness": TeamReadinessDimension(),
        }

    async def score_paper(
        self,
        paper: PaperContext,
        similar_papers: list[PaperContext] | None = None,
        dimensions: list[str] | None = None,
        track_usage: bool = True,
    ) -> AggregatedScore:
        """
        Score a paper across all (or specified) dimensions.

        Args:
            paper: Paper context to score
            similar_papers: Optional list of similar papers for comparison
            dimensions: Optional list of specific dimensions to score
            track_usage: Whether to track token usage (default: True)

        Returns:
            AggregatedScore with all dimension results
        """
        # Determine which dimensions to score
        dims_to_score = dimensions or list(self.dimensions.keys())
        dims_to_score = [d for d in dims_to_score if d in self.dimensions]

        logger.info(f"Scoring paper {paper.id} on dimensions: {dims_to_score}")

        # Score all dimensions in parallel with concurrency limiting
        tasks = [
            self._score_dimension_with_semaphore(name, paper, similar_papers)
            for name in dims_to_score
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        dimension_results: dict[str, DimensionResult] = {}
        errors: list[str] = []
        usage = ScoringUsage() if track_usage else None

        for name, result in zip(dims_to_score, results):
            if isinstance(result, Exception):
                errors.append(f"{name}: {str(result)}")
                logger.error(f"Dimension {name} scoring failed for paper {paper.id}: {result}")
                # Use default score for failed dimensions
                dimension_results[name] = DimensionResult(
                    dimension=name,
                    score=5.0,  # Neutral score
                    confidence=0.0,  # Zero confidence
                    reasoning=f"Scoring failed: {str(result)}",
                )
            else:
                dimension_results[name] = result
                # Track usage if available in details
                if track_usage and usage and "usage" in result.details:
                    usage.add_dimension_usage(name, result.details["usage"])

        # Calculate weighted overall score
        overall_score, overall_confidence = self._calculate_overall(
            dimension_results, dims_to_score
        )

        if usage:
            logger.info(
                f"Paper {paper.id} scored: overall={overall_score:.2f}, "
                f"tokens={usage.total_tokens}, cost=${usage.estimated_cost_usd:.6f}"
            )

        return AggregatedScore(
            paper_id=paper.id,
            overall_score=overall_score,
            overall_confidence=overall_confidence,
            dimension_results=dimension_results,
            weights=self.weights,
            model_version=self.model_version,
            errors=errors,
            usage=usage,
        )

    async def _score_dimension_with_semaphore(
        self,
        dimension_name: str,
        paper: PaperContext,
        similar_papers: list[PaperContext] | None,
    ) -> DimensionResult:
        """Score a single dimension with concurrency control."""
        async with self._semaphore:
            logger.debug(f"Scoring dimension {dimension_name} for paper {paper.id}")
            return await self._score_dimension(dimension_name, paper, similar_papers)

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
            max_concurrent_llm_calls=self._semaphore._value,  # type: ignore
        )


# =============================================================================
# Batch Scoring with Rate Limiting
# =============================================================================


class BatchScoringOrchestrator:
    """
    Orchestrator for batch scoring multiple papers with rate limiting.

    Provides additional controls for batch operations:
    - Global concurrency limit across all papers
    - Progress tracking
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        model_version: str = "v1.0.0",
        max_concurrent_papers: int = 2,
        max_concurrent_llm_calls: int = 5,
    ):
        """
        Initialize batch orchestrator.

        Args:
            weights: Scoring weights
            model_version: Version identifier
            max_concurrent_papers: Max papers to score simultaneously
            max_concurrent_llm_calls: Max concurrent LLM calls per paper
        """
        self.orchestrator = ScoringOrchestrator(
            weights=weights,
            model_version=model_version,
            max_concurrent_llm_calls=max_concurrent_llm_calls,
        )
        self._paper_semaphore = asyncio.Semaphore(max_concurrent_papers)

    async def score_papers(
        self,
        papers: list[tuple[PaperContext, list[PaperContext] | None]],
        on_progress: Callable[[int, int, AggregatedScore], None] | None = None,
    ) -> list[AggregatedScore]:
        """
        Score multiple papers with rate limiting.

        Args:
            papers: List of (paper, similar_papers) tuples
            on_progress: Optional callback(completed, total, result)

        Returns:
            List of AggregatedScore results
        """
        total = len(papers)
        completed = 0

        async def score_with_semaphore(
            paper: PaperContext, similar: list[PaperContext] | None
        ) -> AggregatedScore:
            nonlocal completed
            async with self._paper_semaphore:
                result = await self.orchestrator.score_paper(paper, similar)
                completed += 1
                if on_progress:
                    on_progress(completed, total, result)
                return result

        tasks = [score_with_semaphore(paper, similar) for paper, similar in papers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed scores
        final_results: list[AggregatedScore] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                paper, _ = papers[i]
                logger.error(f"Batch scoring failed for paper {paper.id}: {result}")
                final_results.append(
                    AggregatedScore(
                        paper_id=paper.id,
                        overall_score=0.0,
                        overall_confidence=0.0,
                        dimension_results={},
                        weights=self.orchestrator.weights,
                        model_version=self.orchestrator.model_version,
                        errors=[str(result)],
                    )
                )
            else:
                final_results.append(result)

        return final_results
