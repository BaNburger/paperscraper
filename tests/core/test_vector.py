"""Unit tests for paper_scraper.core.vector — pgvector VectorService.

Tests the pgvector-based VectorService that stores embeddings directly
on the papers table and uses HNSW cosine distance for similarity search.

These tests use the testcontainers PostgreSQL fixture for real pgvector queries.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.vector import EMBEDDING_DIM, VectorService
from paper_scraper.modules.auth.models import Organization
from paper_scraper.modules.papers.models import OrganizationPaper, Paper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dummy_vector(dim: int = EMBEDDING_DIM, seed: float = 0.1) -> list[float]:
    """Return a simple embedding of the given dimension."""
    return [seed] * dim


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def org(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    organization = Organization(name="Test Org", type="university")
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def paper_with_embedding(db_session: AsyncSession, org: Organization) -> Paper:
    """Create a paper with an embedding."""
    paper = Paper(
        organization_id=org.id,
        title="Paper With Embedding",
        source="openalex",
        is_global=True,
        embedding=_dummy_vector(seed=0.5),
        has_embedding=True,
    )
    db_session.add(paper)
    # Also add org claim
    await db_session.flush()
    op = OrganizationPaper(organization_id=org.id, paper_id=paper.id, source="test")
    db_session.add(op)
    await db_session.flush()
    await db_session.refresh(paper)
    return paper


@pytest_asyncio.fixture
async def paper_without_embedding(db_session: AsyncSession, org: Organization) -> Paper:
    """Create a paper without an embedding."""
    paper = Paper(
        organization_id=org.id,
        title="Paper Without Embedding",
        source="openalex",
        is_global=True,
        has_embedding=False,
    )
    db_session.add(paper)
    await db_session.flush()
    op = OrganizationPaper(organization_id=org.id, paper_id=paper.id, source="test")
    db_session.add(op)
    await db_session.flush()
    await db_session.refresh(paper)
    return paper


# ---------------------------------------------------------------------------
# Upsert Operations
# ---------------------------------------------------------------------------


class TestUpsertEmbedding:
    """Tests for VectorService.upsert_embedding."""

    async def test_upsert_sets_embedding_and_flag(
        self, db_session: AsyncSession, paper_without_embedding: Paper
    ) -> None:
        """Upsert should store the embedding and set has_embedding=True."""
        service = VectorService()
        embedding = _dummy_vector(seed=0.7)

        await service.upsert_embedding(db_session, paper_without_embedding.id, embedding)

        await db_session.refresh(paper_without_embedding)
        assert paper_without_embedding.has_embedding is True
        assert paper_without_embedding.embedding is not None

    async def test_upsert_rejects_wrong_dimension(
        self, db_session: AsyncSession, paper_without_embedding: Paper
    ) -> None:
        """Upsert should raise ValueError for wrong embedding dimension."""
        service = VectorService()

        with pytest.raises(ValueError, match="dimension mismatch"):
            await service.upsert_embedding(db_session, paper_without_embedding.id, [0.1] * 768)


class TestUpsertBatch:
    """Tests for VectorService.upsert_batch."""

    async def test_upsert_batch_updates_multiple(
        self, db_session: AsyncSession, org: Organization
    ) -> None:
        """Batch upsert should update multiple papers."""
        # Create papers
        papers = []
        for i in range(3):
            p = Paper(
                organization_id=org.id,
                title=f"Batch Paper {i}",
                source="openalex",
                is_global=True,
            )
            db_session.add(p)
            papers.append(p)
        await db_session.flush()

        service = VectorService()
        items = [
            {"paper_id": p.id, "embedding": _dummy_vector(seed=0.1 * (i + 1))}
            for i, p in enumerate(papers)
        ]
        count = await service.upsert_batch(db_session, items)

        assert count == 3
        for p in papers:
            await db_session.refresh(p)
            assert p.has_embedding is True

    async def test_upsert_batch_empty_list(self, db_session: AsyncSession) -> None:
        """Empty batch should return 0."""
        service = VectorService()
        count = await service.upsert_batch(db_session, [])
        assert count == 0


# ---------------------------------------------------------------------------
# Search Operations
# ---------------------------------------------------------------------------


class TestSearchSimilar:
    """Tests for VectorService.search_similar."""

    async def test_search_returns_results(
        self, db_session: AsyncSession, org: Organization, paper_with_embedding: Paper
    ) -> None:
        """Search should find papers with similar embeddings."""
        service = VectorService()
        query_vec = _dummy_vector(seed=0.5)

        results = await service.search_similar(
            db_session, query_vec, organization_id=org.id, limit=10
        )

        assert len(results) >= 1
        assert results[0]["paper_id"] == str(paper_with_embedding.id)
        assert results[0]["score"] > 0

    async def test_search_excludes_papers_without_embedding(
        self,
        db_session: AsyncSession,
        org: Organization,
        paper_with_embedding: Paper,
        paper_without_embedding: Paper,
    ) -> None:
        """Search should not return papers without embeddings."""
        service = VectorService()
        query_vec = _dummy_vector(seed=0.5)

        results = await service.search_similar(
            db_session, query_vec, organization_id=org.id, limit=100
        )

        result_ids = {r["paper_id"] for r in results}
        assert str(paper_without_embedding.id) not in result_ids


class TestSearchByPaperId:
    """Tests for VectorService.search_by_paper_id."""

    async def test_search_by_paper_excludes_self(
        self, db_session: AsyncSession, org: Organization, paper_with_embedding: Paper
    ) -> None:
        """search_by_paper_id should not return the reference paper itself."""
        service = VectorService()

        results = await service.search_by_paper_id(
            db_session, paper_with_embedding.id, organization_id=org.id
        )

        result_ids = {r["id"] for r in results}
        assert str(paper_with_embedding.id) not in result_ids

    async def test_search_by_nonexistent_paper(self, db_session: AsyncSession) -> None:
        """Searching by a non-existent paper ID should return empty list."""
        service = VectorService()
        results = await service.search_by_paper_id(db_session, uuid4())
        assert results == []


# ---------------------------------------------------------------------------
# Delete Operations
# ---------------------------------------------------------------------------


class TestDeleteEmbedding:
    """Tests for VectorService.delete_embedding."""

    async def test_delete_clears_embedding(
        self, db_session: AsyncSession, paper_with_embedding: Paper
    ) -> None:
        """Delete should clear the embedding and set has_embedding=False."""
        service = VectorService()

        await service.delete_embedding(db_session, paper_with_embedding.id)

        await db_session.refresh(paper_with_embedding)
        assert paper_with_embedding.has_embedding is False
        assert paper_with_embedding.embedding is None


# ---------------------------------------------------------------------------
# Utility Methods
# ---------------------------------------------------------------------------


class TestHasVector:
    """Tests for VectorService.has_vector."""

    async def test_has_vector_true(
        self, db_session: AsyncSession, paper_with_embedding: Paper
    ) -> None:
        """Returns True for papers with embeddings."""
        service = VectorService()
        assert await service.has_vector(db_session, paper_with_embedding.id) is True

    async def test_has_vector_false(
        self, db_session: AsyncSession, paper_without_embedding: Paper
    ) -> None:
        """Returns False for papers without embeddings."""
        service = VectorService()
        assert await service.has_vector(db_session, paper_without_embedding.id) is False

    async def test_has_vector_nonexistent(self, db_session: AsyncSession) -> None:
        """Returns False for non-existent paper IDs."""
        service = VectorService()
        assert await service.has_vector(db_session, uuid4()) is False


class TestCountEmbeddings:
    """Tests for VectorService.count_embeddings."""

    async def test_count_with_org(
        self,
        db_session: AsyncSession,
        org: Organization,
        paper_with_embedding: Paper,
        paper_without_embedding: Paper,
    ) -> None:
        """Count should only count papers with embeddings in org scope."""
        service = VectorService()
        count = await service.count_embeddings(db_session, organization_id=org.id)
        assert count == 1

    async def test_count_global(
        self, db_session: AsyncSession, paper_with_embedding: Paper
    ) -> None:
        """Count should count global papers with embeddings."""
        service = VectorService()
        count = await service.count_embeddings(db_session, global_only=True)
        assert count >= 1
