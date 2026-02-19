"""SQLAlchemy models for the library module."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.papers.models import Paper


class HighlightSource(str, enum.Enum):
    """Source of a highlight."""

    AI = "ai"
    MANUAL = "manual"
    ZOTERO = "zotero"


class LibraryCollection(Base):
    """Hierarchical collection for organizing papers."""

    __tablename__ = "library_collections"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("library_collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    parent: Mapped[LibraryCollection | None] = relationship(
        "LibraryCollection",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list[LibraryCollection]] = relationship(
        "LibraryCollection",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    items: Mapped[list[LibraryCollectionItem]] = relationship(
        "LibraryCollectionItem",
        back_populates="collection",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_library_collections_org_parent", "organization_id", "parent_id"),)


class LibraryCollectionItem(Base):
    """Association between collections and papers."""

    __tablename__ = "library_collection_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("library_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    collection: Mapped[LibraryCollection] = relationship(
        "LibraryCollection", back_populates="items"
    )
    paper: Mapped[Paper] = relationship("Paper")

    __table_args__ = (
        Index(
            "ix_library_collection_items_unique",
            "collection_id",
            "paper_id",
            unique=True,
        ),
        Index(
            "ix_library_collection_items_org_collection",
            "organization_id",
            "collection_id",
        ),
    )


class PaperTag(Base):
    """User-defined tag on a paper (separate from extracted keywords)."""

    __tablename__ = "paper_tags"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    paper: Mapped[Paper] = relationship("Paper")

    __table_args__ = (
        Index("ix_paper_tags_org_tag", "organization_id", "tag"),
        Index("ix_paper_tags_unique", "organization_id", "paper_id", "tag", unique=True),
    )


class PaperTextChunk(Base):
    """Canonical chunked text representation for a paper."""

    __tablename__ = "paper_text_chunks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    paper: Mapped[Paper] = relationship("Paper")
    highlights: Mapped[list[PaperHighlight]] = relationship(
        "PaperHighlight",
        back_populates="chunk",
    )

    __table_args__ = (
        Index("ix_paper_text_chunks_org_paper", "organization_id", "paper_id"),
        Index("ix_paper_text_chunks_unique", "paper_id", "chunk_index", unique=True),
    )


class PaperHighlight(Base):
    """Insight highlight for a paper with deterministic chunk anchors."""

    __tablename__ = "paper_highlights"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("paper_text_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    chunk_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    insight_summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source: Mapped[HighlightSource] = mapped_column(
        Enum(HighlightSource, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=HighlightSource.AI,
    )
    generation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, default=uuid4)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    paper: Mapped[Paper] = relationship("Paper")
    chunk: Mapped[PaperTextChunk | None] = relationship(
        "PaperTextChunk", back_populates="highlights"
    )

    __table_args__ = (
        Index(
            "ix_paper_highlights_org_paper_active",
            "organization_id",
            "paper_id",
            "is_active",
        ),
        Index("ix_paper_highlights_generation", "paper_id", "generation_id"),
    )
