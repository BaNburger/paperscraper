"""Repository source sync background jobs."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.developer import service as dev_service
from paper_scraper.modules.developer.models import RepositoryProvider, RepositorySource
from paper_scraper.modules.ingestion.models import IngestRunStatus
from paper_scraper.modules.ingestion.service import IngestionService
from paper_scraper.modules.papers.models import PaperSource


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
        papers_imported = 0
        errors = []
        ingestion_service = IngestionService(db)
        checkpoint = await ingestion_service.get_checkpoint(provider, str(source.id))
        run = await ingestion_service.create_run(
            source=provider,
            organization_id=UUID(org_id),
            cursor_before=checkpoint.cursor_json if checkpoint else {},
            idempotency_key=f"repo:{source.id}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
        )

        try:
            if provider == RepositoryProvider.OPENALEX.value:
                papers_imported, errors = await _sync_openalex(
                    db, UUID(org_id), config
                )
            elif provider == RepositoryProvider.PUBMED.value:
                papers_imported, errors = await _sync_pubmed(
                    db, UUID(org_id), config
                )
            elif provider == RepositoryProvider.ARXIV.value:
                papers_imported, errors = await _sync_arxiv(
                    db, UUID(org_id), config
                )
            elif provider == RepositoryProvider.CROSSREF.value:
                papers_imported, errors = await _sync_crossref(
                    db, UUID(org_id), config
                )
            elif provider == RepositoryProvider.SEMANTIC_SCHOLAR.value:
                papers_imported, errors = await _sync_semantic_scholar(
                    db, UUID(org_id), config
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            completed_status = (
                IngestRunStatus.COMPLETED_WITH_ERRORS
                if errors
                else IngestRunStatus.COMPLETED
            )
            cursor_after = {
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "source_id": source_id,
                "papers_imported": papers_imported,
            }
            await ingestion_service.complete_run(
                run.id,
                status=completed_status,
                cursor_after=cursor_after,
                stats_json={
                    "papers_imported": papers_imported,
                    "error_count": len(errors),
                },
            )
            await ingestion_service.upsert_checkpoint(
                source=provider,
                scope_key=str(source.id),
                cursor_json=cursor_after,
            )

            # Record result
            result_data = {
                "status": "completed",
                "papers_imported": papers_imported,
                "errors": errors[:10],  # Limit error log size
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            await dev_service.record_sync_result(
                db, UUID(source_id), result_data, papers_imported
            )
            await db.commit()

            return {
                "status": "completed",
                "source_id": source_id,
                "provider": provider,
                "papers_imported": papers_imported,
                "error_count": len(errors),
            }

        except Exception as e:
            result_data = {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            await ingestion_service.complete_run(
                run.id,
                status=IngestRunStatus.FAILED,
                cursor_after={
                    "last_sync_at": datetime.now(timezone.utc).isoformat(),
                    "source_id": source_id,
                },
                stats_json={"papers_imported": 0, "error_count": 1},
                error_message=str(e),
            )
            await dev_service.record_sync_result(db, UUID(source_id), result_data, 0)
            await db.commit()

            return {
                "status": "failed",
                "error": str(e),
                "source_id": source_id,
            }


async def _sync_openalex(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from OpenAlex.

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    from paper_scraper.jobs.ingestion import ingest_openalex_task

    query = config.get("query", "")
    max_results = config.get("max_results", 100)
    filters = config.get("filters", {})

    if not query:
        return 0, ["No query configured"]

    # Use the existing ingestion task
    result = await ingest_openalex_task(
        {},  # Empty context for direct call
        organization_id=str(org_id),
        query=query,
        max_results=max_results,
        filters=filters,
    )

    papers_imported = result.get("papers_created", 0) + result.get("papers_updated", 0)
    errors = []
    if result.get("errors"):
        errors = result["errors"]

    return papers_imported, errors


async def _sync_pubmed(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from PubMed.

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    from paper_scraper.jobs.worker import ingest_papers_task

    query = config.get("query", "")
    max_results = config.get("max_results", 100)

    if not query:
        return 0, ["No query configured"]

    result = await ingest_papers_task(
        {},
        source="pubmed",
        organization_id=str(org_id),
        query=query,
        max_results=max_results,
    )
    return result.get("papers_created", 0), result.get("errors", [])


async def _sync_arxiv(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from arXiv.

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    from paper_scraper.jobs.worker import ingest_papers_task

    query = config.get("query", "")
    max_results = config.get("max_results", 100)
    category = config.get("filters", {}).get("category")

    if not query:
        return 0, ["No query configured"]

    result = await ingest_papers_task(
        {},
        source="arxiv",
        organization_id=str(org_id),
        query=query,
        max_results=max_results,
        category=category,
    )
    return result.get("papers_created", 0), result.get("errors", [])


async def _sync_crossref(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from Crossref.

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    from paper_scraper.modules.papers.clients.crossref import CrossrefClient
    from paper_scraper.modules.papers.service import PaperService

    query = config.get("query", "")
    max_results = config.get("max_results", 100)

    if not query:
        return 0, ["No query configured"]

    try:
        async with CrossrefClient() as client:
            papers_data = await client.search(query, max_results=max_results)
    except Exception as exc:
        return 0, [str(exc)]

    service = PaperService(db)
    result = await service._ingest_papers_batch(  # noqa: SLF001 - scoped internal use
        papers_data=papers_data,
        organization_id=org_id,
        source=PaperSource.CROSSREF,
    )
    return result.papers_created, result.errors


async def _sync_semantic_scholar(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from Semantic Scholar."""
    from paper_scraper.jobs.worker import ingest_papers_task

    query = config.get("query", "")
    max_results = config.get("max_results", 100)

    if not query:
        return 0, ["No query configured"]

    result = await ingest_papers_task(
        {},
        source="semantic_scholar",
        organization_id=str(org_id),
        query=query,
        max_results=max_results,
    )
    return result.get("papers_created", 0), result.get("errors", [])


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

        now = datetime.now(timezone.utc)
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
