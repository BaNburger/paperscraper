"""Highlight management and AI generation for library reader."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError, ValidationError
from paper_scraper.modules.library.models import HighlightSource, PaperHighlight, PaperTextChunk
from paper_scraper.modules.scoring.llm_client import get_llm_client, sanitize_text_for_prompt

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "scoring" / "prompts"
_jinja_env = Environment(
    loader=FileSystemLoader(_PROMPTS_DIR),
    autoescape=False,
)


class LibraryHighlightService:
    """Service for manual and AI-generated highlights."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_highlights(
        self,
        paper_id: UUID,
        organization_id: UUID,
        active_only: bool = True,
    ) -> list[PaperHighlight]:
        """List highlights for a paper."""
        query = (
            select(PaperHighlight)
            .where(
                PaperHighlight.organization_id == organization_id,
                PaperHighlight.paper_id == paper_id,
            )
            .order_by(PaperHighlight.created_at.asc())
        )
        if active_only:
            query = query.where(PaperHighlight.is_active.is_(True))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_highlight(
        self,
        highlight_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
    ) -> PaperHighlight:
        """Get a highlight by ID with tenant isolation."""
        result = await self.db.execute(
            select(PaperHighlight).where(
                PaperHighlight.id == highlight_id,
                PaperHighlight.paper_id == paper_id,
                PaperHighlight.organization_id == organization_id,
            )
        )
        highlight = result.scalar_one_or_none()
        if not highlight:
            raise NotFoundError("PaperHighlight", str(highlight_id))
        return highlight

    async def create_highlight(
        self,
        paper_id: UUID,
        organization_id: UUID,
        created_by: UUID | None,
        *,
        quote: str,
        insight_summary: str,
        confidence: float,
        chunk_id: UUID | None = None,
        chunk_ref: str | None = None,
        source: HighlightSource = HighlightSource.MANUAL,
        generation_id: UUID | None = None,
    ) -> PaperHighlight:
        """Create a highlight entry."""
        normalized_ref = chunk_ref or (
            f"chunk:{chunk_id}" if chunk_id else f"manual:{uuid4().hex[:8]}"
        )
        highlight = PaperHighlight(
            organization_id=organization_id,
            paper_id=paper_id,
            chunk_id=chunk_id,
            chunk_ref=normalized_ref,
            quote=quote,
            insight_summary=insight_summary,
            confidence=confidence,
            source=source,
            generation_id=generation_id or uuid4(),
            created_by=created_by,
        )
        self.db.add(highlight)
        await self.db.flush()
        await self.db.refresh(highlight)
        return highlight

    async def update_highlight(
        self,
        highlight_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
        *,
        quote: str | None = None,
        insight_summary: str | None = None,
        confidence: float | None = None,
        is_active: bool | None = None,
    ) -> PaperHighlight:
        """Update mutable highlight fields."""
        highlight = await self.get_highlight(highlight_id, paper_id, organization_id)
        if quote is not None:
            highlight.quote = quote
        if insight_summary is not None:
            highlight.insight_summary = insight_summary
        if confidence is not None:
            highlight.confidence = confidence
        if is_active is not None:
            highlight.is_active = is_active
        await self.db.flush()
        await self.db.refresh(highlight)
        return highlight

    async def delete_highlight(
        self,
        highlight_id: UUID,
        paper_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a highlight."""
        highlight = await self.get_highlight(highlight_id, paper_id, organization_id)
        await self.db.delete(highlight)
        await self.db.flush()

    async def generate_ai_highlights(
        self,
        paper_id: UUID,
        organization_id: UUID,
        created_by: UUID | None,
        target_count: int = 8,
    ) -> list[PaperHighlight]:
        """Generate a new set of AI highlights for a paper."""
        chunks_result = await self.db.execute(
            select(PaperTextChunk)
            .where(
                PaperTextChunk.paper_id == paper_id,
                PaperTextChunk.organization_id == organization_id,
            )
            .order_by(PaperTextChunk.chunk_index.asc())
        )
        chunks = list(chunks_result.scalars().all())
        if not chunks:
            raise ValidationError("No chunked full text available for this paper")

        await self.db.execute(
            update(PaperHighlight)
            .where(
                PaperHighlight.paper_id == paper_id,
                PaperHighlight.organization_id == organization_id,
                PaperHighlight.source == HighlightSource.AI,
                PaperHighlight.is_active.is_(True),
            )
            .values(is_active=False)
        )

        generation_id = uuid4()
        chunk_by_index = {chunk.chunk_index: chunk for chunk in chunks}

        candidates = await self._generate_with_llm(chunks, target_count)
        if not candidates:
            candidates = self._generate_fallback(chunks, target_count)

        created: list[PaperHighlight] = []
        for candidate in candidates[:target_count]:
            chunk = chunk_by_index.get(candidate["chunk_index"])
            highlight = await self.create_highlight(
                paper_id=paper_id,
                organization_id=organization_id,
                created_by=created_by,
                quote=candidate["quote"],
                insight_summary=candidate["insight_summary"],
                confidence=candidate["confidence"],
                chunk_id=chunk.id if chunk else None,
                chunk_ref=f"chunk:{candidate['chunk_index']}",
                source=HighlightSource.AI,
                generation_id=generation_id,
            )
            created.append(highlight)
        return created

    async def _generate_with_llm(
        self,
        chunks: list[PaperTextChunk],
        target_count: int,
    ) -> list[dict]:
        """Attempt highlight generation using configured LLM."""
        try:
            llm = get_llm_client()
        except Exception as exc:
            logger.info("LLM unavailable for highlight generation: %s", exc)
            return []

        sampled_chunks = chunks[: min(25, len(chunks))]
        prompt_chunks = [
            {
                "chunk_index": c.chunk_index,
                "text": sanitize_text_for_prompt(c.text, max_length=1200),
            }
            for c in sampled_chunks
        ]

        template = _jinja_env.get_template("library_highlights.jinja2")
        prompt = template.render(
            target_count=target_count,
            chunks=prompt_chunks,
        )
        system = (
            "You extract concrete insights from scientific texts. "
            "Return strict JSON with highlight anchors by chunk_index."
        )

        try:
            payload = await llm.complete_json(
                prompt=prompt,
                system=system,
                temperature=0.2,
                max_tokens=1500,
            )
            return self._normalize_llm_payload(payload, sampled_chunks)
        except Exception as exc:
            logger.info("LLM highlight generation failed: %s", exc)
            return []

    def _normalize_llm_payload(
        self,
        payload: dict,
        chunks: list[PaperTextChunk],
    ) -> list[dict]:
        """Normalize and validate LLM response."""
        chunk_indexes = {chunk.chunk_index for chunk in chunks}
        highlights = payload.get("highlights", [])
        if isinstance(highlights, str):
            try:
                highlights = json.loads(highlights)
            except Exception:
                highlights = []

        normalized: list[dict] = []
        for item in highlights if isinstance(highlights, list) else []:
            if not isinstance(item, dict):
                continue
            chunk_index = item.get("chunk_index")
            if not isinstance(chunk_index, int) or chunk_index not in chunk_indexes:
                continue
            quote = str(item.get("quote", "")).strip()
            insight_summary = str(item.get("insight_summary", "")).strip()
            if not quote or not insight_summary:
                continue
            confidence_raw = item.get("confidence", 0.6)
            try:
                confidence = float(confidence_raw)
            except (TypeError, ValueError):
                confidence = 0.6
            normalized.append(
                {
                    "chunk_index": chunk_index,
                    "quote": quote[:5000],
                    "insight_summary": insight_summary[:5000],
                    "confidence": min(max(confidence, 0.0), 1.0),
                }
            )
        return normalized

    def _generate_fallback(
        self,
        chunks: list[PaperTextChunk],
        target_count: int,
    ) -> list[dict]:
        """Generate deterministic fallback highlights when LLM is unavailable."""
        fallback: list[dict] = []
        for chunk in chunks[:target_count]:
            sentences = re_split_sentences(chunk.text)
            quote = (sentences[0] if sentences else chunk.text)[:320]
            fallback.append(
                {
                    "chunk_index": chunk.chunk_index,
                    "quote": quote,
                    "insight_summary": (
                        "Relevant section detected for review. "
                        "Generated fallback insight due to unavailable AI output."
                    ),
                    "confidence": 0.4,
                }
            )
        return fallback


def re_split_sentences(text: str) -> list[str]:
    """Split text into coarse sentences."""
    parts = []
    for item in text.replace("\n", " ").split(". "):
        cleaned = item.strip()
        if cleaned:
            parts.append(cleaned)
    return parts
