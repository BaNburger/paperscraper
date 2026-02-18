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
from paper_scraper.jobs.discovery import (
    process_discovery_daily_task,
    process_discovery_weekly_task,
    run_discovery_task,
)
from paper_scraper.jobs.ingestion import ingest_source_task
from paper_scraper.jobs.reports import (
    process_daily_reports_task,
    process_monthly_reports_task,
    process_weekly_reports_task,
    run_single_report_task,
)
from paper_scraper.jobs.repository_sync import (
    run_scheduled_syncs_task,
    sync_repository_source_task,
)
from paper_scraper.jobs.research_groups import sync_research_group_task
from paper_scraper.jobs.retention import (
    apply_retention_policies_task,
    preview_retention_impact_task,
    run_nightly_retention_task,
)
from paper_scraper.jobs.scoring import (
    cleanup_expired_score_cache_task,
    score_paper_task,
    score_papers_batch_task,
)
from paper_scraper.jobs.search import backfill_embeddings_task
from paper_scraper.jobs.webhooks import dispatch_webhook_task


async def startup(ctx: dict[str, Any]) -> None:
    """Initialize shared resources when worker starts."""


async def shutdown(ctx: dict[str, Any]) -> None:
    """Cleanup shared resources when worker shuts down."""


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
        ingest_source_task,
        backfill_embeddings_task,
        process_daily_alerts_task,
        process_weekly_alerts_task,
        process_immediate_alert_task,
        check_and_award_badges_task,
        batch_check_badges_task,
        dispatch_webhook_task,
        sync_repository_source_task,
        run_scheduled_syncs_task,
        process_daily_reports_task,
        process_weekly_reports_task,
        process_monthly_reports_task,
        run_single_report_task,
        apply_retention_policies_task,
        run_nightly_retention_task,
        preview_retention_impact_task,
        process_discovery_daily_task,
        process_discovery_weekly_task,
        run_discovery_task,
        cleanup_expired_score_cache_task,
        sync_research_group_task,
    ]

    # Cron jobs for scheduled tasks
    cron_jobs = [
        # Daily alerts at 6:00 AM UTC
        arq.cron(process_daily_alerts_task, hour=6, minute=0),
        # Weekly alerts on Monday at 6:00 AM UTC
        arq.cron(process_weekly_alerts_task, weekday=0, hour=6, minute=0),
        # Repository syncs every 6 hours
        arq.cron(run_scheduled_syncs_task, hour={0, 6, 12, 18}, minute=0),
        # Daily reports at 7:00 AM UTC
        arq.cron(process_daily_reports_task, hour=7, minute=0),
        # Weekly reports on Monday at 7:30 AM UTC
        arq.cron(process_weekly_reports_task, weekday=0, hour=7, minute=30),
        # Monthly reports on 1st of month at 8:00 AM UTC
        arq.cron(process_monthly_reports_task, day=1, hour=8, minute=0),
        # Nightly retention policy enforcement at 3:00 AM UTC
        arq.cron(run_nightly_retention_task, hour=3, minute=0),
        # Daily discovery profiles at 5:00 AM UTC
        arq.cron(process_discovery_daily_task, hour=5, minute=0),
        # Weekly discovery profiles on Monday at 5:00 AM UTC
        arq.cron(process_discovery_weekly_task, weekday=0, hour=5, minute=0),
        # Daily cleanup of expired global score cache at 3:30 AM UTC
        arq.cron(cleanup_expired_score_cache_task, hour=3, minute=30),
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
    job_id: str | None = None,
    **kwargs: Any,
) -> arq.jobs.Job:
    """Enqueue a job for background processing.

    Args:
        job_name: Name of the job function to run.
        *args: Positional arguments for the job.
        job_id: Optional idempotency key mapped to arq `_job_id`.
        **kwargs: Keyword arguments for the job.

    Returns:
        The enqueued Job object.
    """
    pool = await get_redis_pool()
    try:
        if job_id:
            kwargs["_job_id"] = job_id
        enqueued = await pool.enqueue_job(job_name, *args, **kwargs)
        if enqueued is None:
            raise RuntimeError(
                f"Job '{job_name}' was not enqueued (duplicate id or queue unavailable)"
            )
        return enqueued
    finally:
        await pool.close()
