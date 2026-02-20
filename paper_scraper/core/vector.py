"""pgvector-based vector search for paper semantic similarity.

Uses PostgreSQL HNSW indexes for all vector operations. Replaces Qdrant
to consolidate infrastructure and reduce costs at scale (15-25M papers).

The embedding column lives on the papers table directly. Tenant isolation
is handled via JOIN to organization_papers (for "my library" searches) or
via the is_global flag (for catalog browsing).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Embedding dimension (text-embedding-3-small)
EMBEDDING_DIM = 1536


class VectorService:
    """pgvector-backed vector search for paper embeddings.

    All search methods accept an optional organization_id for tenant-scoped
    queries, or operate globally for catalog searches.
    """

    # ------------------------------------------------------------------
    # Upsert Operations
    # ------------------------------------------------------------------

    async def upsert_embedding(
        self,
        db: AsyncSession,
        paper_id: UUID,
        embedding: list[float],
    ) -> None:
        """Store or update the embedding for a single paper.

        Args:
            db: Database session
            paper_id: Paper UUID
            embedding: 1536-dim float vector
        """
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {EMBEDDING_DIM}, "
                f"got {len(embedding)}"
            )

        from paper_scraper.modules.papers.models import Paper

        await db.execute(
            update(Paper)
            .where(Paper.id == paper_id)
            .values(embedding=embedding, has_embedding=True)
        )
        await db.flush()

    async def upsert_batch(
        self,
        db: AsyncSession,
        papers_with_embeddings: list[dict[str, Any]],
    ) -> int:
        """Batch upsert embeddings for multiple papers.

        Args:
            db: Database session
            papers_with_embeddings: List of dicts with keys:
                - paper_id (UUID)
                - embedding (list[float])

        Returns:
            Number of papers updated
        """
        if not papers_with_embeddings:
            return 0

        from paper_scraper.modules.papers.models import Paper

        count = 0
        for item in papers_with_embeddings:
            embedding = item["embedding"]
            if len(embedding) != EMBEDDING_DIM:
                logger.warning(
                    "Skipping paper %s: dimension mismatch (%d != %d)",
                    item["paper_id"],
                    len(embedding),
                    EMBEDDING_DIM,
                )
                continue

            await db.execute(
                update(Paper)
                .where(Paper.id == item["paper_id"])
                .values(embedding=embedding, has_embedding=True)
            )
            count += 1

        await db.flush()
        return count

    # ------------------------------------------------------------------
    # Search Operations
    # ------------------------------------------------------------------

    async def search_similar(
        self,
        db: AsyncSession,
        query_vector: list[float],
        organization_id: UUID | None = None,
        limit: int = 20,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """Find papers similar to a query vector.

        When organization_id is provided, searches only papers claimed by
        that organization (via organization_papers join). Otherwise searches
        the full global catalog.

        Args:
            db: Database session
            query_vector: 1536-dim query embedding
            organization_id: Tenant isolation (None = global catalog)
            limit: Max results (capped at 1000)
            min_score: Minimum cosine similarity (0-1). Note: pgvector uses
                distance, so we convert: distance < (1 - min_score).

        Returns:
            List of dicts: {id, score, paper_id, doi, title}
        """
        limit = min(limit, 1000)

        from paper_scraper.modules.papers.models import OrganizationPaper, Paper

        # pgvector cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity: similarity = 1 - distance
        distance_expr = Paper.embedding.cosine_distance(query_vector)

        query = (
            select(
                Paper.id,
                Paper.doi,
                Paper.title,
                Paper.source,
                distance_expr.label("distance"),
            )
            .where(Paper.embedding.isnot(None))
        )

        if organization_id is not None:
            query = query.join(
                OrganizationPaper,
                OrganizationPaper.paper_id == Paper.id,
            ).where(OrganizationPaper.organization_id == organization_id)
        else:
            query = query.where(Paper.is_global.is_(True))

        if min_score is not None:
            max_distance = 1.0 - min_score
            query = query.where(distance_expr <= max_distance)

        query = query.order_by(distance_expr).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.id),
                "score": round(1.0 - float(row.distance), 4),
                "paper_id": str(row.id),
                "doi": row.doi,
                "title": row.title,
                "source": row.source,
            }
            for row in rows
        ]

    async def search_by_paper_id(
        self,
        db: AsyncSession,
        paper_id: UUID,
        organization_id: UUID | None = None,
        limit: int = 10,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """Find papers similar to an existing paper's embedding.

        Args:
            paper_id: Reference paper UUID
            organization_id: Tenant scope (None = global)
            limit: Max results
            min_score: Minimum cosine similarity

        Returns:
            List of similar papers (excluding the reference paper)
        """
        from paper_scraper.modules.papers.models import Paper

        # Fetch the reference paper's embedding
        ref = await db.execute(
            select(Paper.embedding).where(Paper.id == paper_id)
        )
        ref_row = ref.scalar_one_or_none()
        if ref_row is None:
            return []

        # Search with the reference embedding, excluding the paper itself
        results = await self.search_similar(
            db=db,
            query_vector=list(ref_row),
            organization_id=organization_id,
            limit=limit + 1,
            min_score=min_score,
        )

        # Filter out the reference paper
        return [r for r in results if r["id"] != str(paper_id)][:limit]

    # ------------------------------------------------------------------
    # Delete Operations
    # ------------------------------------------------------------------

    async def delete_embedding(
        self,
        db: AsyncSession,
        paper_id: UUID,
    ) -> None:
        """Remove the embedding from a paper."""
        from paper_scraper.modules.papers.models import Paper

        await db.execute(
            update(Paper)
            .where(Paper.id == paper_id)
            .values(embedding=None, has_embedding=False)
        )
        await db.flush()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    async def count_embeddings(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        global_only: bool = False,
    ) -> int:
        """Count papers with embeddings."""
        from paper_scraper.modules.papers.models import OrganizationPaper, Paper

        query = select(text("count(*)")).select_from(Paper.__table__).where(
            Paper.has_embedding.is_(True)
        )

        if organization_id is not None:
            query = query.join(
                OrganizationPaper.__table__,
                OrganizationPaper.paper_id == Paper.id,
            ).where(OrganizationPaper.organization_id == organization_id)
        elif global_only:
            query = query.where(Paper.is_global.is_(True))

        result = await db.execute(query)
        return result.scalar() or 0

    async def has_vector(
        self,
        db: AsyncSession,
        paper_id: UUID,
    ) -> bool:
        """Check if a paper has an embedding."""
        from paper_scraper.modules.papers.models import Paper

        result = await db.execute(
            select(Paper.has_embedding).where(Paper.id == paper_id)
        )
        return bool(result.scalar_one_or_none())

    async def set_ef_search(self, db: AsyncSession, ef_search: int = 100) -> None:
        """Tune the HNSW ef_search parameter for the current session.

        Higher values improve recall at the cost of latency.
        Default PostgreSQL value is 40; we recommend 100 for production.
        """
        await db.execute(text(f"SET hnsw.ef_search = {ef_search}"))
