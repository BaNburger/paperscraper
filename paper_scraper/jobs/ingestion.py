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
