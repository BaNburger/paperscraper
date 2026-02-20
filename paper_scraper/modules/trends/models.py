"""SQLAlchemy models for trends module."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.papers.models import Paper


class TrendTopic(Base):
    """User-defined trend topic for tracking research areas."""

    __tablename__ = "trend_topics"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Embedding stored in Qdrant "trends" collection (keyed by trend_topic.id)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

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
    creator: Mapped["User | None"] = relationship("User")
    snapshots: Mapped[list["TrendSnapshot"]] = relationship(
        "TrendSnapshot", back_populates="trend_topic", cascade="all, delete-orphan"
    )
    trend_papers: Mapped[list["TrendPaper"]] = relationship(
        "TrendPaper", back_populates="trend_topic", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_trend_topics_org_active", "organization_id", "is_active"),)

    def __repr__(self) -> str:
        return f"<TrendTopic {self.name} org={self.organization_id}>"


class TrendSnapshot(Base):
    """Cached analysis snapshot for a trend topic."""

    __tablename__ = "trend_snapshots"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    trend_topic_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("trend_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Aggregate score metrics
    matched_papers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_novelty: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_ip_potential: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_marketability: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_feasibility: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_commercialization: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_team_readiness: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Patent data
    patent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    patent_results: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # AI-generated insights
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_insights: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    top_keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Publication timeline
    timeline_data: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Metadata
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    trend_topic: Mapped["TrendTopic"] = relationship("TrendTopic", back_populates="snapshots")

    __table_args__ = (Index("ix_trend_snapshots_topic_created", "trend_topic_id", "created_at"),)

    def __repr__(self) -> str:
        return f"<TrendSnapshot topic={self.trend_topic_id} papers={self.matched_papers_count}>"


class TrendPaper(Base):
    """Association between trend topics and matched papers."""

    __tablename__ = "trend_papers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    trend_topic_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("trend_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
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
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    trend_topic: Mapped["TrendTopic"] = relationship("TrendTopic", back_populates="trend_papers")
    paper: Mapped["Paper"] = relationship("Paper")

    __table_args__ = (
        UniqueConstraint("trend_topic_id", "paper_id", name="uq_trend_topic_paper"),
        Index("ix_trend_papers_topic_relevance", "trend_topic_id", "relevance_score"),
    )

    def __repr__(self) -> str:
        return f"<TrendPaper topic={self.trend_topic_id} paper={self.paper_id} score={self.relevance_score:.2f}>"
