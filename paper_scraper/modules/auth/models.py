"""SQLAlchemy models for authentication module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    pass


class OrganizationType(str, enum.Enum):
    """Types of organizations."""

    UNIVERSITY = "university"
    VC = "vc"
    CORPORATE = "corporate"
    RESEARCH_INSTITUTE = "research_institute"


class SubscriptionTier(str, enum.Enum):
    """Subscription tiers for organizations."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UserRole(str, enum.Enum):
    """User roles within an organization."""

    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class Organization(Base):
    """Organization model representing a tenant in the multi-tenant system."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType),
        nullable=False,
        default=OrganizationType.UNIVERSITY,
    )
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier),
        nullable=False,
        default=SubscriptionTier.FREE,
    )
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.type.value})>"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.MEMBER,
    )
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="users",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
