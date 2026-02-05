"""Team Readiness dimension scorer."""

from typing import Any

from paper_scraper.modules.scoring.dimensions.base import BaseDimension, DimensionResult


class TeamReadinessDimension(BaseDimension):
    """
    Scores the team's readiness for commercialization.

    Evaluates the research team's track record, industry connections,
    institutional support, team composition, and prior commercialization
    experience to determine how prepared they are for technology transfer.
    """

    dimension_name = "team_readiness"
    template_name = "team_readiness.jinja2"
    system_prompt = (
        "You are an expert in evaluating research teams for technology transfer "
        "and commercialization readiness. You assess team composition, track records, "
        "industry connections, and institutional support to determine commercialization potential."
    )

    def _parse_response(self, response: dict[str, Any]) -> DimensionResult:
        """Parse team readiness-specific response fields."""
        score, confidence, reasoning = self._extract_base_fields(response)

        details = {
            "evidence": self._safe_get(response, "evidence", [], list),
            "strengths": self._safe_get(response, "strengths", [], list),
            "gaps": self._safe_get(response, "gaps", [], list),
        }

        return DimensionResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            details=details,
        )
