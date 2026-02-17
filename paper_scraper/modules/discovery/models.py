"""SQLAlchemy models for discovery module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization
    from paper_scraper.modules.saved_searches.models import SavedSearch


class DiscoveryRunStatus(str, enum.Enum):
    """Status of a discovery run."""

    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class DiscoveryRun(Base):
    """Tracks individual discovery run executions."""

    __tablename__ = "discovery_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    saved_search_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Run details
    status: Mapped[DiscoveryRunStatus] = mapped_column(
        Enum(DiscoveryRunStatus, create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DiscoveryRunStatus.RUNNING,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    # Stats
    papers_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    papers_imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    papers_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    papers_added_to_project: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    saved_search: Mapped["SavedSearch"] = relationship("SavedSearch")
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_discovery_runs_search_created", "saved_search_id", "created_at"),
        Index("ix_discovery_runs_org", "organization_id"),
    )

    def __repr__(self) -> str:
        return f"<DiscoveryRun {self.id} source={self.source} status={self.status}>"
