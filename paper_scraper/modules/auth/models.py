"""SQLAlchemy models for authentication module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.compliance.models import RetentionPolicy


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
        Enum(OrganizationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrganizationType.UNIVERSITY,
    )
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SubscriptionTier.FREE,
    )
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    branding: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Organization branding: logo_url, primary_color, accent_color, favicon_url",
    )

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
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        "Webhook",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    repository_sources: Mapped[list["RepositorySource"]] = relationship(
        "RepositorySource",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    retention_policies: Mapped[list["RetentionPolicy"]] = relationship(
        "RetentionPolicy",
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
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.MEMBER,
    )
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Onboarding tracking
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Email verification fields
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verification_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    email_verification_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset fields
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    password_reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="created_by",
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        "Webhook",
        back_populates="created_by",
    )
    repository_sources: Mapped[list["RepositorySource"]] = relationship(
        "RepositorySource",
        back_populates="created_by",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"


class InvitationStatus(str, enum.Enum):
    """Status of a team invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class TeamInvitation(Base):
    """Team invitation model for inviting users to an organization."""

    __tablename__ = "team_invitations"

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
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.MEMBER,
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=InvitationStatus.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

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
    organization: Mapped["Organization"] = relationship("Organization")
    created_by: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<TeamInvitation {self.email} to {self.organization_id} ({self.status.value})>"


# Forward references for developer module models
from paper_scraper.modules.developer.models import (  # noqa: E402, F401
    APIKey,
    RepositorySource,
    Webhook,
)

# Forward reference for compliance module - do not import here to avoid circular imports
# RetentionPolicy is referenced as a string in the relationship definition
