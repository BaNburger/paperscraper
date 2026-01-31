"""SQLAlchemy models for saved searches module."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User


class SavedSearch(Base):
    """Saved search model for persisting search queries."""

    __tablename__ = "saved_searches"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Search details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default="hybrid"
    )  # fulltext, semantic, hybrid
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Sharing settings
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    # Alert configuration
    alert_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    alert_frequency: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # daily, weekly, immediately
    last_alert_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Usage tracking
    run_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(
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
    created_by: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_saved_searches_org_name", "organization_id", "name"),
        Index("ix_saved_searches_org_alert", "organization_id", "alert_enabled"),
    )

    def __repr__(self) -> str:
        return f"<SavedSearch {self.name} ({self.id})>"
