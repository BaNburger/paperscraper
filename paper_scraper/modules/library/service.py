"""Service layer for library collections, tags, and reader data."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import DuplicateError, NotFoundError, ValidationError
from paper_scraper.modules.library.highlight_service import LibraryHighlightService
from paper_scraper.modules.library.models import (
    HighlightSource,
    LibraryCollection,
    LibraryCollectionItem,
    PaperHighlight,
    PaperTag,
    PaperTextChunk,
)
from paper_scraper.modules.library.schemas import (
    FullTextStatusResponse,
    HydrateFullTextResponse,
    LibraryCollectionCreate,
    LibraryCollectionListResponse,
    LibraryCollectionResponse,
    LibraryCollectionUpdate,
    PaperTagAggregate,
    PaperTagListResponse,
    ReaderChunkResponse,
    ReaderResponse,
)
from paper_scraper.modules.library.text_service import LibraryTextService
from paper_scraper.modules.papers.models import Paper


class LibraryService:
    """Service for the library-first domain layer."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.text_service = LibraryTextService()
        self.highlight_service = LibraryHighlightService(db)

    # =========================================================================
    # Collections
    # =========================================================================

    async def list_collections(self, organization_id: UUID) -> LibraryCollectionListResponse:
        """List collections with item counts."""
        item_count_sq = (
            select(func.count())
            .where(LibraryCollectionItem.collection_id == LibraryCollection.id)
            .correlate(LibraryCollection)
            .scalar_subquery()
            .label("item_count")
        )
        result = await self.db.execute(
            select(LibraryCollection, item_count_sq)
            .where(LibraryCollection.organization_id == organization_id)
            .order_by(LibraryCollection.name.asc())
        )
        rows = result.all()
        items = [
            LibraryCollectionResponse(
                id=row[0].id,
                organization_id=row[0].organization_id,
                name=row[0].name,
                description=row[0].description,
                parent_id=row[0].parent_id,
                created_by=row[0].created_by,
                created_at=row[0].created_at,
                updated_at=row[0].updated_at,
                item_count=row[1] or 0,
            )
            for row in rows
        ]
        return LibraryCollectionListResponse(items=items, total=len(items))

    async def get_collection(self, collection_id: UUID, organization_id: UUID) -> LibraryCollection:
        """Fetch collection with tenant isolation."""
        result = await self.db.execute(
            select(LibraryCollection).where(
                LibraryCollection.id == collection_id,
                LibraryCollection.organization_id == organization_id,
            )
        )
        collection = result.scalar_one_or_none()
        if not collection:
            raise NotFoundError("LibraryCollection", str(collection_id))
        return collection

    async def create_collection(
        self,
        organization_id: UUID,
        user_id: UUID,
        data: LibraryCollectionCreate,
    ) -> LibraryCollection:
        """Create a new collection."""
        if data.parent_id:
            await self.get_collection(data.parent_id, organization_id)

        collection = LibraryCollection(
            organization_id=organization_id,
            created_by=user_id,
            name=data.name.strip(),
            description=data.description,
            parent_id=data.parent_id,
        )
        self.db.add(collection)
        await self.db.flush()
        await self.db.refresh(collection)
        return collection

    async def update_collection(
        self,
        collection_id: UUID,
        organization_id: UUID,
        data: LibraryCollectionUpdate,
    ) -> LibraryCollection:
        """Update collection metadata."""
        collection = await self.get_collection(collection_id, organization_id)

        payload = data.model_dump(exclude_unset=True)
        if "parent_id" in payload and payload["parent_id"] == collection.id:
            raise ValidationError("Collection cannot be its own parent")

        if payload.get("parent_id"):
            await self.get_collection(payload["parent_id"], organization_id)
            await self._ensure_no_collection_cycle(
                collection_id=collection.id,
                candidate_parent_id=payload["parent_id"],
                organization_id=organization_id,
            )

        for key, value in payload.items():
            setattr(collection, key, value)

        await self.db.flush()
        await self.db.refresh(collection)
        return collection

    async def delete_collection(self, collection_id: UUID, organization_id: UUID) -> None:
        """Delete a collection."""
        collection = await self.get_collection(collection_id, organization_id)
        await self.db.delete(collection)
        await self.db.flush()

    async def add_paper_to_collection(
        self,
        collection_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> None:
        """Add paper to a collection."""
        await self.get_collection(collection_id, organization_id)
        await self.get_paper(paper_id, organization_id)

        existing = await self.db.execute(
            select(LibraryCollectionItem).where(
                LibraryCollectionItem.collection_id == collection_id,
                LibraryCollectionItem.paper_id == paper_id,
                LibraryCollectionItem.organization_id == organization_id,
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("LibraryCollectionItem", "paper_id", str(paper_id))

        item = LibraryCollectionItem(
            organization_id=organization_id,
            collection_id=collection_id,
            paper_id=paper_id,
            created_by=user_id,
        )
        self.db.add(item)
        await self.db.flush()

    async def remove_paper_from_collection(
        self,
        collection_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Remove paper from collection."""
        result = await self.db.execute(
            select(LibraryCollectionItem).where(
                LibraryCollectionItem.collection_id == collection_id,
                LibraryCollectionItem.paper_id == paper_id,
                LibraryCollectionItem.organization_id == organization_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        await self.db.delete(item)
        await self.db.flush()
        return True

    # =========================================================================
    # Tags
    # =========================================================================

    async def list_tags(self, organization_id: UUID) -> PaperTagListResponse:
        """List distinct tags with usage count."""
        result = await self.db.execute(
            select(PaperTag.tag, func.count(PaperTag.id))
            .where(PaperTag.organization_id == organization_id)
            .group_by(PaperTag.tag)
            .order_by(func.count(PaperTag.id).desc(), PaperTag.tag.asc())
        )
        rows = result.all()
        items = [PaperTagAggregate(tag=row[0], usage_count=row[1]) for row in rows]
        return PaperTagListResponse(items=items, total=len(items))

    async def add_tag(
        self,
        paper_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        tag: str,
    ) -> PaperTag:
        """Attach a user tag to a paper."""
        await self.get_paper(paper_id, organization_id)
        normalized_tag = tag.strip().lower()
        if not normalized_tag:
            raise ValidationError("Tag cannot be empty")

        existing = await self.db.execute(
            select(PaperTag).where(
                PaperTag.paper_id == paper_id,
                PaperTag.organization_id == organization_id,
                PaperTag.tag == normalized_tag,
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("PaperTag", "tag", normalized_tag)

        record = PaperTag(
            organization_id=organization_id,
            paper_id=paper_id,
            tag=normalized_tag,
            created_by=user_id,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def remove_tag(
        self,
        paper_id: UUID,
        organization_id: UUID,
        tag: str,
    ) -> bool:
        """Remove a tag from a paper."""
        normalized_tag = tag.strip().lower()
        record_result = await self.db.execute(
            select(PaperTag).where(
                PaperTag.paper_id == paper_id,
                PaperTag.organization_id == organization_id,
                PaperTag.tag == normalized_tag,
            )
        )
        record = record_result.scalar_one_or_none()
        if not record:
            return False
        await self.db.delete(record)
        await self.db.flush()
        return True

    # =========================================================================
    # Reader / Full Text
    # =========================================================================

    async def get_reader_data(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> ReaderResponse:
        """Get chunked reader payload for a paper."""
        paper = await self.get_paper(paper_id, organization_id)
        chunks_result = await self.db.execute(
            select(PaperTextChunk)
            .where(
                PaperTextChunk.paper_id == paper_id,
                PaperTextChunk.organization_id == organization_id,
            )
            .order_by(PaperTextChunk.chunk_index.asc())
        )
        chunks = list(chunks_result.scalars().all())
        chunk_payload = [
            ReaderChunkResponse(
                id=chunk.id,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                text=chunk.text,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
            )
            for chunk in chunks
        ]
        source = None
        hydrated_at = None
        if chunks:
            source = chunks[0].source
            hydrated_at = chunks[0].created_at

        status = FullTextStatusResponse(
            available=bool(chunks),
            source=source,
            chunk_count=len(chunks),
            hydrated_at=hydrated_at,
        )
        return ReaderResponse(
            paper_id=paper.id,
            title=paper.title,
            status=status,
            chunks=chunk_payload,
        )

    async def hydrate_full_text(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> HydrateFullTextResponse:
        """Hydrate full text from stored content or OA sources and persist chunks."""
        paper = await self.get_paper(paper_id, organization_id)

        hydrated_source: str | None = None
        hydrated_text: str | None = None

        if paper.full_text and paper.full_text.strip():
            hydrated_text = paper.full_text
            hydrated_source = "paper_full_text"
        elif paper.pdf_path:
            result = await self.text_service.hydrate_from_pdf_path(paper.pdf_path)
            if result:
                hydrated_text = result.text
                hydrated_source = result.source
        if not hydrated_text and paper.doi:
            result = await self.text_service.hydrate_from_oa_sources(paper.doi)
            if result:
                hydrated_text = result.text
                hydrated_source = result.source

        if not hydrated_text:
            return HydrateFullTextResponse(
                paper_id=paper.id,
                hydrated=False,
                source=None,
                chunks_created=0,
                message="No full text available. Upload or attach a PDF to continue.",
            )

        paper.full_text = hydrated_text

        await self.db.execute(
            delete(PaperTextChunk).where(
                PaperTextChunk.paper_id == paper.id,
                PaperTextChunk.organization_id == organization_id,
            )
        )

        chunks = self.text_service.chunk_text(hydrated_text)
        now = datetime.now(timezone.utc)
        for chunk in chunks:
            self.db.add(
                PaperTextChunk(
                    organization_id=organization_id,
                    paper_id=paper.id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    source=hydrated_source or "unknown",
                    created_at=now,
                )
            )

        await self.db.flush()
        return HydrateFullTextResponse(
            paper_id=paper.id,
            hydrated=True,
            source=hydrated_source,
            chunks_created=len(chunks),
            message=f"Hydrated full text and created {len(chunks)} chunks.",
        )

    # =========================================================================
    # Highlights
    # =========================================================================

    async def generate_highlights(
        self,
        paper_id: UUID,
        organization_id: UUID,
        created_by: UUID | None,
        target_count: int,
    ) -> list[PaperHighlight]:
        """Generate AI highlights using chunked text."""
        return await self.highlight_service.generate_ai_highlights(
            paper_id=paper_id,
            organization_id=organization_id,
            created_by=created_by,
            target_count=target_count,
        )

    async def create_manual_highlight(
        self,
        paper_id: UUID,
        organization_id: UUID,
        created_by: UUID | None,
        *,
        chunk_id: UUID | None,
        chunk_ref: str | None,
        quote: str,
        insight_summary: str,
        confidence: float,
    ) -> PaperHighlight:
        """Create manual highlight."""
        await self.get_paper(paper_id, organization_id)
        return await self.highlight_service.create_highlight(
            paper_id=paper_id,
            organization_id=organization_id,
            created_by=created_by,
            chunk_id=chunk_id,
            chunk_ref=chunk_ref,
            quote=quote,
            insight_summary=insight_summary,
            confidence=confidence,
            source=HighlightSource.MANUAL,
        )

    # =========================================================================
    # Internal helpers
    # =========================================================================

    async def get_paper(self, paper_id: UUID, organization_id: UUID) -> Paper:
        """Fetch a paper with tenant isolation."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        paper = result.scalar_one_or_none()
        if not paper:
            raise NotFoundError("Paper", str(paper_id))
        return paper

    async def _ensure_no_collection_cycle(
        self,
        *,
        collection_id: UUID,
        candidate_parent_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Prevent assigning a collection parent to one of its own descendants."""
        current_parent_id: UUID | None = candidate_parent_id
        visited: set[UUID] = set()
        while current_parent_id:
            if current_parent_id == collection_id:
                raise ValidationError("Collection hierarchy cycle detected")
            if current_parent_id in visited:
                break
            visited.add(current_parent_id)
            parent_result = await self.db.execute(
                select(LibraryCollection.parent_id).where(
                    LibraryCollection.id == current_parent_id,
                    LibraryCollection.organization_id == organization_id,
                )
            )
            current_parent_id = parent_result.scalar_one_or_none()
