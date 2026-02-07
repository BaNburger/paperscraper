"""SQLAlchemy models for search module."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from paper_scraper.core.database import Base


class SearchActivity(Base):
    """Track search activity for analytics and gamification."""

    __tablename__ = "search_activities"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    query: Mapped[str] = mapped_column(String(1000), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="hybrid")
    results_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    search_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_search_activities_user_created", "user_id", "created_at"),
        Index("ix_search_activities_org_created", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SearchActivity user={self.user_id} query='{self.query[:30]}'>"
