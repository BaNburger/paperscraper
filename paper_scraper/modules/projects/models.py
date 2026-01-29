"""SQLAlchemy models for projects module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.papers.models import Paper


class ProjectStage(str, enum.Enum):
    """Default pipeline stages for paper review."""

    INBOX = "inbox"
    SCREENING = "screening"
    EVALUATION = "evaluation"
    SHORTLISTED = "shortlisted"
    CONTACTED = "contacted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class RejectionReason(str, enum.Enum):
    """Predefined reasons for rejecting a paper."""

    OUT_OF_SCOPE = "out_of_scope"
    LOW_NOVELTY = "low_novelty"
    LOW_COMMERCIAL_POTENTIAL = "low_commercial_potential"
    IP_CONCERNS = "ip_concerns"
    INSUFFICIENT_DATA = "insufficient_data"
    COMPETITOR_OWNED = "competitor_owned"
    TOO_EARLY_STAGE = "too_early_stage"
    TOO_LATE_STAGE = "too_late_stage"
    DUPLICATE = "duplicate"
    OTHER = "other"


class Project(Base):
    """Project model for organizing papers in a KanBan pipeline."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configurable pipeline stages (JSON array of stage names)
    # Default stages can be overridden per project
    stages: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            {"name": "inbox", "label": "Inbox", "order": 0},
            {"name": "screening", "label": "Screening", "order": 1},
            {"name": "evaluation", "label": "Evaluation", "order": 2},
            {"name": "shortlisted", "label": "Shortlisted", "order": 3},
            {"name": "contacted", "label": "Contacted", "order": 4},
            {"name": "rejected", "label": "Rejected", "order": 5},
            {"name": "archived", "label": "Archived", "order": 6},
        ],
    )

    # Scoring weights for this project (overrides default weights)
    scoring_weights: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "novelty": 0.20,
            "ip_potential": 0.20,
            "marketability": 0.20,
            "feasibility": 0.20,
            "commercialization": 0.20,
        },
    )

    # Project settings (e.g., auto-score on add, notification settings)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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
    organization: Mapped["Organization"] = relationship("Organization")
    paper_statuses: Mapped[list["PaperProjectStatus"]] = relationship(
        "PaperProjectStatus",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class PaperProjectStatus(Base):
    """Association model tracking a paper's position in a project's pipeline."""

    __tablename__ = "paper_project_statuses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Foreign keys
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Current stage in pipeline
    stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default="inbox"
    )

    # Position within stage for ordering (lower = higher in list)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Assignment
    assigned_to_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Notes and rejection tracking
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[RejectionReason | None] = mapped_column(
        Enum(RejectionReason), nullable=True
    )
    rejection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Priority (1=highest, 5=lowest)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Tags for filtering (JSON array of strings)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

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

    # Stage transition tracking
    stage_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", backref="project_statuses")
    project: Mapped["Project"] = relationship(
        "Project", back_populates="paper_statuses"
    )
    assigned_to: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        # Each paper can only be in a project once
        UniqueConstraint("paper_id", "project_id", name="uq_paper_project"),
        # Index for efficient KanBan queries (get all papers in a stage)
        Index("ix_paper_project_status_project_stage", "project_id", "stage"),
        # Index for finding papers by assignee
        Index("ix_paper_project_status_assigned", "assigned_to_id"),
    )

    def __repr__(self) -> str:
        return f"<PaperProjectStatus paper={self.paper_id} stage={self.stage}>"


class PaperStageHistory(Base):
    """Audit log for paper stage transitions."""

    __tablename__ = "paper_stage_history"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Foreign keys
    paper_project_status_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("paper_project_statuses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Transition details
    from_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    paper_project_status: Mapped["PaperProjectStatus"] = relationship(
        "PaperProjectStatus", backref="stage_history"
    )
    changed_by: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<PaperStageHistory {self.from_stage} -> {self.to_stage}>"
