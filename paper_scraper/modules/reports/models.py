"""SQLAlchemy models for scheduled reports."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User


class ReportType(str, enum.Enum):
    """Type of scheduled report."""

    DASHBOARD_SUMMARY = "dashboard_summary"
    PAPER_TRENDS = "paper_trends"
    TEAM_ACTIVITY = "team_activity"


class ReportSchedule(str, enum.Enum):
    """Report schedule frequency."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportFormat(str, enum.Enum):
    """Report output format."""

    PDF = "pdf"
    CSV = "csv"


class ScheduledReport(Base):
    """Scheduled report configuration."""

    __tablename__ = "scheduled_reports"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Report configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    schedule: Mapped[ReportSchedule] = mapped_column(
        Enum(ReportSchedule, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    recipients: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, values_callable=lambda x: [e.value for e in x]),
        default=ReportFormat.PDF,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
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
    organization: Mapped["Organization"] = relationship("Organization")
    created_by: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        Index("ix_scheduled_reports_org_active", "organization_id", "is_active"),
        Index("ix_scheduled_reports_schedule", "schedule", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ScheduledReport {self.name} ({self.schedule.value})>"
