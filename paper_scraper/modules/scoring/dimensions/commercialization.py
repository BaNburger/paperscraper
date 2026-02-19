"""Commercialization dimension scorer."""

from typing import Any

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult


class CommercializationDimension(BaseDimension):
    """
    Scores the commercialization potential and strategy of research.

    Evaluates recommended commercialization path, entry barriers,
    revenue model viability, and strategic value.
    """

    dimension_name = "commercialization"
    template_name = "commercialization.jinja2"
    system_prompt = (
        "You are an expert commercialization strategist with experience advising "
        "technology transfer offices, startups, and corporate innovation teams. "
        "You specialize in identifying optimal paths to market for research innovations."
    )

    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """Parse commercialization-specific response fields."""
        score, confidence, reasoning = self._extract_base_fields(response)

        entry_barriers = self._safe_get(response, "entry_barriers", {}, dict)

        details = {
            "recommended_path": self._safe_get(response, "recommended_path", "licensing", str),
            "alternative_paths": self._safe_get(response, "alternative_paths", [], list),
            "entry_barriers": {
                "regulatory": self._safe_get(entry_barriers, "regulatory", "medium", str),
                "capital": self._safe_get(entry_barriers, "capital", "medium", str),
                "market_access": self._safe_get(entry_barriers, "market_access", "medium", str),
                "competition": self._safe_get(entry_barriers, "competition", "medium", str),
            },
            "revenue_model_suggestions": self._safe_get(
                response, "revenue_model_suggestions", [], list
            ),
            "strategic_value": self._safe_get(response, "strategic_value", "incremental", str),
            "key_success_factors": self._safe_get(response, "key_success_factors", [], list),
        }

        return DimensionResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            details=details,
        )
