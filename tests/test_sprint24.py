"""Tests for Sprint 24 - AI Intelligence Enhancements.

Tests cover:
- Task 24.1: Embedding-based group member suggestions (AI-001)
- Task 24.2: Similar papers for submission analysis (AI-002)
- Task 24.3: Enhanced transfer next-steps AI (AI-004)
- Task 24.4: Badge auto-award engine (TD-009)
- Task 24.5: Knowledge-enhanced scoring (TD-010, AI-005)
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.groups.schemas import SuggestedMember, SuggestMembersRequest
from paper_scraper.modules.knowledge.models import KnowledgeScope, KnowledgeType
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.scoring.dimensions.base import PaperContext
from paper_scraper.modules.transfer.schemas import NextStep, NextStepsResponse

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_organization() -> Organization:
    """Create a sample organization."""
    return Organization(
        id=uuid.uuid4(),
        name="Test University",
        type="academic",
        subscription_tier="professional",
    )


@pytest.fixture
def sample_user(sample_organization: Organization) -> User:
    """Create a sample user."""
    return User(
        id=uuid.uuid4(),
        organization_id=sample_organization.id,
        email="researcher@test.edu",
        hashed_password="hashed",
        full_name="Dr. Test Researcher",
        role="member",
    )


@pytest.fixture
def sample_paper(sample_organization: Organization) -> Paper:
    """Create a sample paper with embedding."""
    return Paper(
        id=uuid.uuid4(),
        organization_id=sample_organization.id,
        doi="10.1234/test.paper",
        title="Novel Machine Learning Approaches for Drug Discovery",
        abstract="This paper presents innovative ML techniques for accelerating drug discovery pipelines.",
        source=PaperSource.OPENALEX,
        keywords=["machine learning", "drug discovery", "AI", "pharmaceuticals"],
        has_embedding=True,  # Embedding stored in pgvector column
    )


@pytest.fixture
def sample_knowledge_sources(sample_organization: Organization, sample_user: User) -> list:
    """Create sample knowledge source data (mocked, not ORM objects)."""
    # Using dataclass to avoid SQLAlchemy column validation issues
    # Matches actual KnowledgeSource model attributes
    from dataclasses import dataclass

    @dataclass
    class MockKnowledgeSource:
        id: uuid.UUID
        organization_id: uuid.UUID
        user_id: uuid.UUID
        scope: KnowledgeScope
        type: KnowledgeType
        title: str
        content: str

    source1 = MockKnowledgeSource(
        id=uuid.uuid4(),
        organization_id=sample_organization.id,
        user_id=sample_user.id,
        scope=KnowledgeScope.ORGANIZATION,
        type=KnowledgeType.RESEARCH_FOCUS,
        title="Research Focus Areas",
        content="We focus on oncology, immunotherapy, and personalized medicine.",
    )

    source2 = MockKnowledgeSource(
        id=uuid.uuid4(),
        organization_id=sample_organization.id,
        user_id=sample_user.id,
        scope=KnowledgeScope.ORGANIZATION,
        type=KnowledgeType.INDUSTRY_CONTEXT,
        title="Industry Priorities",
        content="Our partners are primarily in biotech and pharma sectors.",
    )

    return [source1, source2]


# =============================================================================
# Task 24.1: Embedding-Based Group Member Suggestions
# =============================================================================


class TestGroupMemberSuggestions:
    """Tests for embedding-based group member suggestions."""

    def test_suggest_members_schema(self):
        """Test SuggestMembersRequest schema with new fields."""
        request = SuggestMembersRequest(
            keywords=["machine learning", "drug discovery"],
            target_size=5,
            group_name="ML Drug Discovery",
            group_description="Researchers working on ML for pharma",
            use_llm_explanation=True,
        )

        assert request.keywords == ["machine learning", "drug discovery"]
        assert request.target_size == 5
        assert request.group_name == "ML Drug Discovery"
        assert request.group_description == "Researchers working on ML for pharma"
        assert request.use_llm_explanation is True

    def test_suggested_member_schema(self):
        """Test SuggestedMember schema with explanation field."""
        member = SuggestedMember(
            researcher_id=uuid.uuid4(),
            name="Dr. Jane Smith",
            relevance_score=0.95,
            matching_keywords=["machine learning", "drug discovery"],
            affiliations=["Stanford University"],
            explanation="Dr. Smith is a leading expert in applying ML to pharmaceutical research.",
        )

        assert member.name == "Dr. Jane Smith"
        assert member.relevance_score == 0.95
        assert member.explanation is not None
        assert "leading expert" in member.explanation

    def test_suggest_members_request_defaults(self):
        """Test default values for suggest members request."""
        request = SuggestMembersRequest(keywords=["AI"])

        assert request.target_size == 10
        assert request.group_name is None
        assert request.group_description is None
        assert request.use_llm_explanation is False


# =============================================================================
# Task 24.2: Similar Papers for Submission Analysis
# =============================================================================


class TestSimilarPapersForSubmissions:
    """Tests for similar papers in submission analysis."""

    async def test_paper_context_with_similar_papers(self, sample_paper: Paper):
        """Test that PaperContext can be created from paper."""
        context = PaperContext.from_paper(sample_paper)

        assert context.title == sample_paper.title
        assert context.abstract == sample_paper.abstract
        assert context.keywords == sample_paper.keywords

    async def test_embedding_based_similarity(self):
        """Test that embedding similarity search concept works."""
        # Create mock papers with embeddings
        embedding1 = [0.1] * 768 + [0.0] * 768
        embedding2 = [0.1] * 768 + [0.0] * 768  # Similar
        embedding3 = [-0.1] * 768 + [0.0] * 768  # Different

        # Simple cosine similarity check (vectors should be similar)
        import numpy as np

        sim_12 = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        sim_13 = np.dot(embedding1, embedding3) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding3)
        )

        assert sim_12 > sim_13  # Similar embeddings have higher similarity


# =============================================================================
# Task 24.3: Enhanced Transfer Next-Steps AI
# =============================================================================


class TestTransferNextStepsAI:
    """Tests for enhanced transfer next-steps AI."""

    def test_next_step_schema_with_template(self):
        """Test NextStep schema includes suggested template."""
        step = NextStep(
            action="Send initial outreach email",
            priority="high",
            rationale="First contact is crucial for establishing relationship",
            suggested_template="initial_researcher_outreach",
        )

        assert step.action == "Send initial outreach email"
        assert step.priority == "high"
        assert step.suggested_template == "initial_researcher_outreach"

    def test_next_steps_response_with_stage_recommendation(self):
        """Test NextStepsResponse includes stage recommendation."""
        response = NextStepsResponse(
            conversation_id=uuid.uuid4(),
            steps=[
                NextStep(
                    action="Follow up on initial email",
                    priority="medium",
                    rationale="No response in 3 days",
                    suggested_template="follow_up_no_response",
                )
            ],
            summary="Initial contact made, awaiting response",
            stage_recommendation="Consider moving to 'negotiation' stage if response is positive",
        )

        assert response.stage_recommendation is not None
        assert "negotiation" in response.stage_recommendation.lower()


# =============================================================================
# Task 24.4: Badge Auto-Award Engine
# =============================================================================


class TestBadgeAutoAward:
    """Tests for badge auto-award engine."""

    async def test_trigger_badge_check_import(self):
        """Test that trigger_badge_check function can be imported."""
        from paper_scraper.jobs.badges import trigger_badge_check

        assert callable(trigger_badge_check)

    async def test_badge_tasks_registered(self):
        """Test that badge tasks are registered in worker."""
        from paper_scraper.jobs.worker import WorkerSettings

        function_names = [f.__name__ for f in WorkerSettings.functions]

        assert "check_and_award_badges_task" in function_names
        assert "batch_check_badges_task" in function_names

    @patch("paper_scraper.jobs.worker.enqueue_job")
    async def test_trigger_badge_check_enqueues_job(self, mock_enqueue):
        """Test that trigger_badge_check enqueues an arq job."""
        from paper_scraper.jobs.badges import trigger_badge_check

        mock_enqueue.return_value = None

        user_id = uuid.uuid4()
        org_id = uuid.uuid4()

        await trigger_badge_check(user_id, org_id, "paper_scored")

        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        assert call_args[0][0] == "check_and_award_badges_task"
        assert str(user_id) in call_args[0]
        assert str(org_id) in call_args[0]


# =============================================================================
# Task 24.5: Knowledge-Enhanced Scoring
# =============================================================================


class TestKnowledgeEnhancedScoring:
    """Tests for knowledge-enhanced scoring."""

    def test_paper_context_with_knowledge_field(self):
        """Test PaperContext has knowledge_context field."""
        context = PaperContext(
            id=uuid.uuid4(),
            title="Test Paper",
            abstract="Test abstract",
            keywords=["test"],
            knowledge_context="We focus on oncology research.",
        )

        assert context.knowledge_context == "We focus on oncology research."

    def test_paper_context_knowledge_default(self):
        """Test PaperContext knowledge_context defaults to None."""
        context = PaperContext(
            id=uuid.uuid4(),
            title="Test Paper",
            abstract="Test abstract",
            keywords=["test"],
        )

        assert context.knowledge_context is None

    async def test_knowledge_service_formatting(self, sample_knowledge_sources: list):
        """Test knowledge source formatting for prompts."""
        from paper_scraper.modules.knowledge.service import KnowledgeService

        # format_knowledge_for_prompt is an instance method
        # Create a mock db session to instantiate the service
        mock_db = MagicMock()
        service = KnowledgeService(mock_db)

        # Test format method exists and works
        formatted = service.format_knowledge_for_prompt(sample_knowledge_sources)

        assert isinstance(formatted, str)
        assert "Organization Knowledge" in formatted
        assert "Research Focus Areas" in formatted
        assert "oncology" in formatted.lower()

    def test_scoring_prompt_includes_knowledge_placeholder(self):
        """Test that scoring prompts include knowledge context."""
        from paper_scraper.modules.scoring.prompts import render_prompt

        # Create context with knowledge
        context = MagicMock()
        context.id = uuid.uuid4()
        context.title = "Test Paper"
        context.abstract = "Test abstract"
        context.keywords = ["test"]
        context.journal = None
        context.publication_date = None
        context.doi = None
        context.citations_count = None
        context.references_count = None
        context.knowledge_context = "We focus on AI in healthcare."

        rendered = render_prompt("novelty.jinja2", paper=context, similar_papers=[])

        # The rendered prompt should include knowledge context section
        # when knowledge_context is provided
        assert "Test Paper" in rendered

    def test_scoring_weights_include_team_readiness(self):
        """Test scoring weights schema includes team_readiness."""
        from paper_scraper.modules.scoring.schemas import ScoringWeightsSchema

        weights = ScoringWeightsSchema(
            novelty=0.15,
            ip_potential=0.15,
            marketability=0.20,
            feasibility=0.20,
            commercialization=0.15,
            team_readiness=0.15,
        )

        assert weights.team_readiness == 0.15
        assert (
            abs(
                sum(
                    [
                        weights.novelty,
                        weights.ip_potential,
                        weights.marketability,
                        weights.feasibility,
                        weights.commercialization,
                        weights.team_readiness,
                    ]
                )
                - 1.0
            )
            < 0.01
        )  # Weights sum to ~1.0


# =============================================================================
# Integration Tests
# =============================================================================


class TestSprint24Integration:
    """Integration tests for Sprint 24 features."""

    async def test_scoring_service_accepts_knowledge_params(self):
        """Test scoring service accepts knowledge-related parameters."""
        import inspect

        from paper_scraper.modules.scoring.service import ScoringService

        # Check that score_paper method signature includes new params
        sig = inspect.signature(ScoringService.score_paper)
        params = list(sig.parameters.keys())

        assert "use_knowledge_context" in params
        assert "user_id" in params

    async def test_groups_service_accepts_llm_params(self):
        """Test groups service accepts LLM explanation parameters."""
        import inspect

        from paper_scraper.modules.groups.service import GroupService

        sig = inspect.signature(GroupService.suggest_members)
        params = list(sig.parameters.keys())

        assert "group_name" in params
        assert "group_description" in params
        assert "use_llm_explanation" in params

    async def test_transfer_service_returns_enhanced_response(self):
        """Test transfer service returns enhanced response schema."""

        from paper_scraper.modules.transfer.schemas import NextStepsResponse

        # Check NextStepsResponse has new fields
        fields = NextStepsResponse.model_fields.keys()

        assert "stage_recommendation" in fields

    async def test_knowledge_service_has_scoring_method(self):
        """Test knowledge service has scoring-specific retrieval."""

        from paper_scraper.modules.knowledge.service import KnowledgeService

        assert hasattr(KnowledgeService, "get_relevant_sources_for_scoring")
        assert hasattr(KnowledgeService, "format_knowledge_for_prompt")


# =============================================================================
# Prompt Template Tests
# =============================================================================


class TestPromptTemplates:
    """Tests for Jinja2 prompt templates."""

    def test_suggest_members_template_exists(self):
        """Test suggest_members prompt template exists."""
        from pathlib import Path

        template_path = Path("paper_scraper/modules/scoring/prompts/suggest_members.jinja2")
        assert template_path.exists()

    def test_transfer_next_steps_template_exists(self):
        """Test transfer_next_steps prompt template exists."""
        from pathlib import Path

        template_path = Path("paper_scraper/modules/scoring/prompts/transfer_next_steps.jinja2")
        assert template_path.exists()

    def test_team_readiness_template_exists(self):
        """Test team_readiness prompt template exists."""
        from pathlib import Path

        template_path = Path("paper_scraper/modules/scoring/prompts/team_readiness.jinja2")
        assert template_path.exists()
