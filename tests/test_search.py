"""Tests for search module."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.search.schemas import (
    SearchFilters,
    SearchMode,
    SearchRequest,
)

# Mark for tests requiring PostgreSQL (pg_trgm, pgvector)
requires_postgresql = pytest.mark.skip(
    reason="Requires PostgreSQL with pg_trgm and pgvector extensions"
)


class TestSearchSchemas:
    """Test search schema validation."""

    def test_search_request_defaults(self):
        """Test SearchRequest default values."""
        request = SearchRequest(query="machine learning")
        assert request.mode == SearchMode.HYBRID
        assert request.page == 1
        assert request.page_size == 20
        assert request.include_highlights is True
        assert request.semantic_weight == 0.5
        assert request.filters is None

    def test_search_request_with_filters(self):
        """Test SearchRequest with filters."""
        filters = SearchFilters(
            sources=[PaperSource.OPENALEX, PaperSource.CROSSREF],
            min_score=5.0,
            max_score=10.0,
            date_from=datetime(2023, 1, 1),
            has_embedding=True,
        )
        request = SearchRequest(
            query="quantum computing",
            mode=SearchMode.SEMANTIC,
            filters=filters,
            page=2,
            page_size=50,
        )
        assert request.query == "quantum computing"
        assert request.mode == SearchMode.SEMANTIC
        assert request.filters.min_score == 5.0
        assert request.filters.sources == [PaperSource.OPENALEX, PaperSource.CROSSREF]

    def test_search_request_validation(self):
        """Test SearchRequest validation."""
        # Query too short
        with pytest.raises(ValueError):
            SearchRequest(query="")

        # Invalid page
        with pytest.raises(ValueError):
            SearchRequest(query="test", page=0)

        # Invalid page_size
        with pytest.raises(ValueError):
            SearchRequest(query="test", page_size=200)

        # Invalid semantic_weight
        with pytest.raises(ValueError):
            SearchRequest(query="test", semantic_weight=1.5)

    def test_search_filters_score_validation(self):
        """Test SearchFilters score validation."""
        # Valid scores
        filters = SearchFilters(min_score=0, max_score=10)
        assert filters.min_score == 0
        assert filters.max_score == 10

        # Invalid scores
        with pytest.raises(ValueError):
            SearchFilters(min_score=-1)

        with pytest.raises(ValueError):
            SearchFilters(max_score=15)


class TestSearchEndpoints:
    """Test search API endpoints."""

    @pytest.mark.asyncio
    async def test_search_unauthenticated(self, client: AsyncClient):
        """Test that search requires authentication."""
        response = await client.post(
            "/api/v1/search/",
            json={"query": "machine learning"},
        )
        assert response.status_code == 401

    @requires_postgresql
    @pytest.mark.asyncio
    async def test_fulltext_search_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test fulltext search GET endpoint (requires PostgreSQL with pg_trgm)."""
        response = await client.get(
            "/api/v1/search/fulltext",
            params={"q": "machine learning"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @requires_postgresql
    @pytest.mark.asyncio
    async def test_semantic_search_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test semantic search GET endpoint (requires PostgreSQL with pgvector)."""
        with patch(
            "paper_scraper.modules.search.service.EmbeddingClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.embed_text = AsyncMock(return_value=[0.1] * 1536)
            mock_client.return_value = mock_instance

            response = await client.get(
                "/api/v1/search/semantic",
                params={"q": "quantum algorithms"},
                headers=auth_headers,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_embedding_stats_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test embedding statistics endpoint."""
        # Create some test papers
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="Paper with embedding",
            source=PaperSource.MANUAL,
            # Note: We can't set embedding in SQLite tests
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="Paper without embedding",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([paper1, paper2])
        await db_session.flush()

        response = await client.get(
            "/api/v1/search/embeddings/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_papers" in data
        assert "with_embedding" in data
        assert "without_embedding" in data
        assert "embedding_coverage" in data
        assert data["total_papers"] == 2

    @pytest.mark.asyncio
    async def test_similar_papers_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test finding similar papers for non-existent paper."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/search/similar/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_similar_papers_no_embedding(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test finding similar papers when paper has no embedding."""
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Paper without embedding",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/search/similar/{paper.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["similar_papers"] == []
        assert data["total_found"] == 0


class TestSearchService:
    """Test SearchService methods."""

    @pytest.mark.asyncio
    async def test_apply_filters_sources(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test filter application for paper sources."""
        from sqlalchemy import select

        from paper_scraper.modules.papers.models import Paper as PaperModel
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create papers with different sources
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="OpenAlex Paper",
            source=PaperSource.OPENALEX,
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="Manual Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([paper1, paper2])
        await db_session.flush()

        # Test source filter
        filters = SearchFilters(sources=[PaperSource.OPENALEX])
        base_query = select(PaperModel).where(
            PaperModel.organization_id == test_user.organization_id
        )
        filtered_query = service._apply_filters(
            base_query, filters, test_user.organization_id
        )

        result = await db_session.execute(filtered_query)
        papers = list(result.scalars().all())

        assert len(papers) == 1
        assert papers[0].source == PaperSource.OPENALEX

    @pytest.mark.asyncio
    async def test_apply_filters_dates(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test filter application for date ranges."""
        from sqlalchemy import select

        from paper_scraper.modules.papers.models import Paper as PaperModel
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create papers with different dates
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="Old Paper",
            source=PaperSource.MANUAL,
            publication_date=datetime(2020, 1, 1),
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="New Paper",
            source=PaperSource.MANUAL,
            publication_date=datetime(2024, 1, 1),
        )
        db_session.add_all([paper1, paper2])
        await db_session.flush()

        # Test date filter
        filters = SearchFilters(date_from=datetime(2023, 1, 1))
        base_query = select(PaperModel).where(
            PaperModel.organization_id == test_user.organization_id
        )
        filtered_query = service._apply_filters(
            base_query, filters, test_user.organization_id
        )

        result = await db_session.execute(filtered_query)
        papers = list(result.scalars().all())

        assert len(papers) == 1
        assert papers[0].title == "New Paper"

    @pytest.mark.asyncio
    async def test_apply_filters_journals(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test filter application for journals."""
        from sqlalchemy import select

        from paper_scraper.modules.papers.models import Paper as PaperModel
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create papers with different journals
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="Nature Paper",
            source=PaperSource.MANUAL,
            journal="Nature",
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="Science Paper",
            source=PaperSource.MANUAL,
            journal="Science",
        )
        db_session.add_all([paper1, paper2])
        await db_session.flush()

        # Test journal filter
        filters = SearchFilters(journals=["Nature"])
        base_query = select(PaperModel).where(
            PaperModel.organization_id == test_user.organization_id
        )
        filtered_query = service._apply_filters(
            base_query, filters, test_user.organization_id
        )

        result = await db_session.execute(filtered_query)
        papers = list(result.scalars().all())

        assert len(papers) == 1
        assert papers[0].journal == "Nature"

    @pytest.mark.asyncio
    async def test_generate_highlights(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test highlight generation for search results."""
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        paper = Paper(
            organization_id=test_user.organization_id,
            title="Machine Learning for Healthcare",
            abstract="This paper explores machine learning techniques for medical diagnosis.",
            source=PaperSource.MANUAL,
        )

        highlights = service._generate_highlights(paper, "machine learning")

        assert len(highlights) >= 1
        # Should have at least a title highlight
        title_highlights = [h for h in highlights if h.field == "title"]
        assert len(title_highlights) == 1
        assert "Machine" in title_highlights[0].snippet

    @pytest.mark.asyncio
    async def test_count_papers_without_embeddings(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test counting papers without embeddings."""
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create papers (all without embeddings in SQLite tests)
        for i in range(5):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
        await db_session.flush()

        count = await service.count_papers_without_embeddings(
            test_user.organization_id
        )
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_latest_scores(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test fetching latest scores for papers."""
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create a paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Scored Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        # Create scores
        old_score = PaperScore(
            paper_id=paper.id,
            organization_id=test_user.organization_id,
            novelty=5.0,
            ip_potential=5.0,
            marketability=5.0,
            feasibility=5.0,
            commercialization=5.0,
            overall_score=5.0,
            overall_confidence=0.8,
            model_version="test-v1",
            weights={},
            dimension_details={},
            errors=[],
        )
        db_session.add(old_score)
        await db_session.flush()

        # Fetch scores
        scores_map = await service._get_latest_scores(
            [paper.id], test_user.organization_id
        )

        assert paper.id in scores_map
        assert scores_map[paper.id].overall_score == 5.0


class TestSearchTenantIsolation:
    """Test tenant isolation in search."""

    @pytest.mark.asyncio
    async def test_search_respects_organization(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that search only returns papers from user's organization."""
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create a real organization for the other tenant
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        # Create paper for test user's org
        my_paper = Paper(
            organization_id=test_user.organization_id,
            title="My Organization Paper",
            source=PaperSource.MANUAL,
        )
        # Create paper for different org
        other_paper = Paper(
            organization_id=other_org.id,
            title="Other Organization Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([my_paper, other_paper])
        await db_session.flush()

        # Test that service respects organization
        paper = await service._get_paper(my_paper.id, test_user.organization_id)
        assert paper is not None
        assert paper.title == "My Organization Paper"

        # Should not find other org's paper
        other = await service._get_paper(other_paper.id, test_user.organization_id)
        assert other is None

    @pytest.mark.asyncio
    async def test_similar_papers_respects_organization(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that similar papers endpoint respects organization."""
        # Create a real organization for the other tenant
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        # Create papers for different orgs
        my_paper = Paper(
            organization_id=test_user.organization_id,
            title="My Paper",
            source=PaperSource.MANUAL,
        )
        other_paper = Paper(
            organization_id=other_org.id,
            title="Other Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([my_paper, other_paper])
        await db_session.flush()

        # Try to access other org's paper
        response = await client.get(
            f"/api/v1/search/similar/{other_paper.id}",
            headers=auth_headers,
        )
        # Should be 404 because paper belongs to different org
        assert response.status_code == 404


class TestSearchModes:
    """Test different search modes."""

    def test_search_mode_enum(self):
        """Test SearchMode enum values."""
        assert SearchMode.FULLTEXT.value == "fulltext"
        assert SearchMode.SEMANTIC.value == "semantic"
        assert SearchMode.HYBRID.value == "hybrid"

    def test_search_request_mode_conversion(self):
        """Test search request accepts mode strings."""
        request = SearchRequest(query="test", mode="fulltext")
        assert request.mode == SearchMode.FULLTEXT

        request = SearchRequest(query="test", mode="semantic")
        assert request.mode == SearchMode.SEMANTIC

        request = SearchRequest(query="test", mode="hybrid")
        assert request.mode == SearchMode.HYBRID


class TestHybridSearchRRF:
    """Test hybrid search with Reciprocal Rank Fusion."""

    @pytest.mark.asyncio
    async def test_rrf_score_calculation(self):
        """Test RRF score calculation logic."""
        from paper_scraper.modules.search.service import SearchService

        # RRF constant
        k = SearchService.RRF_K  # Should be 60

        # Test RRF formula: 1/(k+rank)
        rank = 1
        expected_score = 1 / (k + rank)  # 1/61 ≈ 0.0164
        assert abs(expected_score - 0.0164) < 0.001

        # Higher rank = lower score
        rank_high = 10
        score_high_rank = 1 / (k + rank_high)  # 1/70 ≈ 0.0143
        assert score_high_rank < expected_score

    @pytest.mark.asyncio
    async def test_semantic_weight_affects_results(self):
        """Test that semantic_weight parameter affects hybrid search."""
        # With semantic_weight=1.0, only semantic results should matter
        # With semantic_weight=0.0, only text results should matter

        # This is a conceptual test - actual ranking would require
        # PostgreSQL with pgvector and pg_trgm extensions
        request_text_only = SearchRequest(
            query="test", mode=SearchMode.HYBRID, semantic_weight=0.0
        )
        assert request_text_only.semantic_weight == 0.0

        request_semantic_only = SearchRequest(
            query="test", mode=SearchMode.HYBRID, semantic_weight=1.0
        )
        assert request_semantic_only.semantic_weight == 1.0

        request_balanced = SearchRequest(
            query="test", mode=SearchMode.HYBRID, semantic_weight=0.5
        )
        assert request_balanced.semantic_weight == 0.5


class TestBackfillEmbeddings:
    """Test embedding backfill functionality."""

    @pytest.mark.asyncio
    async def test_backfill_sync_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test synchronous embedding backfill endpoint."""
        # Create papers without embeddings
        for i in range(3):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Paper {i} for embedding",
                abstract=f"Abstract {i} content",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
        await db_session.flush()

        # Mock the embedding generation at the source module
        with patch(
            "paper_scraper.modules.scoring.embeddings.generate_paper_embedding"
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            response = await client.post(
                "/api/v1/search/embeddings/backfill/sync",
                params={"batch_size": 10, "max_papers": 3},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "papers_processed" in data
        assert "papers_succeeded" in data
        assert "papers_failed" in data

    @pytest.mark.asyncio
    async def test_backfill_handles_errors(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that backfill handles individual paper errors gracefully."""
        from paper_scraper.modules.search.service import SearchService

        service = SearchService(db_session)

        # Create papers
        for i in range(3):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
        await db_session.flush()

        # Mock embedding to fail on some papers
        call_count = 0

        async def mock_embed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API error")
            return [0.1] * 1536

        with patch(
            "paper_scraper.modules.scoring.embeddings.generate_paper_embedding",
            side_effect=mock_embed,
        ):
            result = await service.backfill_embeddings(
                organization_id=test_user.organization_id,
                batch_size=10,
                max_papers=3,
            )

        assert result.papers_processed == 3
        assert result.papers_succeeded == 2
        assert result.papers_failed == 1
        assert len(result.errors) == 1
