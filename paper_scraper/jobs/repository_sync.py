"""Repository source sync background jobs."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.developer import service as dev_service
from paper_scraper.modules.developer.models import RepositoryProvider, RepositorySource
from paper_scraper.modules.ingestion.filter_builder import build_repository_pipeline_filters
from paper_scraper.modules.ingestion.pipeline import IngestionPipeline


async def sync_repository_source_task(
    ctx: dict[str, Any],
    source_id: str,
    org_id: str,
) -> dict[str, Any]:
    """Sync papers from a repository source.

    Args:
        ctx: Worker context.
        source_id: Repository source ID.
        org_id: Organization ID.

    Returns:
        Result dict with sync status and stats.
    """
    async with get_db_session() as db:
        try:
            source = await dev_service.get_repository_source(
                db, UUID(org_id), UUID(source_id)
            )
        except Exception:
            return {
                "status": "failed",
                "error": "Repository source not found",
                "source_id": source_id,
            }

        if not source.is_active:
            return {
                "status": "skipped",
                "reason": "Source is inactive",
                "source_id": source_id,
            }

        config = source.config
        provider = source.provider
        query = str(config.get("query", "")).strip() if isinstance(config, dict) else ""
        if not query:
            missing_query_result: dict[str, Any] = {
                "status": "failed",
                "error": "No query configured",
                "completed_at": datetime.now(UTC).isoformat(),
            }
            await dev_service.record_sync_result(
                db,
                UUID(source_id),
                missing_query_result,
                0,
            )
            return {
                "status": "failed",
                "error": "No query configured",
                "source_id": source_id,
                "provider": provider,
            }

        max_results = _as_positive_int(
            config.get("max_results") if isinstance(config, dict) else None,
            default=100,
        )
        filters = build_repository_pipeline_filters(
            provider=provider,
            config=config,
            query=query,
        )

        try:
            if provider not in {item.value for item in RepositoryProvider}:
                raise ValueError(f"Unsupported provider: {provider}")

            run = await IngestionPipeline(db).run(
                source=provider,
                organization_id=UUID(org_id),
                filters=filters,
                limit=max_results,
                idempotency_key=f"repo:{source.id}:{datetime.now(UTC).strftime('%Y%m%d%H%M')}",
            )
            papers_imported, errors = _extract_pipeline_stats(run.stats_json)

            # Record result
            success_result_data: dict[str, Any] = {
                "status": run.status.value,
                "papers_imported": papers_imported,
                "errors": errors[:10],
                "ingest_run_id": str(run.id),
                "completed_at": datetime.now(UTC).isoformat(),
            }
            await dev_service.record_sync_result(
                db,
                UUID(source_id),
                success_result_data,
                papers_imported,
            )

            return {
                "status": run.status.value,
                "source_id": source_id,
                "provider": provider,
                "ingest_run_id": str(run.id),
                "papers_imported": papers_imported,
                "error_count": len(errors),
            }

        except Exception as exc:
            failure_result_data: dict[str, Any] = {
                "status": "failed",
                "error": str(exc),
                "completed_at": datetime.now(UTC).isoformat(),
            }
            await dev_service.record_sync_result(
                db,
                UUID(source_id),
                failure_result_data,
                0,
            )

            return {
                "status": "failed",
                "error": str(exc),
                "source_id": source_id,
            }


def _as_positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _extract_pipeline_stats(stats_json: Any) -> tuple[int, list[str]]:
    stats = stats_json if isinstance(stats_json, dict) else {}
    papers_imported = _as_positive_int(stats.get("papers_created"), default=0)
    errors_raw = stats.get("errors")
    if isinstance(errors_raw, list):
        errors = [str(item) for item in errors_raw if item is not None]
    else:
        errors = []
    return papers_imported, errors


def _matches_cron_part(part: str, value: int) -> bool:
    """Return whether a cron part matches the given value."""
    if part == "*":
        return True

    for fragment in part.split(","):
        if "/" in fragment:
            base, step_str = fragment.split("/", 1)
            step = int(step_str)
            if base == "*":
                if value % step == 0:
                    return True
                continue
            if "-" in base:
                start, end = map(int, base.split("-", 1))
                if start <= value <= end and (value - start) % step == 0:
                    return True
                continue
            start = int(base)
            if value >= start and (value - start) % step == 0:
                return True
            continue

        if "-" in fragment:
            start, end = map(int, fragment.split("-", 1))
            if start <= value <= end:
                return True
            continue

        numeric = int(fragment)
        if numeric == value or (value == 0 and numeric == 7):
            return True

    return False


def _schedule_is_due(schedule: str, now: datetime) -> bool:
    """Evaluate a simple 5-field cron expression against a UTC datetime."""
    parts = schedule.split()
    if len(parts) != 5:
        return False

    minute, hour, day_of_month, month, day_of_week = parts
    # Python weekday: Monday=0..Sunday=6, cron: Sunday=0..Saturday=6
    cron_day_of_week = (now.weekday() + 1) % 7

    return (
        _matches_cron_part(minute, now.minute)
        and _matches_cron_part(hour, now.hour)
        and _matches_cron_part(day_of_month, now.day)
        and _matches_cron_part(month, now.month)
        and _matches_cron_part(day_of_week, cron_day_of_week)
    )


async def run_scheduled_syncs_task(
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """Run all scheduled repository syncs.

    Checks all repository sources with a schedule and runs syncs
    that are due based on their cron expressions.

    Args:
        ctx: Worker context.

    Returns:
        Result dict with sync stats.
    """
    from paper_scraper.jobs.worker import enqueue_job

    async with get_db_session() as db:
        # Get all active sources with schedules
        result = await db.execute(
            select(RepositorySource).where(
                RepositorySource.is_active == True,  # noqa: E712
                RepositorySource.schedule.isnot(None),
            )
        )
        sources = list(result.scalars().all())

        now = datetime.now(UTC)
        syncs_queued = 0
        syncs_skipped = 0
        for source in sources:
            if not source.schedule or not _schedule_is_due(source.schedule, now):
                syncs_skipped += 1
                continue

            await enqueue_job(
                "sync_repository_source_task",
                str(source.id),
                str(source.organization_id),
                job_id=f"sync:{source.id}:{now.strftime('%Y%m%d%H%M')}",
            )
            syncs_queued += 1

        return {
            "status": "completed",
            "syncs_queued": syncs_queued,
            "syncs_skipped": syncs_skipped,
        }
