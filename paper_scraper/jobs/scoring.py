"""Background tasks for paper scoring."""

from typing import Any
from uuid import UUID

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.scoring.schemas import ScoringWeightsSchema
from paper_scraper.modules.scoring.service import ScoringService


async def score_paper_task(
    ctx: dict[str, Any],
    paper_id: str,
    organization_id: str,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    arq task: Score a single paper.

    Args:
        ctx: arq context
        paper_id: UUID string of paper to score
        organization_id: UUID string of organization
        weights: Optional scoring weights dict

    Returns:
        Scoring result dict
    """
    paper_uuid = UUID(paper_id)
    org_uuid = UUID(organization_id)

    weights_schema = ScoringWeightsSchema(**weights) if weights else None

    async with get_db_session() as db:
        service = ScoringService(db)
        score = await service.score_paper(
            paper_id=paper_uuid,
            organization_id=org_uuid,
            weights=weights_schema,
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
    """
    arq task: Score multiple papers in batch.

    Args:
        ctx: arq context
        job_id: UUID string of scoring job
        organization_id: UUID string of organization
        paper_ids: List of paper UUID strings
        weights: Optional scoring weights dict

    Returns:
        Batch scoring result dict
    """
    job_uuid = UUID(job_id)
    org_uuid = UUID(organization_id)

    weights_schema = ScoringWeightsSchema(**weights) if weights else None

    completed = 0
    failed = 0
    errors: list[str] = []

    async with get_db_session() as db:
        service = ScoringService(db)

        # Update job to running
        await service.update_job_status(job_uuid, "running")

        for paper_id_str in paper_ids:
            try:
                paper_uuid = UUID(paper_id_str)
                await service.score_paper(
                    paper_id=paper_uuid,
                    organization_id=org_uuid,
                    weights=weights_schema,
                    force_rescore=True,
                )
                completed += 1

                # Update progress
                await service.update_job_status(
                    job_uuid,
                    "running",
                    completed_papers=completed,
                    failed_papers=failed,
                )

            except Exception as e:
                failed += 1
                errors.append(f"Paper {paper_id_str}: {str(e)}")

        # Mark job as completed
        final_status = "completed" if failed == 0 else "completed"
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


async def generate_embeddings_batch_task(
    ctx: dict[str, Any],
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    """
    arq task: Generate embeddings for papers without them.

    Args:
        ctx: arq context
        organization_id: UUID string of organization
        limit: Maximum papers to process

    Returns:
        Result dict with count of embeddings generated
    """
    org_uuid = UUID(organization_id)

    async with get_db_session() as db:
        service = ScoringService(db)
        count = await service.batch_generate_embeddings(
            organization_id=org_uuid,
            limit=limit,
        )

    return {
        "status": "completed",
        "embeddings_generated": count,
    }
