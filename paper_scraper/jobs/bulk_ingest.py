"""Bulk ingestion job for loading millions of papers from multiple sources.

Orchestrates parallel ingestion across OpenAlex, Semantic Scholar, Lens.org,
EPO, and USPTO with checkpoint/resume support. Ingested papers are stored as
global catalog entries (is_global=true, organization_id=NULL).

Flow:
1. Split sources into parallel tasks
2. Each source fetches in pages using cursor-based pagination
3. Deduplication via DOI (ON CONFLICT DO NOTHING)
4. Redis-backed cursor checkpoints for resume on failure
5. Batch DB writes for throughput
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.ingestion.connectors import get_source_connector
from paper_scraper.modules.papers.models import Paper, PaperSource

logger = logging.getLogger(__name__)

# Sources available for bulk ingestion
BULK_SOURCES = ["openalex", "semantic_scholar", "lens", "epo", "uspto"]

# Batch sizes per source (tuned for API rate limits)
SOURCE_BATCH_SIZES: dict[str, int] = {
    "openalex": 200,
    "semantic_scholar": 100,
    "lens": 500,
    "epo": 100,
    "uspto": 1000,
}


async def bulk_ingest_task(
    ctx: dict[str, Any],
    sources: list[str] | None = None,
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    max_papers_per_source: int = 100_000,
) -> dict[str, Any]:
    """Run parallel bulk ingestion across multiple sources.

    Papers are stored as global catalog entries (is_global=true).

    Args:
        ctx: arq context.
        sources: List of source keys to ingest from. Defaults to all.
        query: Optional search query to filter results.
        date_from: Optional start date (YYYY-MM-DD).
        date_to: Optional end date (YYYY-MM-DD).
        max_papers_per_source: Max papers to fetch per source.

    Returns:
        Summary dict with per-source results.
    """
    active_sources = sources or BULK_SOURCES
    filters: dict[str, Any] = {}
    if query:
        filters["query"] = query
    if date_from or date_to:
        filters["filters"] = {}
        if date_from:
            filters["filters"]["from_publication_date"] = date_from
        if date_to:
            filters["filters"]["to_publication_date"] = date_to

    # Default query for bulk ingestion (broad crawl)
    if "query" not in filters:
        filters["query"] = "*"

    logger.info(
        "Starting bulk ingestion: sources=%s, max_per_source=%d",
        active_sources,
        max_papers_per_source,
    )

    results: dict[str, dict[str, Any]] = {}
    tasks = []
    for source in active_sources:
        tasks.append(
            _ingest_source(
                source=source,
                filters=filters,
                max_papers=max_papers_per_source,
            )
        )

    # Run sources concurrently
    source_results = await asyncio.gather(*tasks, return_exceptions=True)

    total_ingested = 0
    total_errors = 0
    for source, result in zip(active_sources, source_results, strict=False):
        if isinstance(result, Exception):
            results[source] = {
                "status": "failed",
                "error": str(result),
                "papers_ingested": 0,
            }
            total_errors += 1
            logger.error("Bulk ingestion failed for %s: %s", source, result)
        else:
            results[source] = result
            total_ingested += result.get("papers_ingested", 0)

    logger.info(
        "Bulk ingestion complete: %d papers across %d sources, %d errors",
        total_ingested,
        len(active_sources),
        total_errors,
    )

    return {
        "status": "completed",
        "total_papers_ingested": total_ingested,
        "sources": results,
    }


async def _ingest_source(
    source: str,
    filters: dict[str, Any],
    max_papers: int,
) -> dict[str, Any]:
    """Ingest papers from a single source with checkpoint/resume.

    Args:
        source: Source key (e.g., "openalex").
        filters: Query filters.
        max_papers: Maximum papers to ingest.

    Returns:
        Result dict with counts.
    """
    connector = get_source_connector(source)
    batch_size = SOURCE_BATCH_SIZES.get(source, 100)
    papers_ingested = 0
    papers_skipped = 0
    pages_fetched = 0
    errors: list[str] = []

    # Load checkpoint from Redis
    cursor = await _load_checkpoint(source, filters)

    logger.info(
        "Ingesting from %s (batch_size=%d, max=%d, resume_cursor=%s)",
        source,
        batch_size,
        max_papers,
        bool(cursor),
    )

    while papers_ingested < max_papers:
        try:
            batch = await connector.fetch(
                cursor=cursor,
                filters=filters,
                limit=batch_size,
            )
        except Exception as e:
            errors.append(f"Fetch error at page {pages_fetched}: {e}")
            logger.warning("Fetch failed for %s at page %d: %s", source, pages_fetched, e)
            break

        if not batch.records:
            break

        pages_fetched += 1

        # Bulk upsert as global papers
        try:
            created, skipped = await _bulk_upsert_global_papers(batch.records, source)
            papers_ingested += created
            papers_skipped += skipped
        except Exception as e:
            errors.append(f"Upsert error at page {pages_fetched}: {e}")
            logger.warning("Upsert failed for %s at page %d: %s", source, pages_fetched, e)

        # Save checkpoint after each successful page
        cursor = batch.cursor_after
        await _save_checkpoint(source, filters, cursor)

        if not batch.has_more:
            break

        # Brief delay to respect rate limits
        await asyncio.sleep(0.2)

    logger.info(
        "Source %s complete: %d ingested, %d skipped, %d pages, %d errors",
        source,
        papers_ingested,
        papers_skipped,
        pages_fetched,
        len(errors),
    )

    return {
        "status": "completed" if not errors else "completed_with_errors",
        "papers_ingested": papers_ingested,
        "papers_skipped": papers_skipped,
        "pages_fetched": pages_fetched,
        "errors": errors[:20],
    }


async def _bulk_upsert_global_papers(
    records: list[dict[str, Any]],
    source: str,
) -> tuple[int, int]:
    """Bulk upsert papers as global catalog entries.

    Uses INSERT ... ON CONFLICT (lower(doi)) DO NOTHING for dedup.
    Papers without DOI are inserted if title+source_id is unique.

    Args:
        records: Normalized paper records from connector.
        source: Source key for logging.

    Returns:
        (created_count, skipped_count) tuple.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if not records:
        return 0, 0

    created = 0
    skipped = 0

    async with get_db_session() as db:
        for record in records:
            doi = record.get("doi")
            title = record.get("title", "Untitled")
            abstract = record.get("abstract")
            pub_date_str = record.get("publication_date")
            keywords = record.get("keywords", [])
            raw_metadata = record.get("raw_metadata", {})
            citations_count = record.get("citations_count")
            source_id = record.get("source_id")

            # Parse publication date
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str[:10], "%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

            # Map source string to enum
            try:
                paper_source = PaperSource(source)
            except ValueError:
                paper_source = PaperSource.DOI

            values: dict[str, Any] = {
                "title": title[:1000] if title else "Untitled",
                "abstract": abstract[:5000] if abstract else None,
                "doi": doi.lower().strip() if doi else None,
                "source": paper_source.value,
                "source_id": source_id,
                "publication_date": pub_date,
                "keywords": keywords[:20] if keywords else [],
                "raw_metadata": raw_metadata,
                "citations_count": citations_count,
                "is_global": True,
                "organization_id": None,
                "created_at": datetime.now(UTC),
            }

            # Use DOI for dedup when available; otherwise use source+source_id
            if doi:
                stmt = (
                    pg_insert(Paper)
                    .values(**values)
                    .on_conflict_do_nothing(
                        index_elements=["doi"],
                        index_where=Paper.is_global.is_(True),
                    )
                )
            else:
                # For non-DOI records, skip if same source_id exists
                stmt = pg_insert(Paper).values(**values).on_conflict_do_nothing()

            result = await db.execute(stmt)
            if result.rowcount and result.rowcount > 0:
                created += 1
            else:
                skipped += 1

        await db.commit()

    return created, skipped


async def _load_checkpoint(
    source: str,
    filters: dict[str, Any],
) -> dict[str, Any] | None:
    """Load ingestion cursor checkpoint from Redis.

    Args:
        source: Source key.
        filters: Query filters (used in checkpoint key).

    Returns:
        Cursor dict or None if no checkpoint exists.
    """
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        key = _checkpoint_key(source, filters)
        data = await redis.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning("Failed to load checkpoint for %s: %s", source, e)
    return None


async def _save_checkpoint(
    source: str,
    filters: dict[str, Any],
    cursor: dict[str, Any],
) -> None:
    """Save ingestion cursor checkpoint to Redis.

    Args:
        source: Source key.
        filters: Query filters (used in checkpoint key).
        cursor: Current cursor state to persist.
    """
    try:
        from paper_scraper.core.redis import get_redis_pool

        redis = await get_redis_pool()
        key = _checkpoint_key(source, filters)
        await redis.set(key, json.dumps(cursor, default=str), ex=86400 * 30)  # 30 day TTL
    except Exception as e:
        logger.warning("Failed to save checkpoint for %s: %s", source, e)


def _checkpoint_key(source: str, filters: dict[str, Any]) -> str:
    """Build Redis key for bulk ingestion checkpoint."""
    import hashlib

    filter_hash = hashlib.sha256(
        json.dumps(filters, sort_keys=True, default=str).encode()
    ).hexdigest()[:12]
    return f"bulk_ingest:checkpoint:{source}:{filter_hash}"
