"""Novelty dimension scorer."""

from typing import Any

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult


class NoveltyDimension(BaseDimension):
    """
    Scores the novelty/originality of research.

    Evaluates how different the research is from existing state-of-the-art,
    whether it introduces new concepts or methods, and its potential for
    paradigm-shifting impact.
    """

    dimension_name = "novelty"
    template_name = "novelty.jinja2"
    system_prompt = (
        "You are an expert scientific reviewer with deep knowledge across multiple "
        "research domains. You specialize in identifying truly novel research that "
        "advances the state-of-the-art versus incremental improvements."
    )

    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """Parse novelty-specific response fields."""
        score, confidence, reasoning = self._extract_base_fields(response)

        details = {
            "key_factors": self._safe_get(response, "key_factors", [], list),
            "comparison_to_sota": self._safe_get(response, "comparison_to_sota", "", str),
        }

        return DimensionResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            details=details,
        )
