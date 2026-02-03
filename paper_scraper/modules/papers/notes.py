"""Paper notes and comments system."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.papers.models import Paper


class PaperNote(Base):
    """Note/comment on a paper."""

    __tablename__ = "paper_notes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Multi-tenancy
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    paper_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )  # User UUIDs mentioned

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="notes")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        # Composite index for fetching notes by paper within org
        Index("ix_paper_notes_org_paper", "organization_id", "paper_id"),
    )

    def __repr__(self) -> str:
        return f"<PaperNote {self.id} on paper {self.paper_id}>"
