"""Marketability dimension scorer."""

from typing import Any

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult


class MarketabilityDimension(BaseDimension):
    """
    Scores the market potential of research.

    Evaluates addressable market size, industry relevance, market timing,
    competitive landscape, and alignment with market trends.
    """

    dimension_name = "marketability"
    template_name = "marketability.jinja2"
    system_prompt = (
        "You are an expert market analyst with experience in technology markets "
        "and venture capital. You specialize in identifying commercial potential "
        "of emerging technologies and assessing market readiness."
    )

    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """Parse marketability-specific response fields."""
        score, confidence, reasoning = self._extract_base_fields(response)

        details = {
            "target_industries": self._safe_get(response, "target_industries", [], list),
            "market_size_estimate": self._safe_get(response, "market_size_estimate", "medium", str),
            "market_timing": self._safe_get(response, "market_timing", "good", str),
            "competitive_landscape": self._safe_get(
                response, "competitive_landscape", "emerging", str
            ),
            "key_trends_alignment": self._safe_get(response, "key_trends_alignment", [], list),
        }

        return DimensionResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            details=details,
        )
