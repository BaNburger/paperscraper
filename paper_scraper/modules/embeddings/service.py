"""Shared embedding generation service for papers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.sync import SyncService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.projects.models import ProjectPaper
from paper_scraper.modules.scoring.embeddings import EmbeddingClient

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmbeddingBackfillSummary:
    """Summary of embedding backfill execution."""

    papers_processed: int
    papers_succeeded: int
    papers_failed: int
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EmbeddingStatsSummary:
    """Embedding coverage stats for a tenant."""

    total_papers: int
    with_embedding: int
    without_embedding: int
    embedding_coverage: float


class EmbeddingService:
    """Shared service for paper embedding operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.embedding_client = EmbeddingClient()
        self.sync = SyncService()

    async def generate_for_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
        force_regenerate: bool = False,
    ) -> bool:
        """Generate embedding for one paper."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        paper = result.scalar_one_or_none()
        if paper is None:
            raise NotFoundError("Paper", str(paper_id))

        if paper.has_embedding and not force_regenerate:
            return False

        embedding = await self.embedding_client.embed_text(self._paper_to_text(paper))

        # Store embedding directly on the paper row (pgvector)
        paper.embedding = embedding
        paper.has_embedding = True
        await self.db.flush()

        # Sync metadata to Typesense (embedding stored in pgvector, not Typesense)
        self._sync_paper_metadata(paper)

        return True

    async def count_without_embeddings(
        self,
        organization_id: UUID,
    ) -> int:
        """Count papers missing embeddings."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.has_embedding.is_(False),
            )
        )
        return int(result.scalar() or 0)

    async def get_stats(self, organization_id: UUID) -> EmbeddingStatsSummary:
        """Get embedding coverage stats."""
        with_embedding_result = await self.db.execute(
            select(func.count())
            .select_from(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.has_embedding.is_(True),
            )
        )
        without_embedding_result = await self.db.execute(
            select(func.count())
            .select_from(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.has_embedding.is_(False),
            )
        )

        with_count = int(with_embedding_result.scalar() or 0)
        without_count = int(without_embedding_result.scalar() or 0)
        total = with_count + without_count
        coverage = round(with_count / total * 100, 2) if total > 0 else 0.0

        return EmbeddingStatsSummary(
            total_papers=total,
            with_embedding=with_count,
            without_embedding=without_count,
            embedding_coverage=coverage,
        )

    async def backfill_for_organization(
        self,
        organization_id: UUID,
        batch_size: int = 100,
        max_papers: int | None = None,
    ) -> EmbeddingBackfillSummary:
        """Backfill embeddings for all papers in an organization."""
        query = (
            select(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.has_embedding.is_(False),
            )
            .order_by(Paper.created_at.desc())
        )
        if max_papers:
            query = query.limit(max_papers)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())
        return await self._embed_papers(papers, batch_size=batch_size)

    async def backfill_for_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        batch_size: int = 100,
        max_papers: int | None = None,
    ) -> EmbeddingBackfillSummary:
        """Backfill embeddings for papers inside one project."""
        query = (
            select(Paper)
            .join(ProjectPaper, ProjectPaper.paper_id == Paper.id)
            .where(
                Paper.organization_id == organization_id,
                ProjectPaper.project_id == project_id,
                Paper.has_embedding.is_(False),
            )
            .order_by(Paper.created_at.desc())
        )
        if max_papers:
            query = query.limit(max_papers)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())
        return await self._embed_papers(papers, batch_size=batch_size)

    async def _embed_papers(
        self,
        papers: list[Paper],
        batch_size: int,
    ) -> EmbeddingBackfillSummary:
        if not papers:
            return EmbeddingBackfillSummary(
                papers_processed=0,
                papers_succeeded=0,
                papers_failed=0,
                errors=[],
            )

        succeeded = 0
        failed = 0
        errors: list[str] = []

        safe_batch_size = max(1, min(batch_size, 500))
        for start in range(0, len(papers), safe_batch_size):
            chunk = papers[start : start + safe_batch_size]
            texts = [self._paper_to_text(paper) for paper in chunk]
            try:
                embeddings = await self.embedding_client.embed_texts(texts)
                for paper, embedding in zip(chunk, embeddings, strict=False):
                    paper.has_embedding = True
                    await self._sync_paper_to_external(paper, embedding)
                    succeeded += 1
                await self.db.commit()
                continue
            except Exception as chunk_exc:
                errors.append(f"Batch {start // safe_batch_size + 1}: {str(chunk_exc)[:120]}")

            # Fallback to per-paper embedding when batch call fails.
            for paper in chunk:
                try:
                    embedding = await self.embedding_client.embed_text(self._paper_to_text(paper))
                    paper.has_embedding = True
                    await self._sync_paper_to_external(paper, embedding)
                    succeeded += 1
                except Exception as exc:
                    failed += 1
                    errors.append(f"Paper {paper.id}: {str(exc)[:120]}")
            await self.db.commit()

        return EmbeddingBackfillSummary(
            papers_processed=len(papers),
            papers_succeeded=succeeded,
            papers_failed=failed,
            errors=errors[:20],
        )

    async def _sync_paper_to_external(
        self,
        paper: Paper,
        embedding: list[float],
    ) -> None:
        """Store embedding on paper row (pgvector) and sync metadata to Typesense.

        Failures are logged but never raised — the PostgreSQL write is the
        authoritative operation and must not be blocked by external service
        errors.
        """
        try:
            # Store embedding directly on paper row (pgvector)
            paper.embedding = embedding
            paper.has_embedding = True
            # Sync metadata to Typesense
            self._sync_paper_metadata(paper)
        except Exception:
            logger.exception("Failed to sync paper %s to external services", paper.id)

    def _sync_paper_metadata(self, paper: Paper) -> None:
        """Sync paper metadata to Typesense (no embedding — that's in pgvector)."""
        try:
            self.sync.sync_paper(
                paper_id=paper.id,
                organization_id=paper.organization_id,
                title=paper.title,
                abstract=paper.abstract,
                doi=paper.doi,
                source=paper.source.value if paper.source else None,
                journal=paper.journal,
                paper_type=paper.paper_type.value if paper.paper_type else None,
                keywords=paper.keywords,
                citations_count=paper.citations_count,
                has_embedding=paper.has_embedding,
                is_global=getattr(paper, "is_global", False),
                publication_date=paper.publication_date,
                created_at=paper.created_at,
            )
        except Exception:
            logger.exception("Failed to sync paper %s to Typesense", paper.id)

    def _paper_to_text(self, paper: Paper) -> str:
        parts = [f"Title: {paper.title}"]
        if paper.abstract:
            parts.append(f"Abstract: {paper.abstract}")
        if paper.keywords:
            parts.append(f"Keywords: {', '.join(paper.keywords)}")
        return "\n\n".join(parts)
