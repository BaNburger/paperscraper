"""Base class for scoring dimensions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from paper_scraper.core.exceptions import ScoringError
from paper_scraper.modules.scoring.llm_client import BaseLLMClient, get_llm_client
from paper_scraper.modules.scoring.prompts import render_prompt


@dataclass
class DimensionResult:
    """Result from a dimension scoring operation."""

    dimension: str
    score: float
    confidence: float
    reasoning: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate score and confidence ranges."""
        if not 0 <= self.score <= 10:
            raise ValueError(f"Score must be between 0 and 10, got {self.score}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                f"Confidence must be between 0 and 1, got {self.confidence}"
            )


@dataclass
class PaperContext:
    """Context object containing paper data for scoring."""

    id: UUID
    title: str
    abstract: str | None = None
    keywords: list[str] = field(default_factory=list)
    journal: str | None = None
    publication_date: str | None = None
    doi: str | None = None
    citations_count: int | None = None
    references_count: int | None = None

    @classmethod
    def from_paper(cls, paper: Any) -> "PaperContext":
        """Create context from Paper model instance."""
        return cls(
            id=paper.id,
            title=paper.title,
            abstract=paper.abstract,
            keywords=paper.keywords or [],
            journal=paper.journal,
            publication_date=(
                paper.publication_date.isoformat() if paper.publication_date else None
            ),
            doi=paper.doi,
            citations_count=paper.citations_count,
            references_count=paper.references_count,
        )


class BaseDimension(ABC):
    """Abstract base class for scoring dimensions."""

    # Subclasses must define these
    dimension_name: str
    template_name: str
    system_prompt: str = "You are an expert scientific analyst."

    def __init__(self, llm_client: BaseLLMClient | None = None):
        """
        Initialize the dimension scorer.

        Args:
            llm_client: Optional LLM client (uses default if not provided)
        """
        self.llm_client = llm_client or get_llm_client()

    async def score(
        self,
        paper: PaperContext,
        similar_papers: list[PaperContext] | None = None,
    ) -> DimensionResult:
        """
        Score a paper on this dimension.

        Args:
            paper: Paper context to score
            similar_papers: Optional list of similar papers for comparison

        Returns:
            DimensionResult with score, confidence, and details

        Raises:
            ScoringError: If scoring fails
        """
        try:
            # Render the prompt template
            prompt = render_prompt(
                self.template_name,
                paper=paper,
                similar_papers=similar_papers or [],
            )

            # Get LLM response as JSON
            response = await self.llm_client.complete_json(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.3,
            )

            # Parse and validate response
            return self._parse_response(response)

        except Exception as e:
            raise ScoringError(
                paper_id=paper.id,
                dimension=self.dimension_name,
                reason=str(e),
                details={"error_type": type(e).__name__},
            )

    @abstractmethod
    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """
        Parse LLM response into DimensionResult.

        Args:
            response: Parsed JSON response from LLM

        Returns:
            DimensionResult with extracted data
        """
        pass

    def _safe_get(
        self, data: dict, key: str, default: Any = None, expected_type: type | None = None
    ) -> Any:
        """
        Safely get a value from a dict with optional type checking.

        Args:
            data: Dictionary to get value from
            key: Key to look up
            default: Default value if key not found
            expected_type: Optional type to validate against

        Returns:
            Value or default
        """
        value = data.get(key, default)
        if expected_type is not None and value is not None:
            if not isinstance(value, expected_type):
                try:
                    value = expected_type(value)
                except (ValueError, TypeError):
                    value = default
        return value

    def _extract_base_fields(self, response: dict[str, Any]) -> tuple[float, float, str]:
        """
        Extract and validate common scoring fields from LLM response.

        Args:
            response: Parsed JSON response from LLM

        Returns:
            Tuple of (score, confidence, reasoning) with values clamped to valid ranges
        """
        score = self._safe_get(response, "score", 5.0, float)
        confidence = self._safe_get(response, "confidence", 0.5, float)
        reasoning = self._safe_get(response, "reasoning", "No reasoning provided.", str)

        # Clamp values to valid ranges
        score = max(0.0, min(10.0, score))
        confidence = max(0.0, min(1.0, confidence))

        return score, confidence, reasoning
