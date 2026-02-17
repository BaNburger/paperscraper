"""SQLAlchemy models for scoring module."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization
    from paper_scraper.modules.papers.models import Paper


class PaperScore(Base):
    """Model for storing paper scoring results."""

    __tablename__ = "paper_scores"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Foreign keys
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Individual dimension scores (0-10)
    novelty: Mapped[float] = mapped_column(Float, nullable=False)
    ip_potential: Mapped[float] = mapped_column(Float, nullable=False)
    marketability: Mapped[float] = mapped_column(Float, nullable=False)
    feasibility: Mapped[float] = mapped_column(Float, nullable=False)
    commercialization: Mapped[float] = mapped_column(Float, nullable=False)
    team_readiness: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")

    # Aggregated score
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Scoring metadata
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    weights: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Detailed dimension data (reasoning, details, etc.)
    dimension_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Scoring errors (if any)
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", backref="scores")
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        # Composite index for finding scores by paper within org
        Index("ix_paper_scores_paper_org", "paper_id", "organization_id"),
        # Index for finding latest scores
        Index("ix_paper_scores_org_created", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PaperScore paper={self.paper_id} overall={self.overall_score:.1f}>"


class ScoringJob(Base):
    """Model for tracking scoring job status."""

    __tablename__ = "scoring_jobs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Foreign keys
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job metadata
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # single, batch, rescore
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed

    # Job details
    paper_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    total_papers: Mapped[int] = mapped_column(nullable=False, default=0)
    completed_papers: Mapped[int] = mapped_column(nullable=False, default=0)
    failed_papers: Mapped[int] = mapped_column(nullable=False, default=0)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # arq job reference
    arq_job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

    def __repr__(self) -> str:
        return f"<ScoringJob {self.id} status={self.status}>"


class ScoringPolicy(Base):
    """Organization-level model policy used for scoring."""

    __tablename__ = "scoring_policies"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.3")
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="4096")
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_scoring_policies_org_default", "organization_id", "is_default"),
    )

    def __repr__(self) -> str:
        return f"<ScoringPolicy {self.provider}/{self.model} org={self.organization_id}>"


class GlobalScoreCache(Base):
    """Cross-tenant cache for scoring results keyed by DOI.

    Stores LLM-generated scores with a 90-day TTL so that papers
    with the same DOI do not need to be re-scored across organizations.
    """

    __tablename__ = "global_score_cache"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    doi: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # Individual dimension scores (0-10)
    novelty: Mapped[float] = mapped_column(Float, nullable=False)
    ip_potential: Mapped[float] = mapped_column(Float, nullable=False)
    marketability: Mapped[float] = mapped_column(Float, nullable=False)
    feasibility: Mapped[float] = mapped_column(Float, nullable=False)
    commercialization: Mapped[float] = mapped_column(Float, nullable=False)
    team_readiness: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")

    # Aggregated score (default equal weights)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Scoring metadata
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    dimension_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_global_score_cache_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<GlobalScoreCache doi={self.doi} overall={self.overall_score:.1f}>"
