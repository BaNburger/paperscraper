"""SQLAlchemy models for research submissions module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.papers.models import Paper


class SubmissionStatus(str, enum.Enum):
    """Status of a research submission."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONVERTED = "converted"


class AttachmentType(str, enum.Enum):
    """Type of submission attachment."""

    PDF = "pdf"
    SUPPLEMENTARY = "supplementary"
    PATENT_DRAFT = "patent_draft"
    PRESENTATION = "presentation"
    OTHER = "other"


SUBMISSION_STATUS_ENUM = Enum(
    SubmissionStatus,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

ATTACHMENT_TYPE_ENUM = Enum(
    AttachmentType,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class ResearchSubmission(Base):
    """Model representing a researcher's submission for TTO review."""

    __tablename__ = "research_submissions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    submitted_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Core metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_field: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Submission details
    status: Mapped[SubmissionStatus] = mapped_column(
        SUBMISSION_STATUS_ENUM, nullable=False, default=SubmissionStatus.DRAFT
    )
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_venue: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Researcher-provided context
    commercial_potential: Mapped[str | None] = mapped_column(Text, nullable=True)
    prior_art_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_disclosure: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Review fields (filled by TTO reviewer)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Conversion tracking
    converted_paper_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Timestamps
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    submitted_by: Mapped["User | None"] = relationship("User", foreign_keys=[submitted_by_id])
    reviewed_by: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by_id])
    converted_paper: Mapped["Paper | None"] = relationship("Paper")
    attachments: Mapped[list["SubmissionAttachment"]] = relationship(
        "SubmissionAttachment",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    scores: Mapped[list["SubmissionScore"]] = relationship(
        "SubmissionScore",
        back_populates="submission",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_submissions_org_status", "organization_id", "status"),
        Index("ix_submissions_submitter", "submitted_by_id", "status"),
        Index("ix_submissions_org_created", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ResearchSubmission {self.id} - {self.title[:50]}>"


class SubmissionAttachment(Base):
    """Model for files attached to a submission."""

    __tablename__ = "submission_attachments"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("research_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File metadata
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attachment_type: Mapped[AttachmentType] = mapped_column(
        ATTACHMENT_TYPE_ENUM, nullable=False, default=AttachmentType.PDF
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    submission: Mapped["ResearchSubmission"] = relationship(
        "ResearchSubmission", back_populates="attachments"
    )

    def __repr__(self) -> str:
        return f"<SubmissionAttachment {self.filename}>"


class SubmissionScore(Base):
    """Model for AI analysis scores of a submission."""

    __tablename__ = "submission_scores"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("research_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Individual dimension scores (0-10)
    novelty: Mapped[float] = mapped_column(Float, nullable=False)
    ip_potential: Mapped[float] = mapped_column(Float, nullable=False)
    marketability: Mapped[float] = mapped_column(Float, nullable=False)
    feasibility: Mapped[float] = mapped_column(Float, nullable=False)
    commercialization: Mapped[float] = mapped_column(Float, nullable=False)

    # Aggregated
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Detailed analysis
    analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimension_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Scoring metadata
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    submission: Mapped["ResearchSubmission"] = relationship(
        "ResearchSubmission", back_populates="scores"
    )

    __table_args__ = (Index("ix_submission_scores_submission", "submission_id", "created_at"),)

    def __repr__(self) -> str:
        return f"<SubmissionScore submission={self.submission_id} overall={self.overall_score:.1f}>"
