"""SQLAlchemy models for researcher groups."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base


class GroupType(str, enum.Enum):
    """Type of researcher group."""

    CUSTOM = "custom"
    MAILING_LIST = "mailing_list"
    SPEAKER_POOL = "speaker_pool"


GROUP_TYPE_ENUM = Enum(
    GroupType,
    name="grouptype",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class ResearcherGroup(Base):
    """Group of researchers for organization and outreach."""

    __tablename__ = "researcher_groups"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[GroupType] = mapped_column(
        GROUP_TYPE_ENUM, default=GroupType.CUSTOM, nullable=False
    )
    keywords: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
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
    members: Mapped[list["GroupMember"]] = relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])  # noqa: F821


class GroupMember(Base):
    """Association table for group membership."""

    __tablename__ = "group_members"

    group_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("researcher_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    researcher_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("authors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    added_by: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    group: Mapped["ResearcherGroup"] = relationship(
        "ResearcherGroup", back_populates="members"
    )
    researcher: Mapped["Author"] = relationship("Author")  # noqa: F821
