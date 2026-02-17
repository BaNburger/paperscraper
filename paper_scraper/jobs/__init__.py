"""Background job processing using arq.

This module provides async-native background job processing
as a replacement for Celery.

Usage:
    # Run worker
    arq paper_scraper.jobs.WorkerSettings

    # Enqueue a job from code
    from paper_scraper.jobs import enqueue_job
    await enqueue_job('score_paper_task', paper_id=paper_id)
"""

from paper_scraper.jobs.worker import WorkerSettings, enqueue_job, get_redis_pool

__all__ = ["WorkerSettings", "get_redis_pool", "enqueue_job"]
