"""SQLAlchemy models for compliance and data retention."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from paper_scraper.core.database import Base


class RetentionAction(str, Enum):
    """Actions to take when retention period expires."""

    ARCHIVE = "archive"
    ANONYMIZE = "anonymize"
    DELETE = "delete"


class RetentionEntityType(str, Enum):
    """Types of entities that can have retention policies."""

    PAPERS = "papers"
    AUDIT_LOGS = "audit_logs"
    CONVERSATIONS = "conversations"
    SUBMISSIONS = "submissions"
    ALERTS = "alerts"
    KNOWLEDGE = "knowledge"
    SEARCH_ACTIVITIES = "search_activities"


class RetentionPolicy(Base):
    """Data retention policy for GDPR and compliance.

    Defines how long data of a specific type should be kept
    and what action to take when the retention period expires.
    """

    __tablename__ = "retention_policies"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Policy configuration
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RetentionAction.ARCHIVE.value
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_affected: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="retention_policies")

    __table_args__ = (
        # Ensure unique policy per entity type per organization
        Index(
            "ix_retention_policies_org_entity",
            "organization_id",
            "entity_type",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        """String representation of retention policy."""
        return (
            f"<RetentionPolicy {self.entity_type} "
            f"retention={self.retention_days}d action={self.action}>"
        )


class RetentionLog(Base):
    """Log of retention policy applications for auditing."""

    __tablename__ = "retention_logs"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("retention_policies.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Execution details
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    records_affected: Mapped[int] = mapped_column(Integer, default=0)
    is_dry_run: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="completed"
    )  # completed, failed, partial
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_retention_logs_org_started", "organization_id", "started_at"),)

    def __repr__(self) -> str:
        """String representation of retention log."""
        return f"<RetentionLog {self.entity_type} {self.action} records={self.records_affected}>"
