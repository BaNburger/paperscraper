"""SQLAlchemy models for developer API keys, webhooks, and repository sources."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base


class WebhookEvent(str, enum.Enum):
    """Available webhook events."""

    PAPER_CREATED = "paper.created"
    PAPER_UPDATED = "paper.updated"
    PAPER_DELETED = "paper.deleted"
    PAPER_SCORED = "paper.scored"
    SUBMISSION_CREATED = "submission.created"
    SUBMISSION_REVIEWED = "submission.reviewed"
    PROJECT_PAPER_MOVED = "project.paper_moved"
    AUTHOR_CONTACTED = "author.contacted"
    ALERT_TRIGGERED = "alert.triggered"


class RepositoryProvider(str, enum.Enum):
    """Supported repository/data source providers."""

    OPENALEX = "openalex"
    PUBMED = "pubmed"
    ARXIV = "arxiv"
    CROSSREF = "crossref"
    SEMANTIC_SCHOLAR = "semantic_scholar"


class APIKey(Base):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    permissions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="api_keys"
    )
    created_by: Mapped["User"] = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey {self.key_prefix}... ({self.name})>"


class Webhook(Base):
    """Webhook configuration for event notifications."""

    __tablename__ = "webhooks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    events: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="webhooks"
    )
    created_by: Mapped["User"] = relationship("User", back_populates="webhooks")

    def __repr__(self) -> str:
        return f"<Webhook {self.name} ({self.url[:30]}...)>"


class RepositorySource(Base):
    """Repository/data source configuration for paper imports."""

    __tablename__ = "repository_sources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    papers_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="repository_sources"
    )
    created_by: Mapped["User"] = relationship("User", back_populates="repository_sources")

    def __repr__(self) -> str:
        return f"<RepositorySource {self.name} ({self.provider})>"


# Forward references for type hints
from paper_scraper.modules.auth.models import Organization, User  # noqa: E402, F401
