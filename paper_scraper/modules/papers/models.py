"""SQLAlchemy models for papers module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization


class PaperSource(str, enum.Enum):
    """Source from which paper was imported."""

    DOI = "doi"
    OPENALEX = "openalex"
    PUBMED = "pubmed"
    ARXIV = "arxiv"
    CROSSREF = "crossref"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    MANUAL = "manual"
    PDF = "pdf"


class Paper(Base):
    """Paper model representing a scientific publication."""

    __tablename__ = "papers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identifiers
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[PaperSource] = mapped_column(Enum(PaperSource), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Core metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    volume: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issue: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pages: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Extended metadata
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    mesh_terms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    references_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citations_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Content
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vector embedding (1536d for OpenAI text-embedding-3-small)
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)

    # Raw API response for debugging
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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
    authors: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_papers_source_source_id", "source", "source_id"),
        Index("ix_papers_org_created", "organization_id", "created_at"),
    )

    @property
    def has_pdf(self) -> bool:
        """Check if paper has PDF stored."""
        return self.pdf_path is not None

    @property
    def has_embedding(self) -> bool:
        """Check if paper has embedding vector."""
        return self.embedding is not None

    def __repr__(self) -> str:
        return f"<Paper {self.doi or self.id} - {self.title[:50]}>"


class Author(Base):
    """Author model representing a researcher."""

    __tablename__ = "authors"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Identifiers
    orcid: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    openalex_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True
    )

    # Profile
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    affiliations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Metrics
    h_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    works_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Vector embedding for author similarity (768d)
    embedding: Mapped[list | None] = mapped_column(Vector(768), nullable=True)

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
    papers: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="author"
    )

    def __repr__(self) -> str:
        return f"<Author {self.name} ({self.orcid or 'no orcid'})>"


class PaperAuthor(Base):
    """Association table for paper-author relationship."""

    __tablename__ = "paper_authors"

    paper_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_corresponding: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="authors")
    author: Mapped["Author"] = relationship("Author", back_populates="papers")

    def __repr__(self) -> str:
        return f"<PaperAuthor paper={self.paper_id} author={self.author_id}>"
