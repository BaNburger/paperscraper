"""arq worker configuration and job definitions."""

from typing import Any
from uuid import UUID

import arq
from arq.connections import ArqRedis, RedisSettings

from paper_scraper.core.config import settings


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup handler.

    Called when the worker starts up. Use this to initialize
    shared resources like database connections.

    Args:
        ctx: Worker context dictionary for storing shared resources.
    """
    # TODO: Initialize database connection pool
    # TODO: Initialize LLM client
    pass


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown handler.

    Called when the worker shuts down. Use this to cleanup
    shared resources.

    Args:
        ctx: Worker context dictionary.
    """
    # TODO: Close database connections
    pass


# =============================================================================
# Job Definitions
# =============================================================================


async def score_paper_task(ctx: dict[str, Any], paper_id: UUID) -> dict[str, Any]:
    """Score a paper using the AI scoring pipeline.

    Args:
        ctx: Worker context with shared resources.
        paper_id: UUID of the paper to score.

    Returns:
        Dict with scoring results.
    """
    # TODO: Implement paper scoring
    return {"status": "completed", "paper_id": str(paper_id)}


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
    # TODO: Implement paper ingestion
    return {
        "status": "completed",
        "source": source,
        "papers_ingested": 0,
    }


async def generate_embeddings_task(
    ctx: dict[str, Any],
    paper_ids: list[UUID],
) -> dict[str, Any]:
    """Generate embeddings for papers.

    Args:
        ctx: Worker context.
        paper_ids: List of paper UUIDs to generate embeddings for.

    Returns:
        Dict with generation results.
    """
    # TODO: Implement embedding generation
    return {
        "status": "completed",
        "papers_processed": len(paper_ids),
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
        ingest_papers_task,
        generate_embeddings_task,
    ]

    # Redis connection settings
    redis_settings = get_redis_settings()

    # Startup/shutdown handlers
    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = 10
    job_timeout = 300  # 5 minutes
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
