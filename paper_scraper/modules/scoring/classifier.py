"""LLM-based paper classification service."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError, ScoringError
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.scoring.llm_client import get_llm_client
from paper_scraper.modules.scoring.prompts import jinja_env

logger = logging.getLogger(__name__)

# Paper type enumeration
PAPER_TYPES = [
    "ORIGINAL_RESEARCH",
    "REVIEW",
    "CASE_STUDY",
    "METHODOLOGY",
    "THEORETICAL",
    "COMMENTARY",
    "PREPRINT",
    "OTHER",
]


class PaperClassifier:
    """Service for classifying papers using LLM."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_client = get_llm_client()

    async def classify_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> dict[str, Any]:
        """
        Classify a paper into a category using LLM.

        Args:
            paper_id: ID of the paper to classify.
            organization_id: Organization ID for tenant isolation.

        Returns:
            Classification result with type, confidence, and reasoning.

        Raises:
            NotFoundError: If paper not found.
            ScoringError: If classification fails.
        """
        # Get paper
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        paper = result.scalar_one_or_none()

        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Build prompt
        template = jinja_env.get_template("paper_classification.jinja2")
        prompt = template.render(paper=paper)

        # Call LLM
        try:
            response = await self.llm_client.complete_json(
                prompt=prompt,
                temperature=0.2,  # Low temperature for classification
                max_tokens=500,
            )
        except Exception as e:
            logger.exception(f"Classification failed for paper {paper_id}: {e}")
            raise ScoringError(
                paper_id=paper_id,
                dimension="classification",
                reason=str(e),
            ) from e

        # Validate response
        paper_type = response.get("paper_type", "OTHER")
        if paper_type not in PAPER_TYPES:
            logger.warning(
                f"Unknown paper type '{paper_type}' from LLM, defaulting to OTHER"
            )
            paper_type = "OTHER"

        confidence = response.get("confidence", 0.5)
        if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
            confidence = 0.5

        # Update paper
        paper.paper_type = paper_type

        await self.db.commit()

        return {
            "paper_id": str(paper_id),
            "paper_type": paper_type,
            "confidence": confidence,
            "reasoning": response.get("reasoning", ""),
            "indicators": response.get("indicators", []),
        }

    async def classify_papers_batch(
        self,
        paper_ids: list[UUID],
        organization_id: UUID,
    ) -> dict[str, Any]:
        """
        Classify multiple papers.

        Args:
            paper_ids: List of paper IDs to classify.
            organization_id: Organization ID for tenant isolation.

        Returns:
            Batch classification results.
        """
        results = []
        errors = []

        for paper_id in paper_ids:
            try:
                result = await self.classify_paper(paper_id, organization_id)
                results.append(result)
            except Exception as e:
                logger.exception(f"Failed to classify paper {paper_id}: {e}")
                errors.append({
                    "paper_id": str(paper_id),
                    "error": str(e),
                })

        return {
            "total": len(paper_ids),
            "succeeded": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors[:10],  # Limit errors in response
        }

    async def get_unclassified_papers(
        self,
        organization_id: UUID,
        limit: int = 100,
    ) -> list[Paper]:
        """
        Get papers that haven't been classified yet.

        Args:
            organization_id: Organization ID for tenant isolation.
            limit: Maximum papers to return.

        Returns:
            List of unclassified papers.
        """
        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.paper_type.is_(None),
            )
            .order_by(Paper.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())
