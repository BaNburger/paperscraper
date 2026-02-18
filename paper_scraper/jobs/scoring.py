"""Background tasks for paper scoring."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.scoring.models import GlobalScoreCache
from paper_scraper.modules.scoring.schemas import ScoringWeightsSchema
from paper_scraper.modules.scoring.service import ScoringService


def _parse_weights(weights: dict[str, float] | None) -> ScoringWeightsSchema | None:
    """Convert weights dict to schema if provided."""
    return ScoringWeightsSchema(**weights) if weights else None


async def score_paper_task(
    ctx: dict[str, Any],
    paper_id: str,
    organization_id: str,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Score a single paper.

    Args:
        ctx: arq context.
        paper_id: UUID string of paper to score.
        organization_id: UUID string of organization.
        weights: Optional scoring weights dict.

    Returns:
        Scoring result dict with all dimension scores.
    """
    async with get_db_session() as db:
        service = ScoringService(db)
        score = await service.score_paper(
            paper_id=UUID(paper_id),
            organization_id=UUID(organization_id),
            weights=_parse_weights(weights),
            force_rescore=True,
        )

        return {
            "status": "completed",
            "paper_id": paper_id,
            "score_id": str(score.id),
            "overall_score": score.overall_score,
            "novelty": score.novelty,
            "ip_potential": score.ip_potential,
            "marketability": score.marketability,
            "feasibility": score.feasibility,
            "commercialization": score.commercialization,
        }


async def score_papers_batch_task(
    ctx: dict[str, Any],
    job_id: str,
    organization_id: str,
    paper_ids: list[str],
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Score multiple papers in batch.

    Args:
        ctx: arq context.
        job_id: UUID string of scoring job.
        organization_id: UUID string of organization.
        paper_ids: List of paper UUID strings.
        weights: Optional scoring weights dict.

    Returns:
        Batch scoring result dict with completion statistics.
    """
    job_uuid = UUID(job_id)
    org_uuid = UUID(organization_id)
    weights_schema = _parse_weights(weights)

    completed = 0
    failed = 0
    errors: list[str] = []

    async with get_db_session() as db:
        service = ScoringService(db)
        await service.update_job_status(job_uuid, "running")

        for paper_id_str in paper_ids:
            try:
                await service.score_paper(
                    paper_id=UUID(paper_id_str),
                    organization_id=org_uuid,
                    weights=weights_schema,
                    force_rescore=True,
                )
                completed += 1
                await service.update_job_status(
                    job_uuid,
                    "running",
                    completed_papers=completed,
                    failed_papers=failed,
                )
            except Exception as e:
                failed += 1
                errors.append(f"Paper {paper_id_str}: {e}")

        final_status = "completed" if failed == 0 else "completed_with_errors"
        await service.update_job_status(
            job_uuid,
            final_status,
            completed_papers=completed,
            failed_papers=failed,
            error_message="\n".join(errors) if errors else None,
        )

    return {
        "status": final_status,
        "job_id": job_id,
        "completed": completed,
        "failed": failed,
        "errors": errors,
    }


async def cleanup_expired_score_cache_task(
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """Remove expired entries from the global_score_cache table.

    Args:
        ctx: arq context.

    Returns:
        Result dict with count of deleted entries.
    """
    async with get_db_session() as db:
        result = await db.execute(
            delete(GlobalScoreCache).where(
                GlobalScoreCache.expires_at <= datetime.now(UTC)
            )
        )
        await db.commit()
        deleted = result.rowcount

    return {"status": "completed", "deleted_entries": deleted}
