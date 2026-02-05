"""arq worker configuration and job definitions."""

from typing import Any
from urllib.parse import urlparse

import arq
from arq.connections import ArqRedis, RedisSettings

from paper_scraper.core.config import settings
from paper_scraper.jobs.alerts import (
    process_daily_alerts_task,
    process_immediate_alert_task,
    process_weekly_alerts_task,
)
from paper_scraper.jobs.badges import (
    batch_check_badges_task,
    check_and_award_badges_task,
)
from paper_scraper.jobs.ingestion import ingest_openalex_task
from paper_scraper.jobs.scoring import (
    generate_embeddings_batch_task,
    score_paper_task,
    score_papers_batch_task,
)
from paper_scraper.jobs.search import backfill_embeddings_task


async def startup(ctx: dict[str, Any]) -> None:
    """Initialize shared resources when worker starts."""


async def shutdown(ctx: dict[str, Any]) -> None:
    """Cleanup shared resources when worker shuts down."""


async def ingest_papers_task(
    ctx: dict[str, Any],
    source: str,
    query: str,
    max_results: int = 100,
) -> dict[str, Any]:
    """Ingest papers from an external source (placeholder).

    Note: This is a placeholder for future implementations of PubMed,
    arXiv, and Crossref ingestion. Use ingest_openalex_task for OpenAlex.

    Args:
        ctx: Worker context.
        source: Source to ingest from ('pubmed', 'arxiv', 'crossref').
        query: Search query for the source.
        max_results: Maximum number of papers to ingest.

    Returns:
        Dict with ingestion results.
    """
    return {
        "status": "not_implemented",
        "source": source,
        "papers_ingested": 0,
        "message": f"Ingestion from {source} is not yet implemented",
    }


def get_redis_settings() -> RedisSettings:
    """Parse Redis URL and return arq RedisSettings."""
    parsed = urlparse(settings.REDIS_URL)

    db = 0
    if parsed.path and parsed.path != "/":
        db = int(parsed.path.lstrip("/"))

    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=db,
    )


class WorkerSettings:
    """arq worker settings configuration.

    This class is used by the arq CLI to configure the worker:
        arq paper_scraper.jobs.WorkerSettings
    """

    # Job functions available to this worker
    functions = [
        score_paper_task,
        score_papers_batch_task,
        ingest_papers_task,
        ingest_openalex_task,
        generate_embeddings_batch_task,
        backfill_embeddings_task,
        process_daily_alerts_task,
        process_weekly_alerts_task,
        process_immediate_alert_task,
        check_and_award_badges_task,
        batch_check_badges_task,
    ]

    # Cron jobs for scheduled tasks
    cron_jobs = [
        # Daily alerts at 6:00 AM UTC
        arq.cron(process_daily_alerts_task, hour=6, minute=0),
        # Weekly alerts on Monday at 6:00 AM UTC
        arq.cron(process_weekly_alerts_task, weekday=0, hour=6, minute=0),
    ]

    # Redis connection settings
    redis_settings = get_redis_settings()

    # Startup/shutdown handlers
    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = 10
    job_timeout = 600  # 10 minutes
    keep_result = 3600  # Keep results for 1 hour
    poll_delay = 0.5  # Poll every 500ms
    queue_name = "paperscraper:queue"


async def get_redis_pool() -> ArqRedis:
    """Get a Redis connection pool for enqueuing jobs.

    Returns:
        ArqRedis connection pool.
    """
    return await arq.create_pool(get_redis_settings())


async def enqueue_job(
    job_name: str,
    *args: Any,
    **kwargs: Any,
) -> arq.jobs.Job:
    """Enqueue a job for background processing.

    Args:
        job_name: Name of the job function to run.
        *args: Positional arguments for the job.
        **kwargs: Keyword arguments for the job.

    Returns:
        The enqueued Job object.
    """
    pool = await get_redis_pool()
    try:
        return await pool.enqueue_job(job_name, *args, **kwargs)
    finally:
        await pool.close()
