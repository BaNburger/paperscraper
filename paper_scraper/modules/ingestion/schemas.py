"""Pydantic schemas for ingestion pipeline APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from paper_scraper.modules.ingestion.models import IngestRunStatus


class IngestOpenAlexRequest(BaseModel):
    """Request to ingest from OpenAlex."""

    query: str = Field(..., min_length=1, description="Search query for OpenAlex")
    max_results: int = Field(default=100, ge=1, le=1000)
    filters: dict = Field(default_factory=dict)


class IngestPubMedRequest(BaseModel):
    """Request to ingest from PubMed."""

    query: str = Field(..., min_length=1, description="PubMed search query")
    max_results: int = Field(default=100, ge=1, le=1000)


class IngestArxivRequest(BaseModel):
    """Request to ingest from arXiv."""

    query: str = Field(..., min_length=1, description="arXiv search query")
    max_results: int = Field(default=100, ge=1, le=1000)
    category: str | None = Field(default=None, description="Optional arXiv category")


class IngestSemanticScholarRequest(BaseModel):
    """Request to ingest from Semantic Scholar."""

    query: str = Field(..., min_length=1, description="Semantic Scholar search query")
    max_results: int = Field(default=100, ge=1, le=1000)


class IngestJobResponse(BaseModel):
    """Response for async source ingestion job creation."""

    job_id: str
    ingest_run_id: UUID
    source: str
    status: str = "queued"
    message: str


class IngestRunStats(BaseModel):
    """Typed ingestion run stats."""

    fetched_records: int = 0
    source_records_inserted: int = 0
    source_records_duplicates: int = 0
    papers_created: int = 0
    papers_matched: int = 0
    papers_failed: int = 0
    dedupe_report: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict | None) -> "IngestRunStats":
        payload = raw if isinstance(raw, dict) else {}
        return cls(
            fetched_records=int(payload.get("fetched_records", 0) or 0),
            source_records_inserted=int(payload.get("source_records_inserted", 0) or 0),
            source_records_duplicates=int(payload.get("source_records_duplicates", 0) or 0),
            papers_created=int(payload.get("papers_created", 0) or 0),
            papers_matched=int(payload.get("papers_matched", 0) or 0),
            papers_failed=int(payload.get("papers_failed", 0) or 0),
            dedupe_report=(
                payload.get("dedupe_report")
                if isinstance(payload.get("dedupe_report"), dict)
                else {}
            ),
            errors=[str(item) for item in payload.get("errors", []) if item is not None]
            if isinstance(payload.get("errors"), list)
            else [],
        )


class IngestRunResponse(BaseModel):
    """Ingestion run response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    organization_id: UUID | None
    status: IngestRunStatus
    cursor_before: dict = Field(default_factory=dict)
    cursor_after: dict = Field(default_factory=dict)
    stats: IngestRunStats = Field(default_factory=IngestRunStats)
    idempotency_key: str | None = None
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _coerce_stats(cls, data: object) -> object:
        if isinstance(data, dict):
            raw_stats = data.pop("stats_json", None)
            data["stats"] = IngestRunStats.from_raw(raw_stats)
            return data

        raw_stats = getattr(data, "stats_json", None)
        if hasattr(data, "__dict__"):
            # Pydantic will read attributes directly; expose typed stats via a dict.
            return {
                "id": data.id,
                "source": data.source,
                "organization_id": data.organization_id,
                "status": data.status,
                "cursor_before": data.cursor_before,
                "cursor_after": data.cursor_after,
                "stats": IngestRunStats.from_raw(raw_stats),
                "idempotency_key": data.idempotency_key,
                "error_message": data.error_message,
                "started_at": data.started_at,
                "completed_at": data.completed_at,
                "created_at": data.created_at,
            }
        return data


class IngestRunListResponse(BaseModel):
    """Paginated ingestion run list."""

    items: list[IngestRunResponse]
    total: int
    page: int
    page_size: int
    pages: int


class IngestRunRecordResponse(BaseModel):
    """Per-record resolution details for an ingestion run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    source_record_id: str
    content_hash: str
    paper_id: UUID | None = None
    resolution_status: str | None = None
    matched_on: str | None = None
    error: str | None = None
    resolved_at: datetime | None = None
    fetched_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _coerce_error(cls, data: object) -> object:
        if isinstance(data, dict):
            if "error" not in data and "resolution_error" in data:
                data["error"] = data.get("resolution_error")
            return data
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "source": data.source,
                "source_record_id": data.source_record_id,
                "content_hash": data.content_hash,
                "paper_id": data.paper_id,
                "resolution_status": data.resolution_status,
                "matched_on": data.matched_on,
                "error": data.resolution_error,
                "resolved_at": data.resolved_at,
                "fetched_at": data.fetched_at,
            }
        return data


class IngestRunRecordListResponse(BaseModel):
    """Paginated source-record list for a run."""

    items: list[IngestRunRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int
