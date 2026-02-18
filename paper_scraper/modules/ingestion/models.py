"""SQLAlchemy models for ingestion pipeline control and bookkeeping."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.papers.models import Paper


class IngestRunStatus(str, enum.Enum):
    """Execution status for ingestion runs."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class IngestRun(Base):
    """Top-level record for an ingestion execution."""

    __tablename__ = "ingest_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    initiated_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[IngestRunStatus] = mapped_column(
        Enum(IngestRunStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=IngestRunStatus.QUEUED,
        index=True,
    )
    cursor_before: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    cursor_after: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    stats_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization | None"] = relationship("Organization")
    initiated_by: Mapped["User | None"] = relationship("User")
    source_records: Mapped[list["SourceRecord"]] = relationship(
        "SourceRecord",
        back_populates="ingest_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_ingest_runs_org_source_created", "organization_id", "source", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<IngestRun {self.id} source={self.source} status={self.status.value}>"


class SourceRecord(Base):
    """Raw record storage for ingestion idempotency and replay."""

    __tablename__ = "source_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingest_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ingest_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resolution_status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    matched_on: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolution_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ingest_run: Mapped["IngestRun"] = relationship("IngestRun", back_populates="source_records")
    organization: Mapped["Organization | None"] = relationship("Organization")
    paper: Mapped["Paper | None"] = relationship("Paper")

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source",
            "source_record_id",
            "content_hash",
            name="uq_source_records_org_source_id_hash",
        ),
        Index("ix_source_records_run_resolution", "ingest_run_id", "resolution_status"),
    )

    def __repr__(self) -> str:
        return f"<SourceRecord {self.source}:{self.source_record_id}>"


class IngestCheckpoint(Base):
    """Cursor/checkpoint state per source and scope."""

    __tablename__ = "ingest_checkpoints"

    source: Mapped[str] = mapped_column(String(100), primary_key=True)
    scope_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    cursor_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<IngestCheckpoint {self.source}:{self.scope_key}>"
