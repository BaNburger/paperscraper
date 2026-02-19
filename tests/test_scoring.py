"""Tests for scoring module."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import User
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.scoring.dimensions import (
    CommercializationDimension,
    DimensionResult,
    FeasibilityDimension,
    IPPotentialDimension,
    MarketabilityDimension,
    NoveltyDimension,
)
from paper_scraper.modules.scoring.dimensions.base import PaperContext
from paper_scraper.modules.scoring.models import PaperScore, ScoringJob
from paper_scraper.modules.scoring.orchestrator import (
    ScoringOrchestrator,
    ScoringWeights,
)
from paper_scraper.modules.scoring.schemas import ScoringWeightsSchema

# =============================================================================
# Mock LLM Responses
# =============================================================================


def mock_llm_response(dimension: str) -> dict:
    """Generate mock LLM response for a dimension."""
    responses = {
        "novelty": {
            "score": 7.5,
            "confidence": 0.85,
            "reasoning": "The paper presents novel approaches to the problem.",
            "key_factors": ["new methodology", "unique dataset", "innovative approach"],
            "comparison_to_sota": "Significantly advances state-of-the-art.",
        },
        "ip_potential": {
            "score": 8.0,
            "confidence": 0.80,
            "reasoning": "Strong patentability with clear novel elements.",
            "patentability_factors": {
                "novelty": 8.5,
                "non_obviousness": 7.5,
                "utility": 9.0,
                "enablement": 8.0,
            },
            "prior_art_risk": "low",
            "suggested_claim_scope": "broad",
        },
        "marketability": {
            "score": 6.5,
            "confidence": 0.75,
            "reasoning": "Good market potential in healthcare sector.",
            "target_industries": ["Healthcare", "Pharmaceuticals", "Biotech"],
            "market_size_estimate": "large",
            "market_timing": "good",
            "competitive_landscape": "emerging",
            "key_trends_alignment": ["personalized medicine", "AI in healthcare"],
        },
        "feasibility": {
            "score": 7.0,
            "confidence": 0.82,
            "reasoning": "Technology is at TRL 5 with clear path to product.",
            "estimated_trl": 5,
            "time_to_market_years": "2-5",
            "development_cost_estimate": "medium",
            "key_technical_risks": ["scalability", "regulatory approval"],
            "required_capabilities": ["ML expertise", "clinical trials"],
            "scalability_assessment": "moderate",
        },
        "commercialization": {
            "score": 7.5,
            "confidence": 0.78,
            "reasoning": "Multiple viable commercialization paths exist.",
            "recommended_path": "licensing",
            "alternative_paths": ["spinoff", "partnership"],
            "entry_barriers": {
                "regulatory": "medium",
                "capital": "high",
                "market_access": "medium",
                "competition": "low",
            },
            "revenue_model_suggestions": ["licensing fees", "royalties"],
            "strategic_value": "platform",
            "key_success_factors": ["clinical validation", "regulatory strategy", "partnerships"],
        },
    }
    return responses.get(dimension, {"score": 5.0, "confidence": 0.5, "reasoning": "Default"})


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = AsyncMock()

    async def mock_complete_json(prompt, system=None, temperature=None, max_tokens=None):
        # Determine which dimension based on prompt content
        if "Novelty" in prompt or "novelty" in prompt.lower():
            return mock_llm_response("novelty")
        elif "IP Potential" in prompt or "ip_potential" in prompt.lower():
            return mock_llm_response("ip_potential")
        elif "Marketability" in prompt or "marketability" in prompt.lower():
            return mock_llm_response("marketability")
        elif "Feasibility" in prompt or "feasibility" in prompt.lower():
            return mock_llm_response("feasibility")
        elif "Commercialization" in prompt or "commercialization" in prompt.lower():
            return mock_llm_response("commercialization")
        return mock_llm_response("default")

    client.complete_json = mock_complete_json
    return client


@pytest.fixture
def sample_paper_context() -> PaperContext:
    """Create a sample paper context for testing."""
    return PaperContext(
        id=uuid.uuid4(),
        title="Novel Machine Learning Approach for Drug Discovery",
        abstract="This paper presents a novel deep learning approach for identifying potential drug candidates using molecular structure analysis.",
        keywords=["machine learning", "drug discovery", "deep learning", "molecular analysis"],
        journal="Nature Biotechnology",
        publication_date="2024-01-15",
        doi="10.1234/test.123",
        citations_count=42,
        references_count=50,
    )


# =============================================================================
# Dimension Tests
# =============================================================================


class TestNoveltyDimension:
    """Test novelty dimension scorer."""

    @pytest.mark.asyncio
    async def test_parse_response(self):
        """Test parsing novelty-specific response."""
        dimension = NoveltyDimension()
        response = mock_llm_response("novelty")
        result = dimension._parse_response(response)

        assert result.dimension == "novelty"
        assert result.score == 7.5
        assert result.confidence == 0.85
        assert "novel approaches" in result.reasoning
        assert "key_factors" in result.details
        assert len(result.details["key_factors"]) == 3

    @pytest.mark.asyncio
    async def test_score_with_mock_llm(self, mock_llm_client, sample_paper_context):
        """Test scoring with mocked LLM."""
        dimension = NoveltyDimension(llm_client=mock_llm_client)
        result = await dimension.score(sample_paper_context)

        assert result.dimension == "novelty"
        assert 0 <= result.score <= 10
        assert 0 <= result.confidence <= 1


class TestIPPotentialDimension:
    """Test IP potential dimension scorer."""

    @pytest.mark.asyncio
    async def test_parse_response(self):
        """Test parsing IP potential-specific response."""
        dimension = IPPotentialDimension()
        response = mock_llm_response("ip_potential")
        result = dimension._parse_response(response)

        assert result.dimension == "ip_potential"
        assert result.score == 8.0
        assert "patentability_factors" in result.details
        assert result.details["prior_art_risk"] == "low"
        assert result.details["suggested_claim_scope"] == "broad"


class TestMarketabilityDimension:
    """Test marketability dimension scorer."""

    @pytest.mark.asyncio
    async def test_parse_response(self):
        """Test parsing marketability-specific response."""
        dimension = MarketabilityDimension()
        response = mock_llm_response("marketability")
        result = dimension._parse_response(response)

        assert result.dimension == "marketability"
        assert result.score == 6.5
        assert "Healthcare" in result.details["target_industries"]
        assert result.details["market_size_estimate"] == "large"


class TestFeasibilityDimension:
    """Test feasibility dimension scorer."""

    @pytest.mark.asyncio
    async def test_parse_response(self):
        """Test parsing feasibility-specific response."""
        dimension = FeasibilityDimension()
        response = mock_llm_response("feasibility")
        result = dimension._parse_response(response)

        assert result.dimension == "feasibility"
        assert result.score == 7.0
        assert result.details["estimated_trl"] == 5
        assert result.details["time_to_market_years"] == "2-5"


class TestCommercializationDimension:
    """Test commercialization dimension scorer."""

    @pytest.mark.asyncio
    async def test_parse_response(self):
        """Test parsing commercialization-specific response."""
        dimension = CommercializationDimension()
        response = mock_llm_response("commercialization")
        result = dimension._parse_response(response)

        assert result.dimension == "commercialization"
        assert result.score == 7.5
        assert result.details["recommended_path"] == "licensing"
        assert "spinoff" in result.details["alternative_paths"]


# =============================================================================
# Orchestrator Tests
# =============================================================================


class TestScoringOrchestrator:
    """Test scoring orchestrator."""

    def test_default_weights(self):
        """Test default equal weights (6 dimensions)."""
        weights = ScoringWeights()
        expected = 1 / 6
        assert abs(weights.novelty - expected) < 1e-10
        assert abs(weights.ip_potential - expected) < 1e-10
        assert abs(weights.marketability - expected) < 1e-10
        assert abs(weights.feasibility - expected) < 1e-10
        assert abs(weights.commercialization - expected) < 1e-10
        assert abs(weights.team_readiness - expected) < 1e-10

    def test_custom_weights_validation(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="sum to 1.0"):
            ScoringWeights(
                novelty=0.5,
                ip_potential=0.5,
                marketability=0.5,
                feasibility=0.5,
                commercialization=0.5,
                team_readiness=0.5,
            )

    def test_valid_custom_weights(self):
        """Test valid custom weights."""
        weights = ScoringWeights(
            novelty=0.25,
            ip_potential=0.20,
            marketability=0.20,
            feasibility=0.15,
            commercialization=0.10,
            team_readiness=0.10,
        )
        assert weights.novelty == 0.25
        assert weights.team_readiness == 0.10

    @pytest.mark.asyncio
    async def test_score_paper(self, sample_paper_context):
        """Test scoring a paper with mocked dimensions."""
        orchestrator = ScoringOrchestrator()

        # Mock all dimension scorers
        for name, dim in orchestrator.dimensions.items():
            dim.score = AsyncMock(
                return_value=DimensionResult(
                    dimension=name,
                    score=7.0,
                    confidence=0.8,
                    reasoning="Test reasoning",
                    details={},
                )
            )

        result = await orchestrator.score_paper(sample_paper_context)

        assert result.paper_id == sample_paper_context.id
        assert result.overall_score == 7.0  # All scores are 7.0
        assert result.overall_confidence == 0.8
        assert len(result.dimension_results) == 6

    @pytest.mark.asyncio
    async def test_score_paper_partial_dimensions(self, sample_paper_context):
        """Test scoring only specific dimensions."""
        orchestrator = ScoringOrchestrator()

        # Mock specific dimensions
        for name in ["novelty", "ip_potential"]:
            orchestrator.dimensions[name].score = AsyncMock(
                return_value=DimensionResult(
                    dimension=name,
                    score=8.0,
                    confidence=0.9,
                    reasoning="Test",
                    details={},
                )
            )

        result = await orchestrator.score_paper(
            sample_paper_context,
            dimensions=["novelty", "ip_potential"],
        )

        assert len(result.dimension_results) == 2
        assert "novelty" in result.dimension_results
        assert "ip_potential" in result.dimension_results
        assert result.overall_score == 8.0


# =============================================================================
# Schema Tests
# =============================================================================


class TestScoringSchemas:
    """Test scoring schemas."""

    def test_weights_schema_validation(self):
        """Test weight schema validation."""
        # Valid weights (6 dimensions summing to 1.0)
        valid = ScoringWeightsSchema(
            novelty=0.25,
            ip_potential=0.20,
            marketability=0.20,
            feasibility=0.15,
            commercialization=0.10,
            team_readiness=0.10,
        )
        assert valid.novelty == 0.25

    def test_weights_schema_sum_validation(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError):
            ScoringWeightsSchema(
                novelty=0.5,
                ip_potential=0.5,
                marketability=0.5,
                feasibility=0.5,
                commercialization=0.5,
            )

    def test_dimension_result_schema(self):
        """Test dimension result schema."""
        result = DimensionResult(
            dimension="novelty",
            score=7.5,
            confidence=0.85,
            reasoning="Good research",
            details={"key": "value"},
        )
        assert result.score == 7.5
        assert result.confidence == 0.85

    def test_dimension_result_validation(self):
        """Test dimension result validation."""
        with pytest.raises(ValueError):
            DimensionResult(
                dimension="novelty",
                score=15.0,  # Invalid: > 10
                confidence=0.5,
                reasoning="Test",
            )

        with pytest.raises(ValueError):
            DimensionResult(
                dimension="novelty",
                score=5.0,
                confidence=1.5,  # Invalid: > 1
                reasoning="Test",
            )


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestScoringEndpoints:
    """Test scoring API endpoints."""

    @pytest.mark.asyncio
    async def test_list_scores_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test listing scores when none exist."""
        response = await client.get("/api/v1/scoring/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_latest_score_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting score for paper with no scores."""
        response = await client.get(
            f"/api/v1/scoring/papers/{uuid.uuid4()}/scores/latest",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_scores_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing scores with data."""
        # Create test paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper",
            source=PaperSource.MANUAL,
        )
        db_session.add(paper)
        await db_session.flush()

        # Create test score
        score = PaperScore(
            paper_id=paper.id,
            organization_id=test_user.organization_id,
            novelty=7.5,
            ip_potential=8.0,
            marketability=6.5,
            feasibility=7.0,
            commercialization=7.5,
            overall_score=7.3,
            overall_confidence=0.8,
            model_version="v1.0.0",
            weights={
                "novelty": 0.2,
                "ip_potential": 0.2,
                "marketability": 0.2,
                "feasibility": 0.2,
                "commercialization": 0.2,
            },
            dimension_details={},
            errors=[],
        )
        db_session.add(score)
        await db_session.flush()

        response = await client.get("/api/v1/scoring/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["overall_score"] == 7.3

    @pytest.mark.asyncio
    async def test_list_scores_with_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing scores with min/max filters."""
        # Create test papers and scores
        for i, score_val in enumerate([5.0, 7.0, 9.0]):
            paper = Paper(
                organization_id=test_user.organization_id,
                title=f"Paper {i}",
                source=PaperSource.MANUAL,
            )
            db_session.add(paper)
            await db_session.flush()

            score = PaperScore(
                paper_id=paper.id,
                organization_id=test_user.organization_id,
                novelty=score_val,
                ip_potential=score_val,
                marketability=score_val,
                feasibility=score_val,
                commercialization=score_val,
                overall_score=score_val,
                overall_confidence=0.8,
                model_version="v1.0.0",
                weights={},
                dimension_details={},
                errors=[],
            )
            db_session.add(score)
        await db_session.flush()

        # Filter for scores >= 6.0
        response = await client.get(
            "/api/v1/scoring/",
            params={"min_score": 6.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot access scoring."""
        response = await client.get("/api/v1/scoring/")
        assert response.status_code == 401


class TestScoringJobEndpoints:
    """Test scoring job endpoints."""

    @pytest.mark.asyncio
    async def test_list_jobs_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test listing jobs when none exist."""
        response = await client.get("/api/v1/scoring/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_job_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting non-existent job."""
        response = await client.get(
            f"/api/v1/scoring/jobs/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_jobs_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing jobs with data."""
        # Create test job
        job = ScoringJob(
            organization_id=test_user.organization_id,
            job_type="batch",
            status="completed",
            paper_ids=["paper1", "paper2"],
            total_papers=2,
            completed_papers=2,
            failed_papers=0,
        )
        db_session.add(job)
        await db_session.flush()

        response = await client.get("/api/v1/scoring/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "completed"
        assert data["items"][0]["total_papers"] == 2


# =============================================================================
# LLM Client Tests
# =============================================================================


class TestLLMClient:
    """Test LLM client abstraction."""

    def test_get_llm_client_openai(self):
        """Test getting OpenAI client."""
        from paper_scraper.modules.scoring.llm_client import OpenAIClient, get_llm_client

        with patch("paper_scraper.modules.scoring.llm_client.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.OPENAI_API_KEY = MagicMock()
            mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "test-key"
            mock_settings.LLM_MODEL = "gpt-5-mini"
            mock_settings.OPENAI_ORG_ID = None

            client = get_llm_client()
            assert isinstance(client, OpenAIClient)

    def test_get_llm_client_anthropic(self):
        """Test getting Anthropic client."""
        from paper_scraper.modules.scoring.llm_client import AnthropicClient, get_llm_client

        with patch("paper_scraper.modules.scoring.llm_client.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "anthropic"
            mock_settings.ANTHROPIC_API_KEY = MagicMock()
            mock_settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "test-key"

            client = get_llm_client("anthropic")
            assert isinstance(client, AnthropicClient)

    def test_get_llm_client_invalid_provider(self):
        """Test getting client for invalid provider."""
        from paper_scraper.modules.scoring.llm_client import get_llm_client

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_client("invalid_provider")


# =============================================================================
# PaperContext Tests
# =============================================================================


class TestPaperContext:
    """Test paper context creation."""

    def test_from_paper_model(self, db_session: AsyncSession, test_user: User):
        """Test creating context from Paper model."""
        paper = Paper(
            id=uuid.uuid4(),
            organization_id=test_user.organization_id,
            title="Test Paper",
            abstract="Test abstract",
            keywords=["AI", "ML"],
            journal="Nature",
            doi="10.1234/test",
            citations_count=10,
            references_count=20,
            source=PaperSource.MANUAL,
        )

        context = PaperContext.from_paper(paper)

        assert context.title == "Test Paper"
        assert context.abstract == "Test abstract"
        assert context.keywords == ["AI", "ML"]
        assert context.journal == "Nature"
        assert context.doi == "10.1234/test"
        assert context.citations_count == 10
        assert context.references_count == 20

    def test_minimal_context(self):
        """Test creating minimal paper context."""
        context = PaperContext(
            id=uuid.uuid4(),
            title="Minimal Paper",
        )

        assert context.title == "Minimal Paper"
        assert context.abstract is None
        assert context.keywords == []
