"""SQLAlchemy models for alerts module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.saved_searches.models import SavedSearch


class AlertStatus(str, enum.Enum):
    """Status of an alert delivery."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"  # No new results


class AlertChannel(str, enum.Enum):
    """Alert delivery channels."""

    EMAIL = "email"
    IN_APP = "in_app"


class Alert(Base):
    """Alert configuration model."""

    __tablename__ = "alerts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saved_search_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("saved_searches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Alert configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel: Mapped[AlertChannel] = mapped_column(
        Enum(AlertChannel), nullable=False, default=AlertChannel.EMAIL
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Frequency settings
    frequency: Mapped[str] = mapped_column(
        String(50), nullable=False, default="daily"
    )  # immediately, daily, weekly

    # Threshold settings
    min_results: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Minimum new results to trigger alert

    # Tracking
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trigger_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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
    user: Mapped["User"] = relationship("User")
    saved_search: Mapped["SavedSearch"] = relationship("SavedSearch")
    results: Mapped[list["AlertResult"]] = relationship(
        "AlertResult", back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alerts_org_active", "organization_id", "is_active"),
        Index("ix_alerts_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Alert {self.name} ({self.id})>"


class AlertResult(Base):
    """Alert result/history model."""

    __tablename__ = "alert_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    alert_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution details
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus), nullable=False, default=AlertStatus.PENDING
    )
    papers_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_papers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Paper IDs that were included in this alert
    paper_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Delivery details
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="results")

    __table_args__ = (
        Index("ix_alert_results_alert_created", "alert_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AlertResult {self.id} status={self.status}>"
