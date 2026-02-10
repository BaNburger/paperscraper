"""Scoring context assembly with snapshot + knowledge truncation."""

from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.ingestion.interfaces import ScoreContext
from paper_scraper.modules.knowledge.service import KnowledgeService
from paper_scraper.modules.papers.context_service import PaperContextService
from paper_scraper.modules.papers.models import Paper

_MAX_CONTEXT_CHARS = 8000
_MAX_KNOWLEDGE_CHARS = 3000
_MAX_SNAPSHOT_CHARS = 5000


class DefaultScoreContextAssembler:
    """Default implementation of the ScoreContextAssembler interface."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.knowledge_service = KnowledgeService(db)
        self.paper_context_service = PaperContextService(db)

    async def build(
        self,
        paper_id: UUID,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> ScoreContext:
        """Assemble a bounded prompt context for scoring."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        paper = result.scalar_one_or_none()
        if paper is None:
            raise NotFoundError("Paper", str(paper_id))

        snapshot = await self.paper_context_service.get_snapshot(
            paper_id=paper_id,
            organization_id=organization_id,
        )
        if snapshot is None:
            snapshot = await self.paper_context_service.refresh_snapshot(
                paper_id=paper_id,
                organization_id=organization_id,
            )

        keywords = paper.keywords or []
        sources = await self.knowledge_service.get_relevant_sources_for_scoring(
            organization_id=organization_id,
            user_id=user_id,
            keywords=keywords,
            limit=5,
        )
        knowledge_context = self.knowledge_service.format_knowledge_for_prompt(sources)
        knowledge_context = knowledge_context[:_MAX_KNOWLEDGE_CHARS]

        snapshot_blob = json.dumps(snapshot.context_json, ensure_ascii=False)
        snapshot_blob = snapshot_blob[:_MAX_SNAPSHOT_CHARS]

        prompt_context = "\n\n".join(
            [
                "## Enrichment Snapshot",
                snapshot_blob,
                "## Knowledge Context",
                knowledge_context,
            ]
        ).strip()
        prompt_context = prompt_context[:_MAX_CONTEXT_CHARS]

        return ScoreContext(
            paper_id=paper_id,
            organization_id=organization_id,
            user_id=user_id,
            prompt_context=prompt_context,
            metadata={
                "snapshot_id": str(snapshot.id),
                "snapshot_freshness_at": snapshot.freshness_at.isoformat(),
                "knowledge_sources": len(sources),
            },
        )
