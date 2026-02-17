"""SQLAlchemy models for saved searches module."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.projects.models import Project


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
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

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

    # Discovery / Auto-import configuration
    semantic_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    target_project_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    auto_import_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    import_sources: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )  # e.g. ["openalex", "pubmed", "arxiv"]
    max_import_per_run: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20
    )
    discovery_frequency: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # daily, weekly
    last_discovery_at: Mapped[datetime | None] = mapped_column(
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
    target_project: Mapped["Project | None"] = relationship("Project")

    __table_args__ = (
        Index("ix_saved_searches_org_name", "organization_id", "name"),
        Index("ix_saved_searches_org_alert", "organization_id", "alert_enabled"),
    )

    def __repr__(self) -> str:
        return f"<SavedSearch {self.name} ({self.id})>"
