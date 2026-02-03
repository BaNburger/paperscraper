"""Service layer for paper notes."""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import ForbiddenError, NotFoundError
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote
from paper_scraper.modules.papers.schemas import NoteListResponse, NoteResponse

# Regex pattern for @mentions: @{uuid} format
MENTION_PATTERN = re.compile(r"@\{([0-9a-f-]{36})\}", re.IGNORECASE)


def extract_mentions(content: str) -> list[UUID]:
    """Extract user UUIDs from @mentions in content.

    Format: @{uuid} or @{user-uuid-here}

    Args:
        content: Note content with potential @mentions.

    Returns:
        List of unique user UUIDs mentioned (preserves order).
    """
    seen: set[UUID] = set()
    unique_ids: list[UUID] = []

    for match in MENTION_PATTERN.findall(content):
        try:
            uid = UUID(match)
        except ValueError:
            continue
        if uid not in seen:
            seen.add(uid)
            unique_ids.append(uid)

    return unique_ids


class NoteService:
    """Service for paper notes management."""

    def __init__(self, db: AsyncSession):
        """Initialize note service.

        Args:
            db: Async database session.
        """
        self.db = db

    async def _get_paper(
        self, paper_id: UUID, organization_id: UUID
    ) -> Paper:
        """Get paper by ID with tenant isolation.

        Args:
            paper_id: Paper UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Paper object.

        Raises:
            NotFoundError: If paper not found.
        """
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

    async def list_notes(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> NoteListResponse:
        """List all notes for a paper.

        Args:
            paper_id: Paper UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            List of notes with user info.

        Raises:
            NotFoundError: If paper not found.
        """
        # Verify paper access
        await self._get_paper(paper_id, organization_id)

        # Get notes with user info (filter by organization for extra security)
        result = await self.db.execute(
            select(PaperNote)
            .options(selectinload(PaperNote.user))
            .where(
                PaperNote.paper_id == paper_id,
                PaperNote.organization_id == organization_id,
            )
            .order_by(PaperNote.created_at.desc())
        )
        notes = list(result.scalars().all())

        return NoteListResponse(
            items=notes,
            total=len(notes),
        )

    async def create_note(
        self,
        paper_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        content: str,
    ) -> NoteResponse:
        """Create a new note on a paper.

        Args:
            paper_id: Paper UUID.
            user_id: User UUID (author of note).
            organization_id: Organization UUID for tenant isolation.
            content: Note content.

        Returns:
            Created note.

        Raises:
            NotFoundError: If paper not found.
        """
        # Verify paper access
        await self._get_paper(paper_id, organization_id)

        # Extract mentions from content
        mentions = extract_mentions(content)

        # Create note
        note = PaperNote(
            organization_id=organization_id,
            paper_id=paper_id,
            user_id=user_id,
            content=content,
            mentions=[str(m) for m in mentions],
        )
        self.db.add(note)
        await self.db.commit()

        # Reload with user info
        result = await self.db.execute(
            select(PaperNote)
            .options(selectinload(PaperNote.user))
            .where(PaperNote.id == note.id)
        )
        note = result.scalar_one()

        return note  # type: ignore

    async def get_note(
        self,
        paper_id: UUID,
        note_id: UUID,
        organization_id: UUID,
    ) -> NoteResponse:
        """Get a specific note.

        Args:
            paper_id: Paper UUID.
            note_id: Note UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            Note with user info.

        Raises:
            NotFoundError: If paper or note not found.
        """
        # Verify paper access
        await self._get_paper(paper_id, organization_id)

        result = await self.db.execute(
            select(PaperNote)
            .options(selectinload(PaperNote.user))
            .where(
                PaperNote.id == note_id,
                PaperNote.paper_id == paper_id,
            )
        )
        note = result.scalar_one_or_none()
        if not note:
            raise NotFoundError("Note", str(note_id))

        return note  # type: ignore

    async def update_note(
        self,
        paper_id: UUID,
        note_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        content: str,
    ) -> NoteResponse:
        """Update a note (own notes only).

        Args:
            paper_id: Paper UUID.
            note_id: Note UUID.
            user_id: Current user UUID.
            organization_id: Organization UUID for tenant isolation.
            content: Updated note content.

        Returns:
            Updated note.

        Raises:
            NotFoundError: If paper or note not found.
            ForbiddenError: If user doesn't own the note.
        """
        # Verify paper access
        await self._get_paper(paper_id, organization_id)

        result = await self.db.execute(
            select(PaperNote).where(
                PaperNote.id == note_id,
                PaperNote.paper_id == paper_id,
            )
        )
        note = result.scalar_one_or_none()
        if not note:
            raise NotFoundError("Note", str(note_id))

        # Only note author can edit
        if note.user_id != user_id:
            raise ForbiddenError("You can only edit your own notes")

        # Update content and mentions
        mentions = extract_mentions(content)
        note.content = content
        note.mentions = [str(m) for m in mentions]

        await self.db.commit()

        # Reload with user info
        result = await self.db.execute(
            select(PaperNote)
            .options(selectinload(PaperNote.user))
            .where(PaperNote.id == note.id)
        )
        note = result.scalar_one()

        return note  # type: ignore

    async def delete_note(
        self,
        paper_id: UUID,
        note_id: UUID,
        user_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Delete a note (own notes only).

        Args:
            paper_id: Paper UUID.
            note_id: Note UUID.
            user_id: Current user UUID.
            organization_id: Organization UUID for tenant isolation.

        Returns:
            True if deleted.

        Raises:
            NotFoundError: If paper or note not found.
            ForbiddenError: If user doesn't own the note.
        """
        # Verify paper access
        await self._get_paper(paper_id, organization_id)

        result = await self.db.execute(
            select(PaperNote).where(
                PaperNote.id == note_id,
                PaperNote.paper_id == paper_id,
            )
        )
        note = result.scalar_one_or_none()
        if not note:
            raise NotFoundError("Note", str(note_id))

        # Only note author can delete
        if note.user_id != user_id:
            raise ForbiddenError("You can only delete your own notes")

        await self.db.delete(note)
        await self.db.commit()
        return True
