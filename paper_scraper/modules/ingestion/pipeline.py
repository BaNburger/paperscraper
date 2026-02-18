"""Ingestion pipeline orchestration (run -> source records -> resolve -> checkpoint)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.ingestion.connectors import get_source_connector
from paper_scraper.modules.ingestion.interfaces import NormalizedPaperBundle, SourceConnector
from paper_scraper.modules.ingestion.models import IngestRun, IngestRunStatus, SourceRecord
from paper_scraper.modules.ingestion.normalizer import DefaultPaperNormalizer
from paper_scraper.modules.ingestion.resolver import PaperEntityResolver
from paper_scraper.modules.ingestion.service import IngestionService


class IngestionPipeline:
    """Pipeline control implementation for source ingestion jobs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ingestion_service = IngestionService(db)
        self.normalizer = DefaultPaperNormalizer()

    async def run(
        self,
        source: str,
        organization_id: UUID,
        filters: dict | None = None,
        limit: int = 100,
        initiated_by_id: UUID | None = None,
        connector: SourceConnector | None = None,
        idempotency_key: str | None = None,
        existing_run_id: UUID | None = None,
    ) -> IngestRun:
        """Run one ingestion cycle for a source and tenant scope."""
        scope_key = self._build_scope_key(organization_id, filters or {})
        checkpoint = await self.ingestion_service.get_checkpoint(source, scope_key)
        cursor_before = checkpoint.cursor_json if checkpoint else {}
        run: IngestRun | None = None

        stats: dict[str, object] = {
            "fetched_records": 0,
            "source_records_inserted": 0,
            "source_records_duplicates": 0,
            "papers_created": 0,
            "papers_matched": 0,
            "papers_failed": 0,
            "dedupe_report": {},
            "errors": [],
        }

        try:
            if existing_run_id is not None:
                run = await self.ingestion_service.get_run(
                    run_id=existing_run_id,
                    organization_id=organization_id,
                )
                if run.source != source:
                    raise ValueError(
                        f"Run/source mismatch: run source is '{run.source}', got '{source}'"
                    )
                if run.status != IngestRunStatus.QUEUED:
                    raise ValueError(
                        f"Run {run.id} must be queued before execution, got '{run.status.value}'"
                    )
                run.status = IngestRunStatus.RUNNING
                run.cursor_before = cursor_before
                if initiated_by_id and run.initiated_by_id is None:
                    run.initiated_by_id = initiated_by_id
                await self.db.flush()
                await self.db.refresh(run)
            else:
                run = await self.ingestion_service.create_run(
                    source=source,
                    organization_id=organization_id,
                    initiated_by_id=initiated_by_id,
                    cursor_before=cursor_before,
                    idempotency_key=idempotency_key,
                    status=IngestRunStatus.RUNNING,
                )

            source_connector = connector or get_source_connector(source)
            resolver = PaperEntityResolver(
                self.db,
                organization_id=organization_id,
                created_by_id=initiated_by_id,
            )

            batch = await source_connector.fetch(
                cursor=cursor_before or None,
                filters=filters,
                limit=limit,
            )
            stats["fetched_records"] = len(batch.records)

            inserted_records, duplicate_count = await self._persist_source_records(
                source=source,
                run_id=run.id,
                organization_id=organization_id,
                records=batch.records,
            )
            stats["source_records_inserted"] = len(inserted_records)
            stats["source_records_duplicates"] = duplicate_count

            dedupe_matches: Counter[str] = Counter()
            papers_created = 0
            papers_matched = 0
            errors: list[str] = []
            resolution_updates: list[dict[str, object]] = []
            normalized_entries: list[tuple[UUID, NormalizedPaperBundle]] = []

            for source_record_id, record in inserted_records:
                try:
                    bundle = self.normalizer.normalize(record)
                    normalized_entries.append((source_record_id, bundle))
                except Exception as exc:
                    papers_failed = int(stats["papers_failed"]) + 1
                    stats["papers_failed"] = papers_failed
                    record_id = self._source_record_id(record)
                    errors.append(f"{record_id}: {exc}")
                    resolution_updates.append({
                        "id": source_record_id,
                        "paper_id": None,
                        "resolution_status": "failed",
                        "matched_on": None,
                        "resolution_error": str(exc)[:2000],
                        "resolved_at": datetime.now(UTC),
                    })

            if normalized_entries:
                try:
                    resolved = await resolver.resolve_many([entry[1] for entry in normalized_entries])
                    for (source_record_id, _bundle), result in zip(
                        normalized_entries,
                        resolved,
                        strict=False,
                    ):
                        if result.created:
                            papers_created += 1
                            resolution_status = "created"
                        else:
                            papers_matched += 1
                            resolution_status = "matched"
                        dedupe_matches[result.matched_on] += 1
                        resolution_updates.append({
                            "id": source_record_id,
                            "paper_id": result.paper_id,
                            "resolution_status": resolution_status,
                            "matched_on": result.matched_on,
                            "resolution_error": None,
                            "resolved_at": datetime.now(UTC),
                        })
                except Exception:
                    # Fallback to single-record resolution to preserve per-record outcomes.
                    for source_record_id, bundle in normalized_entries:
                        try:
                            result = await resolver.resolve(bundle)
                            if result.created:
                                papers_created += 1
                                resolution_status = "created"
                            else:
                                papers_matched += 1
                                resolution_status = "matched"
                            dedupe_matches[result.matched_on] += 1
                            resolution_updates.append({
                                "id": source_record_id,
                                "paper_id": result.paper_id,
                                "resolution_status": resolution_status,
                                "matched_on": result.matched_on,
                                "resolution_error": None,
                                "resolved_at": datetime.now(UTC),
                            })
                        except Exception as exc:
                            papers_failed = int(stats["papers_failed"]) + 1
                            stats["papers_failed"] = papers_failed
                            errors.append(f"{source_record_id}: {exc}")
                            resolution_updates.append({
                                "id": source_record_id,
                                "paper_id": None,
                                "resolution_status": "failed",
                                "matched_on": None,
                                "resolution_error": str(exc)[:2000],
                                "resolved_at": datetime.now(UTC),
                            })

            await self._apply_resolution_updates(resolution_updates)

            stats["papers_created"] = papers_created
            stats["papers_matched"] = papers_matched
            stats["dedupe_report"] = dict(dedupe_matches)
            stats["errors"] = errors

            status = IngestRunStatus.COMPLETED_WITH_ERRORS if errors else IngestRunStatus.COMPLETED
            await self.ingestion_service.upsert_checkpoint(
                source=source,
                scope_key=scope_key,
                cursor_json=batch.cursor_after or cursor_before,
            )
            run = await self.ingestion_service.complete_run(
                run_id=run.id,
                status=status,
                cursor_after=batch.cursor_after or cursor_before,
                stats_json=stats,
                error_message="\n".join(errors[:20]) if errors else None,
            )
            return run
        except Exception as exc:
            if run is not None:
                run = await self.ingestion_service.complete_run(
                    run_id=run.id,
                    status=IngestRunStatus.FAILED,
                    cursor_after=cursor_before,
                    stats_json=stats,
                    error_message=str(exc)[:2000],
                )
            raise

    def _build_scope_key(self, organization_id: UUID, filters: dict) -> str:
        payload = json.dumps(filters, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"org:{organization_id}:{digest}"

    async def _persist_source_records(
        self,
        source: str,
        run_id: UUID,
        organization_id: UUID,
        records: list[dict],
    ) -> tuple[list[tuple[UUID, dict]], int]:
        if not records:
            return [], 0

        payload_rows: list[dict] = []
        lookup_order: list[tuple[str, str]] = []

        for record in records:
            source_record_id = self._source_record_id(record)
            content_hash = self._content_hash(record)
            payload_rows.append(
                {
                    "source": source,
                    "source_record_id": source_record_id,
                    "content_hash": content_hash,
                    "organization_id": organization_id,
                    "ingest_run_id": run_id,
                    "raw_payload_json": record,
                }
            )
            lookup_order.append((source_record_id, content_hash))

        stmt = (
            pg_insert(SourceRecord)
            .values(payload_rows)
            .on_conflict_do_nothing(
                index_elements=[
                    "organization_id",
                    "source",
                    "source_record_id",
                    "content_hash",
                ]
            )
            .returning(SourceRecord.id, SourceRecord.source_record_id, SourceRecord.content_hash)
        )
        result = await self.db.execute(stmt)
        inserted_rows = result.fetchall()
        inserted_keys = {(row[1], row[2]): row[0] for row in inserted_rows}

        inserted_records: list[tuple[UUID, dict]] = []
        for record, key in zip(records, lookup_order, strict=False):
            source_record_row_id = inserted_keys.get(key)
            if source_record_row_id is not None:
                inserted_records.append((source_record_row_id, record))

        duplicate_count = len(records) - len(inserted_records)
        return inserted_records, duplicate_count

    async def _apply_resolution_updates(self, updates: list[dict[str, object]]) -> None:
        if not updates:
            return
        await self.db.execute(update(SourceRecord), updates)

    def _content_hash(self, payload: dict) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _source_record_id(self, record: dict) -> str:
        record_id = (
            record.get("source_id")
            or record.get("id")
            or record.get("doi")
            or record.get("title")
            or ""
        )
        normalized = str(record_id).strip()
        if normalized:
            return normalized
        return self._content_hash(record)
