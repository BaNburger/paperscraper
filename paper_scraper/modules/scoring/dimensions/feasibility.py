"""Feasibility dimension scorer."""

from typing import Any

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult


class FeasibilityDimension(BaseDimension):
    """
    Scores the technical feasibility of commercializing research.

    Evaluates Technology Readiness Level (TRL), time to market,
    development costs, technical risks, and scalability.
    """

    dimension_name = "feasibility"
    template_name = "feasibility.jinja2"
    system_prompt = (
        "You are an expert technology assessment specialist with experience in "
        "R&D management and product development. You specialize in evaluating "
        "the technical readiness and feasibility of bringing research to market."
    )

    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """Parse feasibility-specific response fields."""
        score, confidence, reasoning = self._extract_base_fields(response)

        details = {
            "estimated_trl": self._safe_get(response, "estimated_trl", 5, int),
            "time_to_market_years": self._safe_get(response, "time_to_market_years", "2-5", str),
            "development_cost_estimate": self._safe_get(
                response, "development_cost_estimate", "medium", str
            ),
            "key_technical_risks": self._safe_get(response, "key_technical_risks", [], list),
            "required_capabilities": self._safe_get(response, "required_capabilities", [], list),
            "scalability_assessment": self._safe_get(
                response, "scalability_assessment", "moderate", str
            ),
        }

        return DimensionResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            details=details,
        )
