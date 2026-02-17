"""SQLAlchemy models for research groups module (replaces KanBan projects)."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
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
    from paper_scraper.modules.auth.models import Organization
    from paper_scraper.modules.papers.models import Author, Paper


class SyncStatus(str, enum.Enum):
    """Sync status for research group paper import."""

    IDLE = "idle"
    IMPORTING = "importing"
    CLUSTERING = "clustering"
    READY = "ready"
    FAILED = "failed"


class Project(Base):
    """Research group model — represents an academic chair/lab/institution."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Group metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Institution / researcher info
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    openalex_institution_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    pi_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pi_author_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("authors.id", ondelete="SET NULL"),
        nullable=True,
    )
    openalex_author_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Denormalized counts
    paper_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Sync state
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SyncStatus.IDLE.value
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Extensible settings
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
    pi_author: Mapped["Author | None"] = relationship("Author")
    papers: Mapped[list["ProjectPaper"]] = relationship(
        "ProjectPaper",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    clusters: Mapped[list["ProjectCluster"]] = relationship(
        "ProjectCluster",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(ResearchGroup) {self.name}>"


class ProjectPaper(Base):
    """Junction table: paper belongs to a research group."""

    __tablename__ = "project_papers"

    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="papers")
    paper: Mapped["Paper"] = relationship("Paper")

    __table_args__ = (
        Index("ix_project_papers_paper_id", "paper_id"),
    )

    def __repr__(self) -> str:
        return f"<ProjectPaper project={self.project_id} paper={self.paper_id}>"


class ProjectCluster(Base):
    """Topic cluster within a research group."""

    __tablename__ = "project_clusters"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    paper_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    centroid: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)

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
    project: Mapped["Project"] = relationship("Project", back_populates="clusters")
    cluster_papers: Mapped[list["ProjectClusterPaper"]] = relationship(
        "ProjectClusterPaper",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ProjectCluster {self.label} ({self.paper_count} papers)>"


class ProjectClusterPaper(Base):
    """Junction table: paper belongs to a cluster within a research group."""

    __tablename__ = "project_cluster_papers"

    cluster_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("project_clusters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    cluster: Mapped["ProjectCluster"] = relationship(
        "ProjectCluster", back_populates="cluster_papers"
    )
    paper: Mapped["Paper"] = relationship("Paper")

    __table_args__ = (
        Index("ix_project_cluster_papers_paper_id", "paper_id"),
    )

    def __repr__(self) -> str:
        return f"<ProjectClusterPaper cluster={self.cluster_id} paper={self.paper_id}>"
