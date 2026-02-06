"""Tests for analytics module."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.projects.models import Project
from paper_scraper.modules.scoring.models import PaperScore


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test dashboard summary when no data exists."""
        response = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_papers"] == 0
        assert data["papers_this_week"] == 0
        assert data["papers_this_month"] == 0
        assert data["scored_papers"] == 0
        assert data["average_score"] is None
        assert data["total_projects"] == 0
        assert data["total_users"] >= 1  # At least the test user

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test dashboard summary with papers and scores."""
        # Create papers
        papers = []
        for i in range(3):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Test Paper {i}",
                source=PaperSource.MANUAL,
            )
            papers.append(paper)
            db_session.add(paper)
        await db_session.flush()

        # Create a score for one paper
        score = PaperScore(
            paper_id=papers[0].id,
            organization_id=test_user.organization_id,
            novelty=8.0,
            ip_potential=7.5,
            marketability=6.0,
            feasibility=8.5,
            commercialization=7.0,
            overall_score=7.4,
            overall_confidence=0.85,
            model_version="test",
        )
        db_session.add(score)
        await db_session.flush()

        response = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_papers"] == 3
        assert data["scored_papers"] == 1
        assert data["average_score"] == 7.4

    @pytest.mark.asyncio
    async def test_get_team_overview(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test team overview endpoint."""
        response = await client.get("/api/v1/analytics/team", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] >= 1
        assert "user_activity" in data
        assert isinstance(data["user_activity"], list)

    @pytest.mark.asyncio
    async def test_get_paper_analytics_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test paper analytics when no papers exist."""
        response = await client.get("/api/v1/analytics/papers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "import_trends" in data
        assert "scoring_stats" in data
        assert "top_papers" in data
        assert data["papers_with_embeddings"] == 0
        assert data["papers_without_embeddings"] == 0

    @pytest.mark.asyncio
    async def test_get_paper_analytics_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test paper analytics with papers."""
        # Create papers from different sources
        paper1 = Paper(
            organization_id=test_user.organization_id,
            title="OpenAlex Paper",
            source=PaperSource.OPENALEX,
        )
        paper2 = Paper(
            organization_id=test_user.organization_id,
            title="PubMed Paper",
            source=PaperSource.PUBMED,
        )
        paper3 = Paper(
            organization_id=test_user.organization_id,
            title="Manual Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add_all([paper1, paper2, paper3])
        await db_session.flush()

        response = await client.get("/api/v1/analytics/papers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Check source distribution
        sources = {s["source"]: s["count"] for s in data["import_trends"]["by_source"]}
        assert sources.get("openalex", 0) == 1
        assert sources.get("pubmed", 0) == 1
        assert sources.get("manual", 0) == 1

    @pytest.mark.asyncio
    async def test_paper_analytics_days_param(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test paper analytics with custom days parameter."""
        response = await client.get(
            "/api/v1/analytics/papers",
            params={"days": 30},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Test invalid days parameter
        response = await client.get(
            "/api/v1/analytics/papers",
            params={"days": 5},  # Below minimum
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_analytics_tenant_isolation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that analytics only shows data for user's organization."""
        import uuid

        # Create paper for test user's org
        paper = Paper(
            organization_id=test_user.organization_id,
            title="My Org Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)

        # Create paper for different org
        other_org_paper = Paper(
            organization_id=uuid.uuid4(),
            title="Other Org Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(other_org_paper)
        await db_session.flush()

        response = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_papers"] == 1  # Only user's org paper

    @pytest.mark.asyncio
    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot access analytics."""
        response = await client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401

        response = await client.get("/api/v1/analytics/team")
        assert response.status_code == 401

        response = await client.get("/api/v1/analytics/papers")
        assert response.status_code == 401


class TestFunnelEndpoint:
    """Test innovation funnel analytics endpoint."""

    @pytest.mark.asyncio
    async def test_get_funnel_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test funnel endpoint with no data."""
        response = await client.get("/api/v1/analytics/funnel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data
        assert isinstance(data["stages"], list)
        # Should have all 5 funnel stages even with no data
        assert len(data["stages"]) == 5
        stage_names = [s["stage"] for s in data["stages"]]
        assert "imported" in stage_names
        assert "scored" in stage_names
        assert "in_pipeline" in stage_names
        assert "contacted" in stage_names
        assert "transferred" in stage_names

    @pytest.mark.asyncio
    async def test_get_funnel_with_papers(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test funnel shows correct paper counts at each stage."""
        # Create papers
        papers = []
        for i in range(5):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Funnel Paper {i}",
                source=PaperSource.MANUAL,
            )
            papers.append(paper)
            db_session.add(paper)
        await db_session.flush()

        # Add scores to 3 papers
        for i in range(3):
            score = PaperScore(
                paper_id=papers[i].id,
                organization_id=test_user.organization_id,
                novelty=7.0,
                ip_potential=6.5,
                marketability=7.0,
                feasibility=8.0,
                commercialization=6.0,
                overall_score=6.9,
                overall_confidence=0.8,
                model_version="test",
            )
            db_session.add(score)
        await db_session.flush()

        response = await client.get("/api/v1/analytics/funnel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        stages = {s["stage"]: s["count"] for s in data["stages"]}
        assert stages["imported"] == 5
        assert stages["scored"] == 3

    @pytest.mark.asyncio
    async def test_get_funnel_with_date_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test funnel with date range parameters."""
        response = await client.get(
            "/api/v1/analytics/funnel",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestBenchmarksEndpoint:
    """Test benchmarks analytics endpoint.

    Note: Benchmarks use PostgreSQL-specific aggregate functions that don't
    work in SQLite tests. We mark these as skip for SQLite and test the
    basic authentication only.
    """

    @pytest.mark.asyncio
    async def test_get_benchmarks_requires_auth(
        self,
        client: AsyncClient,
    ):
        """Test benchmarks endpoint requires authentication."""
        response = await client.get("/api/v1/analytics/benchmarks")
        assert response.status_code == 401
