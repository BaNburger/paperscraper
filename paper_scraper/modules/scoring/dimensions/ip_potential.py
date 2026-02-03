"""IP Potential dimension scorer."""

from typing import Any

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult


class IPPotentialDimension(BaseDimension):
    """
    Scores the intellectual property potential of research.

    Evaluates patentability based on novelty, non-obviousness, utility,
    and enablement criteria. Also assesses prior art risk and potential
    claim scope.
    """

    dimension_name = "ip_potential"
    template_name = "ip_potential.jinja2"
    system_prompt = (
        "You are an expert intellectual property analyst with experience in patent "
        "law and technology transfer. You specialize in assessing the patentability "
        "of scientific innovations and identifying white space opportunities."
    )

    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """Parse IP potential-specific response fields."""
        score, confidence, reasoning = self._extract_base_fields(response)

        patentability_factors = self._safe_get(response, "patentability_factors", {}, dict)

        details = {
            "patentability_factors": {
                "novelty": self._safe_get(patentability_factors, "novelty", 5.0, float),
                "non_obviousness": self._safe_get(patentability_factors, "non_obviousness", 5.0, float),
                "utility": self._safe_get(patentability_factors, "utility", 5.0, float),
                "enablement": self._safe_get(patentability_factors, "enablement", 5.0, float),
            },
            "prior_art_risk": self._safe_get(response, "prior_art_risk", "medium", str),
            "suggested_claim_scope": self._safe_get(response, "suggested_claim_scope", "uncertain", str),
        }

        return DimensionResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            details=details,
        )
