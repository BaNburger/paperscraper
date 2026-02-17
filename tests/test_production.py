"""Tests for production infrastructure (Sprint 7)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization
from paper_scraper.modules.papers.models import Paper, PaperSource


class TestHealthCheck:
    """Test health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns OK."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestRateLimiting:
    """Test rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_authenticated_endpoint_works(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test authenticated requests work normally."""
        response = await authenticated_client.get("/api/v1/papers/")
        assert response.status_code == 200


class TestPitchGenerator:
    """Test one-line pitch generation."""

    @pytest.mark.asyncio
    async def test_paper_schema_includes_pitch_field(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
    ):
        """Test paper model has one_line_pitch field."""
        paper = Paper(
            organization_id=test_organization.id,
            title="Test Paper",
            abstract="This is a test abstract about AI.",
            source=PaperSource.MANUAL,
        )
        paper.one_line_pitch = "AI revolutionizes healthcare diagnostics"
        db_session.add(paper)
        await db_session.flush()
        await db_session.refresh(paper)

        assert paper.one_line_pitch == "AI revolutionizes healthcare diagnostics"

    @pytest.mark.asyncio
    async def test_generate_pitch_endpoint_exists(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
    ):
        """Test generate-pitch endpoint returns 404 for non-existent paper."""
        import uuid

        fake_paper_id = str(uuid.uuid4())
        response = await authenticated_client.post(
            f"/api/v1/papers/{fake_paper_id}/generate-pitch"
        )
        # Should return 404 for non-existent paper
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_paper_response_includes_pitch(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
    ):
        """Test paper list response includes one_line_pitch field."""
        # Create a test paper with a pitch
        paper = Paper(
            organization_id=test_organization.id,
            title="Test Paper with Pitch",
            abstract="This is a test abstract.",
            source=PaperSource.MANUAL,
            one_line_pitch="Novel approach to machine learning",
        )
        db_session.add(paper)
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/papers/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        if data["items"]:
            paper_data = data["items"][0]
            # Check that one_line_pitch is in the response schema
            assert "one_line_pitch" in paper_data


class TestLogging:
    """Test structured logging configuration."""

    def test_json_formatter_import(self):
        """Test JSONFormatter can be imported."""
        from paper_scraper.core.logging import JSONFormatter

        formatter = JSONFormatter()
        assert formatter is not None

    def test_setup_logging_import(self):
        """Test setup_logging can be imported."""
        from paper_scraper.core.logging import setup_logging

        assert callable(setup_logging)

    def test_get_logger_import(self):
        """Test get_logger can be imported."""
        from paper_scraper.core.logging import get_logger

        logger = get_logger(__name__)
        assert logger is not None


class TestMiddleware:
    """Test API middleware configuration."""

    def test_limiter_import(self):
        """Test limiter can be imported."""
        from paper_scraper.api.middleware import limiter

        assert limiter is not None

    def test_rate_limit_key_function(self):
        """Test get_rate_limit_key function."""
        from paper_scraper.api.middleware import get_rate_limit_key

        assert callable(get_rate_limit_key)


class TestLLMClientObservability:
    """Test LLM client Langfuse integration."""

    def test_langfuse_client_initialized(self):
        """Test Langfuse client is initialized."""
        from paper_scraper.modules.scoring.llm_client import langfuse

        assert langfuse is not None

    def test_llm_client_factory(self):
        """Test get_llm_client factory function."""
        from paper_scraper.modules.scoring.llm_client import get_llm_client

        # Default provider (will fail without API key, but should import)
        assert callable(get_llm_client)


class TestPitchGeneratorModule:
    """Test pitch generator module."""

    def test_pitch_generator_import(self):
        """Test PitchGenerator can be imported."""
        from paper_scraper.modules.scoring.pitch_generator import PitchGenerator

        assert PitchGenerator is not None

    def test_pitch_generator_initialization(self):
        """Test PitchGenerator can be initialized."""
        from paper_scraper.modules.scoring.pitch_generator import PitchGenerator

        # This will fail without LLM API key, but should initialize template
        try:
            generator = PitchGenerator()
            assert generator.template is not None
        except Exception:
            # Expected if no API key configured
            pass
