"""Background tasks for paper ingestion."""

from typing import Any
from uuid import UUID

from paper_scraper.core.database import get_db_session
from paper_scraper.jobs.payloads import SourceIngestionJobPayload
from paper_scraper.modules.ingestion.pipeline import IngestionPipeline


def _as_result(run_stats: dict[str, Any], run_id: UUID, source: str, status: str) -> dict[str, Any]:
    return {
        "run_id": str(run_id),
        "status": status,
        "source": source,
        "papers_created": int(run_stats.get("papers_created", 0)),
        "papers_matched": int(run_stats.get("papers_matched", 0)),
        "source_records_inserted": int(run_stats.get("source_records_inserted", 0)),
        "source_records_duplicates": int(run_stats.get("source_records_duplicates", 0)),
        "errors": run_stats.get("errors", []),
    }


async def ingest_source_task(
    ctx: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Ingest papers from a supported source via the unified pipeline."""
    parsed = SourceIngestionJobPayload.model_validate(payload)

    async with get_db_session() as db:
        pipeline = IngestionPipeline(db)
        run = await pipeline.run(
            source=parsed.source,
            organization_id=parsed.organization_id,
            initiated_by_id=parsed.initiated_by_id,
            filters={"query": parsed.query, **parsed.filters},
            limit=parsed.max_results,
            existing_run_id=parsed.ingest_run_id,
        )
        return _as_result(run.stats_json or {}, run.id, run.source, run.status.value)


async def ingest_openalex_task(
    ctx: dict[str, Any],
    organization_id: str,
    query: str,
    max_results: int = 100,
    filters: dict | None = None,
    ingest_run_id: str | None = None,
    initiated_by_id: str | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper for legacy OpenAlex ingestion jobs."""
    if ingest_run_id:
        payload = SourceIngestionJobPayload(
            ingest_run_id=UUID(ingest_run_id),
            source="openalex",
            organization_id=UUID(organization_id),
            initiated_by_id=UUID(initiated_by_id) if initiated_by_id else None,
            query=query,
            max_results=max_results,
            filters={"filters": filters or {}},
        )
        return await ingest_source_task(ctx, payload.model_dump(mode="json"))

    async with get_db_session() as db:
        pipeline = IngestionPipeline(db)
        run = await pipeline.run(
            source="openalex",
            organization_id=UUID(organization_id),
            initiated_by_id=UUID(initiated_by_id) if initiated_by_id else None,
            filters={"query": query, "filters": filters or {}},
            limit=max_results,
        )
        return _as_result(run.stats_json or {}, run.id, run.source, run.status.value)
