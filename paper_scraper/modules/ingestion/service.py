"""Service layer for ingestion pipeline control."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.ingestion.models import (
    IngestCheckpoint,
    IngestRun,
    IngestRunStatus,
    SourceRecord,
)
from paper_scraper.modules.ingestion.schemas import (
    IngestRunListResponse,
    IngestRunRecordListResponse,
    IngestRunRecordResponse,
    IngestRunResponse,
)


class IngestionService:
    """Ingestion pipeline service for run bookkeeping and checkpoints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_run(
        self,
        source: str,
        organization_id: UUID | None,
        initiated_by_id: UUID | None = None,
        cursor_before: dict | None = None,
        idempotency_key: str | None = None,
        status: IngestRunStatus = IngestRunStatus.RUNNING,
    ) -> IngestRun:
        """Create and persist a new ingestion run."""
        run = IngestRun(
            source=source,
            organization_id=organization_id,
            initiated_by_id=initiated_by_id,
            status=status,
            cursor_before=cursor_before or {},
            idempotency_key=idempotency_key,
            started_at=datetime.now(UTC),
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def complete_run(
        self,
        run_id: UUID,
        status: IngestRunStatus,
        cursor_after: dict | None = None,
        stats_json: dict | None = None,
        error_message: str | None = None,
    ) -> IngestRun:
        """Mark an ingestion run complete/failed."""
        run = await self.db.get(IngestRun, run_id)
        if run is None:
            raise NotFoundError("IngestRun", str(run_id))

        run.status = status
        run.cursor_after = cursor_after or {}
        run.stats_json = stats_json or {}
        run.error_message = error_message
        run.completed_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def list_runs(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        source: str | None = None,
        status: IngestRunStatus | None = None,
    ) -> IngestRunListResponse:
        """List ingestion runs for a tenant."""
        query = select(IngestRun).where(IngestRun.organization_id == organization_id)
        if source:
            query = query.where(IngestRun.source == source)
        if status:
            query = query.where(IngestRun.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(
            query.order_by(IngestRun.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        runs = list(result.scalars().all())

        return IngestRunListResponse(
            items=[IngestRunResponse.model_validate(run) for run in runs],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def get_run(
        self,
        run_id: UUID,
        organization_id: UUID,
    ) -> IngestRun:
        """Get a single run by id with tenant isolation."""
        result = await self.db.execute(
            select(IngestRun).where(
                IngestRun.id == run_id,
                IngestRun.organization_id == organization_id,
            )
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise NotFoundError("IngestRun", str(run_id))
        return run

    async def get_checkpoint(self, source: str, scope_key: str) -> IngestCheckpoint | None:
        """Fetch checkpoint state for a source+scope pair."""
        return await self.db.get(
            IngestCheckpoint,
            {"source": source, "scope_key": scope_key},
        )

    async def upsert_checkpoint(
        self,
        source: str,
        scope_key: str,
        cursor_json: dict,
    ) -> IngestCheckpoint:
        """Create or update a checkpoint."""
        checkpoint = await self.get_checkpoint(source, scope_key)
        if checkpoint is None:
            checkpoint = IngestCheckpoint(
                source=source,
                scope_key=scope_key,
                cursor_json=cursor_json,
            )
            self.db.add(checkpoint)
        else:
            checkpoint.cursor_json = cursor_json

        await self.db.flush()
        await self.db.refresh(checkpoint)
        return checkpoint

    async def record_source_record(
        self,
        source: str,
        source_record_id: str,
        content_hash: str,
        raw_payload_json: dict,
        ingest_run_id: UUID,
        organization_id: UUID,
    ) -> SourceRecord:
        """Store raw source payload metadata for idempotency/replay."""
        result = await self.db.execute(
            select(SourceRecord).where(
                SourceRecord.source == source,
                SourceRecord.source_record_id == source_record_id,
                SourceRecord.content_hash == content_hash,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        record = SourceRecord(
            source=source,
            source_record_id=source_record_id,
            content_hash=content_hash,
            raw_payload_json=raw_payload_json,
            ingest_run_id=ingest_run_id,
            organization_id=organization_id,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def list_run_records(
        self,
        run_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 50,
        resolution_status: str | None = None,
    ) -> IngestRunRecordListResponse:
        """List source records and resolution outcomes for a run."""
        await self.get_run(run_id=run_id, organization_id=organization_id)

        query = select(SourceRecord).where(
            SourceRecord.ingest_run_id == run_id,
            SourceRecord.organization_id == organization_id,
        )
        if resolution_status:
            query = query.where(SourceRecord.resolution_status == resolution_status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(
            query.order_by(SourceRecord.fetched_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        records = list(result.scalars().all())

        return IngestRunRecordListResponse(
            items=[IngestRunRecordResponse.model_validate(record) for record in records],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )
