"""SQLAlchemy models for authors module - Contact tracking."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base


class ContactType(str, enum.Enum):
    """Type of contact made with author."""

    EMAIL = "email"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    MEETING = "meeting"
    CONFERENCE = "conference"
    OTHER = "other"


class ContactOutcome(str, enum.Enum):
    """Outcome of the contact attempt."""

    SUCCESSFUL = "successful"
    NO_RESPONSE = "no_response"
    DECLINED = "declined"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    IN_PROGRESS = "in_progress"


class AuthorContact(Base):
    """Contact log for tracking outreach to authors."""

    __tablename__ = "author_contacts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contacted_by_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Contact details
    contact_type: Mapped[ContactType] = mapped_column(
        Enum(ContactType), nullable=False, default=ContactType.EMAIL
    )
    contact_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Outcome tracking
    outcome: Mapped[ContactOutcome | None] = mapped_column(Enum(ContactOutcome), nullable=True)
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Related paper (if contact is about a specific paper)
    paper_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True
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
    author: Mapped["Author"] = relationship("Author", back_populates="contacts")  # noqa: F821
    contacted_by: Mapped["User"] = relationship("User")  # noqa: F821
    paper: Mapped["Paper"] = relationship("Paper")  # noqa: F821

    __table_args__ = (
        Index("ix_author_contacts_org_author", "organization_id", "author_id"),
        Index("ix_author_contacts_contact_date", "organization_id", "contact_date"),
    )

    def __repr__(self) -> str:
        return f"<AuthorContact {self.id} - {self.contact_type.value} on {self.contact_date}>"
