"""Parallel scoring engine with job sharding for bulk paper scoring.

Replaces sequential scoring with semaphore-bounded parallel execution.
Each paper's 6 dimensions are scored concurrently, and papers are
processed in parallel up to the configured concurrency limit.

Throughput at 20 concurrent papers x 6 dims = 120 parallel LLM calls.
At ~2s/call (Nova Lite): ~60 papers/sec = ~5.2M papers/day.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.scoring.schemas import ScoringWeightsSchema
from paper_scraper.modules.scoring.service import ScoringService

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT_PAPERS = 20
DEFAULT_SHARD_SIZE = 5000


async def score_papers_parallel_task(
    ctx: dict[str, Any],
    job_id: str,
    organization_id: str,
    paper_ids: list[str],
    weights: dict[str, float] | None = None,
    max_concurrent_papers: int = DEFAULT_MAX_CONCURRENT_PAPERS,
) -> dict[str, Any]:
    """Score papers in parallel with semaphore-bounded concurrency.

    Args:
        ctx: arq context.
        job_id: ScoringJob UUID string.
        organization_id: Organization UUID string.
        paper_ids: List of paper UUID strings.
        weights: Optional scoring weights dict.
        max_concurrent_papers: Max papers to score concurrently.

    Returns:
        Scoring result dict with statistics.
    """
    job_uuid = UUID(job_id)
    org_uuid = UUID(organization_id)
    weights_schema = ScoringWeightsSchema(**weights) if weights else None

    # Load checkpoint (resume from last scored paper)
    checkpoint_idx = await _load_checkpoint(job_id)
    remaining_ids = paper_ids[checkpoint_idx:]

    logger.info(
        "Parallel scoring: %d papers (resuming from %d), concurrency=%d",
        len(remaining_ids),
        checkpoint_idx,
        max_concurrent_papers,
    )

    semaphore = asyncio.Semaphore(max_concurrent_papers)
    completed = checkpoint_idx
    failed = 0
    errors: list[str] = []

    async with get_db_session() as db:
        service = ScoringService(db)
        await service.update_job_status(job_uuid, "running")

    # Process in chunks for periodic checkpoint saves
    chunk_size = min(max_concurrent_papers * 5, 200)
    for chunk_start in range(0, len(remaining_ids), chunk_size):
        chunk = remaining_ids[chunk_start : chunk_start + chunk_size]

        async def _score_one(paper_id_str: str) -> tuple[bool, str | None]:
            async with semaphore:
                try:
                    async with get_db_session() as db:
                        svc = ScoringService(db)
                        await svc.score_paper(
                            paper_id=UUID(paper_id_str),
                            organization_id=org_uuid,
                            weights=weights_schema,
                            force_rescore=True,
                        )
                    return True, None
                except Exception as e:
                    return False, f"Paper {paper_id_str}: {e}"

        results = await asyncio.gather(
            *[_score_one(pid) for pid in chunk],
            return_exceptions=True,
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                errors.append(f"Paper {chunk[i]}: {result}")
            else:
                success, error_msg = result
                if success:
                    completed += 1
                else:
                    failed += 1
                    if error_msg:
                        errors.append(error_msg)

        # Update job progress and save checkpoint
        async with get_db_session() as db:
            service = ScoringService(db)
            await service.update_job_status(
                job_uuid,
                "running",
                completed_papers=completed,
                failed_papers=failed,
            )

        await _save_checkpoint(job_id, checkpoint_idx + chunk_start + len(chunk))

    # Finalize
    final_status = "completed" if failed == 0 else "completed_with_errors"
    async with get_db_session() as db:
        service = ScoringService(db)
        await service.update_job_status(
            job_uuid,
            final_status,
            completed_papers=completed,
            failed_papers=failed,
            error_message="\n".join(errors[:50]) if errors else None,
        )

    await _clear_checkpoint(job_id)

    logger.info(
        "Parallel scoring complete: %d completed, %d failed",
        completed,
        failed,
    )

    return {
        "status": final_status,
        "job_id": job_id,
        "completed": completed,
        "failed": failed,
        "errors": errors[:20],
    }


async def shard_scoring_job_task(
    ctx: dict[str, Any],
    job_id: str,
    organization_id: str,
    paper_ids: list[str],
    weights: dict[str, float] | None = None,
    shard_size: int = DEFAULT_SHARD_SIZE,
) -> dict[str, Any]:
    """Split a large scoring job into shards distributed across workers.

    Args:
        ctx: arq context.
        job_id: Parent ScoringJob UUID string.
        organization_id: Organization UUID string.
        paper_ids: Full list of paper UUID strings to score.
        weights: Optional scoring weights.
        shard_size: Papers per shard (sub-job).

    Returns:
        Dict with shard count and status.
    """
    from paper_scraper.jobs.worker import enqueue_job

    total = len(paper_ids)
    shard_count = 0

    for i in range(0, total, shard_size):
        shard = paper_ids[i : i + shard_size]
        shard_job_id = f"{job_id}:shard:{i // shard_size}"

        await enqueue_job(
            "score_papers_parallel_task",
            job_id,
            organization_id,
            shard,
            weights,
            _job_id=shard_job_id,
        )
        shard_count += 1

    logger.info(
        "Sharded scoring job %s into %d shards of %d papers each",
        job_id,
        shard_count,
        shard_size,
    )

    return {
        "status": "shards_enqueued",
        "job_id": job_id,
        "total_papers": total,
        "shard_count": shard_count,
        "shard_size": shard_size,
    }


async def _load_checkpoint(job_id: str) -> int:
    """Load the last processed paper index from Redis."""
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        data = await redis.get(f"bulk_score:checkpoint:{job_id}")
        if data:
            return int(data)
    except Exception as e:
        logger.warning("Failed to load scoring checkpoint: %s", e)
    return 0


async def _save_checkpoint(job_id: str, index: int) -> None:
    """Save the last processed paper index to Redis."""
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        await redis.set(f"bulk_score:checkpoint:{job_id}", str(index), ex=86400 * 7)
    except Exception as e:
        logger.warning("Failed to save scoring checkpoint: %s", e)


async def _clear_checkpoint(job_id: str) -> None:
    """Clear checkpoint on completion."""
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        await redis.delete(f"bulk_score:checkpoint:{job_id}")
    except Exception:
        pass
