"""Repository source sync background jobs."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from paper_scraper.core.config import settings
from paper_scraper.modules.developer import service as dev_service
from paper_scraper.modules.developer.models import RepositoryProvider, RepositorySource


# Create a separate engine for background jobs
_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
)
_async_session = async_sessionmaker(_engine, expire_on_commit=False)


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
    async with _async_session() as db:
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
            else:
                return {
                    "status": "failed",
                    "error": f"Unsupported provider: {provider}",
                    "source_id": source_id,
                }

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
        org_id=str(org_id),
        query=query,
        max_results=max_results,
    )

    papers_imported = result.get("papers_ingested", 0)
    errors = []
    if result.get("errors"):
        errors = result["errors"]

    return papers_imported, errors


async def _sync_pubmed(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from PubMed (placeholder).

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    # PubMed ingestion not yet implemented
    return 0, ["PubMed ingestion not yet implemented"]


async def _sync_arxiv(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from arXiv (placeholder).

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    # arXiv ingestion not yet implemented
    return 0, ["arXiv ingestion not yet implemented"]


async def _sync_crossref(
    db,
    org_id: UUID,
    config: dict,
) -> tuple[int, list[str]]:
    """Sync from Crossref (placeholder).

    Args:
        db: Database session.
        org_id: Organization ID.
        config: Source configuration.

    Returns:
        Tuple of (papers_imported, errors).
    """
    # Crossref ingestion not yet implemented
    return 0, ["Crossref ingestion not yet implemented"]


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

    async with _async_session() as db:
        # Get all active sources with schedules
        result = await db.execute(
            select(RepositorySource).where(
                RepositorySource.is_active == True,  # noqa: E712
                RepositorySource.schedule.isnot(None),
            )
        )
        sources = list(result.scalars().all())

        syncs_queued = 0
        for source in sources:
            # For now, just queue all scheduled sources
            # In production, would check if the cron schedule matches current time
            await enqueue_job(
                "sync_repository_source_task",
                str(source.id),
                str(source.organization_id),
            )
            syncs_queued += 1

        return {
            "status": "completed",
            "syncs_queued": syncs_queued,
        }
