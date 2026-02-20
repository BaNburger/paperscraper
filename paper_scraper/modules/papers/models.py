"""SQLAlchemy models for papers module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
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

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore[assignment,misc]

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization, User
    from paper_scraper.modules.authors.models import AuthorContact
    from paper_scraper.modules.papers.notes import PaperNote


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
    LENS = "lens"
    EPO = "epo"
    USPTO = "uspto"


class PaperType(str, enum.Enum):
    """Type/category of paper."""

    ORIGINAL_RESEARCH = "original_research"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    METHODOLOGY = "methodology"
    THEORETICAL = "theoretical"
    COMMENTARY = "commentary"
    PREPRINT = "preprint"
    PATENT = "patent"
    PATENT_APPLICATION = "patent_application"
    OTHER = "other"


class Paper(Base):
    """Paper model representing a scientific publication."""

    __tablename__ = "papers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Global catalog flag: True = shared across all tenants, org_id is NULL
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Identifiers
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[PaperSource] = mapped_column(
        Enum(PaperSource, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
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
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    mesh_terms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    references_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citations_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Content
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vector embedding (pgvector, 1536d from text-embedding-3-small)
    embedding = mapped_column(Vector(1536) if Vector else Text, nullable=True)

    # Whether this paper has a vector embedding
    has_embedding: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Raw API response for debugging
    raw_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # AI-generated content
    one_line_pitch: Mapped[str | None] = mapped_column(Text, nullable=True)
    simplified_abstract: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Paper classification
    paper_type: Mapped[PaperType | None] = mapped_column(
        Enum(PaperType, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        index=True,
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
    organization: Mapped["Organization | None"] = relationship("Organization")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])
    authors: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan"
    )
    notes: Mapped[list["PaperNote"]] = relationship(
        "PaperNote", back_populates="paper", cascade="all, delete-orphan"
    )
    claiming_orgs: Mapped[list["OrganizationPaper"]] = relationship(
        "OrganizationPaper", back_populates="paper", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_papers_source_source_id", "source", "source_id"),
        Index("ix_papers_org_created", "organization_id", "created_at"),
        Index(
            "uq_papers_org_lower_doi",
            "organization_id",
            func.lower(doi),
            unique=True,
            postgresql_where=doi.is_not(None),
        ),
        Index(
            "uq_papers_org_source_source_id",
            "organization_id",
            "source",
            "source_id",
            unique=True,
            postgresql_where=source_id.is_not(None),
        ),
        # Global catalog indexes
        Index(
            "ix_papers_global_created",
            "created_at",
            postgresql_where="is_global = true",
        ),
        Index(
            "uq_papers_global_doi",
            func.lower(doi),
            unique=True,
            postgresql_where="is_global = true AND doi IS NOT NULL",
        ),
        Index(
            "ix_papers_global_source",
            "source",
            "created_at",
            postgresql_where="is_global = true",
        ),
    )

    @property
    def has_pdf(self) -> bool:
        """Check if paper has PDF stored."""
        return self.pdf_path is not None

    def __repr__(self) -> str:
        return f"<Paper {self.doi or self.id} - {self.title[:50]}>"


class Author(Base):
    """Author model representing a researcher."""

    __tablename__ = "authors"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Multi-tenancy: Authors scoped to organizations, or NULL for global catalog
    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Global catalog flag
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Identifiers - unique within organization or globally
    orcid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    openalex_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Profile
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    affiliations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Metrics
    h_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    works_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    organization: Mapped["Organization | None"] = relationship("Organization")
    papers: Mapped[list["PaperAuthor"]] = relationship("PaperAuthor", back_populates="author")
    contacts: Mapped[list["AuthorContact"]] = relationship(
        "AuthorContact", back_populates="author", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Unique ORCID within organization
        Index(
            "ix_authors_org_orcid",
            "organization_id",
            "orcid",
            unique=True,
            postgresql_where="orcid IS NOT NULL",
        ),
        # Unique OpenAlex ID within organization
        Index(
            "ix_authors_org_openalex",
            "organization_id",
            "openalex_id",
            unique=True,
            postgresql_where="openalex_id IS NOT NULL",
        ),
        # Global catalog unique indexes
        Index(
            "uq_authors_global_orcid",
            "orcid",
            unique=True,
            postgresql_where="is_global = true AND orcid IS NOT NULL",
        ),
        Index(
            "uq_authors_global_openalex",
            "openalex_id",
            unique=True,
            postgresql_where="is_global = true AND openalex_id IS NOT NULL",
        ),
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
    is_corresponding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="authors")
    author: Mapped["Author"] = relationship("Author", back_populates="papers")

    def __repr__(self) -> str:
        return f"<PaperAuthor paper={self.paper_id} author={self.author_id}>"


class OrganizationPaper(Base):
    """Junction table: which organizations have claimed a global paper.

    When a tenant 'adds to library' from the global catalog, a row is
    created here. This avoids copying the paper row per tenant.
    """

    __tablename__ = "organization_papers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    added_by_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="catalog")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="claiming_orgs")
    added_by: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        Index(
            "uq_org_papers_org_paper",
            "organization_id",
            "paper_id",
            unique=True,
        ),
        Index("ix_org_papers_org_id", "organization_id"),
        Index("ix_org_papers_paper_id", "paper_id"),
    )
