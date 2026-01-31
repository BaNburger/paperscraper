"""arq worker configuration and job definitions."""

from typing import Any
from uuid import UUID

import arq
from arq.connections import ArqRedis, RedisSettings

from paper_scraper.core.config import settings
from paper_scraper.jobs.alerts import (
    process_daily_alerts_task,
    process_immediate_alert_task,
    process_weekly_alerts_task,
)
from paper_scraper.jobs.ingestion import ingest_openalex_task
from paper_scraper.jobs.scoring import (
    generate_embeddings_batch_task,
    score_paper_task,
    score_papers_batch_task,
)
from paper_scraper.jobs.search import backfill_embeddings_task


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup handler.

    Called when the worker starts up. Use this to initialize
    shared resources like database connections.

    Args:
        ctx: Worker context dictionary for storing shared resources.
    """
    pass


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown handler.

    Called when the worker shuts down. Use this to cleanup
    shared resources.

    Args:
        ctx: Worker context dictionary.
    """
    pass


# =============================================================================
# Job Definitions
# =============================================================================


async def ingest_papers_task(
    ctx: dict[str, Any],
    source: str,
    query: str,
    project_id: UUID | None = None,
    max_results: int = 100,
) -> dict[str, Any]:
    """Ingest papers from an external source.

    Args:
        ctx: Worker context.
        source: Source to ingest from ('pubmed', 'arxiv', 'crossref').
        query: Search query for the source.
        project_id: Optional project to add papers to.
        max_results: Maximum number of papers to ingest.

    Returns:
        Dict with ingestion results.
    """
    # TODO: Implement paper ingestion for other sources
    return {
        "status": "completed",
        "source": source,
        "papers_ingested": 0,
    }


# =============================================================================
# Worker Configuration
# =============================================================================


def get_redis_settings() -> RedisSettings:
    """Get Redis settings from application config."""
    # Parse Redis URL
    url = settings.REDIS_URL
    # arq expects RedisSettings, we'll parse the URL
    # Format: redis://[:password@]host[:port][/db]
    if url.startswith("redis://"):
        url = url[8:]

    # Split off db number if present
    db = 0
    if "/" in url:
        url, db_str = url.rsplit("/", 1)
        db = int(db_str) if db_str else 0

    # Split host and port
    host = "localhost"
    port = 6379
    password = None

    if "@" in url:
        auth, hostport = url.rsplit("@", 1)
        password = auth.split(":")[-1] if ":" in auth else auth
    else:
        hostport = url

    if ":" in hostport:
        host, port_str = hostport.split(":")
        port = int(port_str)
    else:
        host = hostport

    return RedisSettings(
        host=host,
        port=port,
        password=password,
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
