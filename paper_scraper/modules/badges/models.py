"""SQLAlchemy models for badges and gamification."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
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


class BadgeCategory(str, enum.Enum):
    """Category of badge."""

    IMPORT = "import"
    SCORING = "scoring"
    COLLABORATION = "collaboration"
    EXPLORATION = "exploration"
    MILESTONE = "milestone"


class BadgeTier(str, enum.Enum):
    """Tier/rarity level of a badge."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Badge(Base):
    """Available badge definition with criteria."""

    __tablename__ = "badges"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(100), nullable=False, default="trophy")
    category: Mapped[BadgeCategory] = mapped_column(
        Enum(BadgeCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    tier: Mapped[BadgeTier] = mapped_column(
        Enum(BadgeTier, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BadgeTier.BRONZE,
    )
    criteria: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user_badges: Mapped[list["UserBadge"]] = relationship(
        "UserBadge", back_populates="badge", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Badge names must be unique within their scope (system-wide or per-org)
        UniqueConstraint("name", "organization_id", name="uq_badges_name_org"),
    )

    def __repr__(self) -> str:
        return f"<Badge {self.name} ({self.tier.value})>"


class UserBadge(Base):
    """Badge earned by a user."""

    __tablename__ = "user_badges"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    # Relationships
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),)

    def __repr__(self) -> str:
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"
