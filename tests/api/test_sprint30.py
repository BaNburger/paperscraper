"""Tests for Sprint 30 technical debt changes.

Covers:
- Badge stats CTE optimization (get_user_stats with scalar subqueries)
- Organization-level custom badges (list_badges org filtering)
- Knowledge pagination (list_personal / list_organization)
- Pipeline stage time calculation (_calculate_avg_time_per_stage)
- Search activity tracking for gamification
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.badges.models import Badge, BadgeCategory, BadgeTier, UserBadge
from paper_scraper.modules.badges.service import BadgeService
from paper_scraper.modules.knowledge.models import KnowledgeScope, KnowledgeSource, KnowledgeType
from paper_scraper.modules.knowledge.service import KnowledgeService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote  # noqa: F401 (table creation)
from paper_scraper.modules.projects.models import (
    PaperProjectStatus,
    PaperStageHistory,
    Project,
)
from paper_scraper.modules.projects.service import ProjectService
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.search.models import SearchActivity
from paper_scraper.modules.authors.models import AuthorContact  # noqa: F401 (table creation)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_paper(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> Paper:
    """Create a test paper for use in badge stats and project tests."""
    paper = Paper(
        title="Test Paper for Sprint 30",
        abstract="A paper used to verify badge stats and project calculations.",
        source="openalex",
        organization_id=test_organization.id,
        created_by_id=test_user.id,
    )
    db_session.add(paper)
    await db_session.flush()
    await db_session.refresh(paper)
    return paper


@pytest_asyncio.fixture
async def test_project(
    db_session: AsyncSession,
    test_organization: Organization,
) -> Project:
    """Create a test project with default stages."""
    project = Project(
        organization_id=test_organization.id,
        name="Sprint 30 Test Project",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def second_organization(
    db_session: AsyncSession,
) -> Organization:
    """Create a second organization for tenant isolation tests."""
    org = Organization(
        name="Other Organization",
        type="university",
    )
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


# ---------------------------------------------------------------------------
# Badge Stats CTE Optimization Tests
# ---------------------------------------------------------------------------


class TestBadgeStatsCTE:
    """Test that get_user_stats returns correct structure using the optimized
    single-query CTE approach, including the new searches_performed field."""

    @pytest.mark.asyncio
    async def test_stats_returns_all_fields_for_fresh_user(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Stats for a user with no activity should return zero counts."""
        service = BadgeService(db_session)
        stats = await service.get_user_stats(test_user.id, test_organization.id)

        assert stats.papers_imported == 0
        assert stats.papers_scored == 0
        assert stats.searches_performed == 0
        assert stats.projects_created == 0
        assert stats.notes_created == 0
        assert stats.authors_contacted == 0
        assert stats.badges_earned == 0
        assert stats.total_points == 0
        assert stats.level == 1
        assert stats.level_progress == 0.0

    @pytest.mark.asyncio
    async def test_stats_counts_search_activities(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Searches performed should reflect SearchActivity records."""
        # Arrange -- create 3 search activity records
        for i in range(3):
            activity = SearchActivity(
                user_id=test_user.id,
                organization_id=test_organization.id,
                query=f"search query {i}",
                mode="fulltext",
                results_count=i * 5,
            )
            db_session.add(activity)
        await db_session.flush()

        # Act
        service = BadgeService(db_session)
        stats = await service.get_user_stats(test_user.id, test_organization.id)

        # Assert
        assert stats.searches_performed == 3

    @pytest.mark.asyncio
    async def test_stats_counts_papers_and_scores(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
        test_paper: Paper,
    ) -> None:
        """Papers imported and scored should be counted correctly."""
        # Arrange -- add a score for the existing paper
        score = PaperScore(
            paper_id=test_paper.id,
            organization_id=test_organization.id,
            novelty=7.0,
            ip_potential=6.0,
            marketability=5.0,
            feasibility=8.0,
            commercialization=6.5,
            overall_score=6.5,
            overall_confidence=0.85,
            model_version="test-v1",
        )
        db_session.add(score)
        await db_session.flush()

        # Act
        service = BadgeService(db_session)
        stats = await service.get_user_stats(test_user.id, test_organization.id)

        # Assert
        assert stats.papers_imported == 1
        assert stats.papers_scored == 1

    @pytest.mark.asyncio
    async def test_stats_level_calculation(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Level and level_progress should be derived from total_points."""
        # Arrange -- award a badge worth 25 points
        badge = Badge(
            name="Level Test Badge",
            description="For testing level calculation",
            icon="test",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.SILVER,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=25,
        )
        db_session.add(badge)
        await db_session.flush()

        ub = UserBadge(
            user_id=test_user.id,
            badge_id=badge.id,
            progress=1,
        )
        db_session.add(ub)
        await db_session.flush()

        # Act
        service = BadgeService(db_session)
        stats = await service.get_user_stats(test_user.id, test_organization.id)

        # Assert -- 25 points: level = 25//100 + 1 = 1, progress = 0.25
        assert stats.total_points == 25
        assert stats.level == 1
        assert stats.level_progress == 0.25
        assert stats.badges_earned == 1


# ---------------------------------------------------------------------------
# Badge Stats API Endpoint Test
# ---------------------------------------------------------------------------


class TestBadgeStatsEndpoint:
    """Test the /api/v1/badges/me/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_endpoint_returns_searches_performed(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """The stats endpoint should include searches_performed in its response."""
        # Arrange -- insert search activities directly
        for i in range(2):
            db_session.add(SearchActivity(
                user_id=test_user.id,
                organization_id=test_organization.id,
                query=f"api test query {i}",
                mode="hybrid",
                results_count=10,
            ))
        await db_session.flush()

        # Act
        response = await authenticated_client.get("/api/v1/badges/me/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "searches_performed" in data
        assert data["searches_performed"] == 2
        assert "level" in data
        assert "level_progress" in data
        assert "papers_imported" in data


# ---------------------------------------------------------------------------
# Organization-Level Custom Badges Tests
# ---------------------------------------------------------------------------


class TestBadgeOrganizationFiltering:
    """Test that list_badges filters by organization, showing system-wide
    badges plus the requesting org's custom badges."""

    @pytest.mark.asyncio
    async def test_list_badges_returns_system_badges(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
    ) -> None:
        """Listing badges with an org_id should include system badges (org_id=NULL)."""
        service = BadgeService(db_session)
        result = await service.list_badges(organization_id=test_organization.id)

        # Default seed produces 13 system badges
        assert result.total >= 13
        assert all(isinstance(b.name, str) for b in result.items)

    @pytest.mark.asyncio
    async def test_list_badges_includes_own_custom_badge(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
    ) -> None:
        """Custom badge belonging to the org should appear in the list."""
        # Arrange -- seed defaults first, then add a custom badge
        service = BadgeService(db_session)
        await service.seed_badges()

        custom = Badge(
            name="Org Custom Badge",
            description="A custom badge for this org only",
            icon="star",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.GOLD,
            criteria={"action": "custom_action", "count": 1},
            threshold=1,
            points=50,
            organization_id=test_organization.id,
            is_custom=True,
        )
        db_session.add(custom)
        await db_session.flush()

        # Act
        result = await service.list_badges(organization_id=test_organization.id)

        # Assert -- should include system badges + our custom one
        names = {b.name for b in result.items}
        assert "Org Custom Badge" in names
        assert "First Import" in names  # system badge

    @pytest.mark.asyncio
    async def test_list_badges_excludes_other_org_custom_badge(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        second_organization: Organization,
    ) -> None:
        """Custom badge belonging to another org should not appear."""
        service = BadgeService(db_session)
        await service.seed_badges()

        other_custom = Badge(
            name="Other Org Badge",
            description="Should be invisible to test_organization",
            icon="lock",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.BRONZE,
            criteria={"action": "other", "count": 1},
            threshold=1,
            points=10,
            organization_id=second_organization.id,
            is_custom=True,
        )
        db_session.add(other_custom)
        await db_session.flush()

        # Act -- list for test_organization
        result = await service.list_badges(organization_id=test_organization.id)

        # Assert
        names = {b.name for b in result.items}
        assert "Other Org Badge" not in names

    @pytest.mark.asyncio
    async def test_list_badges_endpoint_filters_by_org(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        second_organization: Organization,
    ) -> None:
        """The GET /badges/ endpoint should only return badges visible to the user's org."""
        # Seed system badges first
        service = BadgeService(db_session)
        await service.seed_badges()

        # Arrange -- create a badge for the other org
        other_badge = Badge(
            name="Hidden Org Badge",
            description="Not visible through the API",
            icon="eye-off",
            category=BadgeCategory.SCORING,
            tier=BadgeTier.SILVER,
            criteria={"action": "hidden", "count": 1},
            threshold=1,
            points=20,
            organization_id=second_organization.id,
            is_custom=True,
        )
        db_session.add(other_badge)
        await db_session.flush()

        # Act
        response = await authenticated_client.get("/api/v1/badges/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        names = {item["name"] for item in data["items"]}
        assert "Hidden Org Badge" not in names
        # System badges should still be present
        assert data["total"] >= 13


# ---------------------------------------------------------------------------
# Knowledge Pagination Tests
# ---------------------------------------------------------------------------


class TestKnowledgePagination:
    """Test that list_personal and list_organization accept page/page_size
    and return proper pagination metadata."""

    @pytest.mark.asyncio
    async def test_list_personal_default_pagination(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Default pagination should return page=1, page_size=50."""
        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=test_user.id,
            organization_id=test_organization.id,
        )

        assert result.page == 1
        assert result.page_size == 50
        assert result.total == 0
        assert result.pages == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_personal_with_data_and_pagination(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Paginating personal knowledge sources should return correct slices."""
        # Arrange -- create 5 personal knowledge sources
        for i in range(5):
            source = KnowledgeSource(
                organization_id=test_organization.id,
                user_id=test_user.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Personal Source {i}",
                content=f"Content for personal source {i}",
                tags=[],
            )
            db_session.add(source)
        await db_session.flush()

        service = KnowledgeService(db_session)

        # Act -- page 1, size 2
        result_p1 = await service.list_personal(
            user_id=test_user.id,
            organization_id=test_organization.id,
            page=1,
            page_size=2,
        )

        # Assert
        assert result_p1.total == 5
        assert result_p1.page == 1
        assert result_p1.page_size == 2
        assert result_p1.pages == 3  # ceil(5/2) = 3
        assert len(result_p1.items) == 2

        # Act -- page 3 (last page, only 1 item)
        result_p3 = await service.list_personal(
            user_id=test_user.id,
            organization_id=test_organization.id,
            page=3,
            page_size=2,
        )

        assert result_p3.page == 3
        assert len(result_p3.items) == 1

    @pytest.mark.asyncio
    async def test_list_organization_pagination(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
    ) -> None:
        """Paginating organization knowledge sources works correctly."""
        # Arrange -- create 3 org-level sources
        for i in range(3):
            source = KnowledgeSource(
                organization_id=test_organization.id,
                user_id=None,
                scope=KnowledgeScope.ORGANIZATION,
                type=KnowledgeType.INDUSTRY_CONTEXT,
                title=f"Org Source {i}",
                content=f"Organization knowledge content {i}",
                tags=["industry"],
            )
            db_session.add(source)
        await db_session.flush()

        service = KnowledgeService(db_session)

        # Act
        result = await service.list_organization(
            organization_id=test_organization.id,
            page=1,
            page_size=2,
        )

        # Assert
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 2
        assert result.pages == 2  # ceil(3/2) = 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_list_personal_endpoint_accepts_pagination_params(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """The GET /knowledge/personal endpoint should accept page and page_size."""
        response = await authenticated_client.get(
            "/api/v1/knowledge/personal",
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert "pages" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_organization_endpoint_accepts_pagination_params(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """The GET /knowledge/organization endpoint should accept page and page_size."""
        response = await authenticated_client.get(
            "/api/v1/knowledge/organization",
            params={"page": 2, "page_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5
        assert "pages" in data

    @pytest.mark.asyncio
    async def test_list_personal_invalid_page_rejected(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """page < 1 should be rejected by the endpoint validation."""
        response = await authenticated_client.get(
            "/api/v1/knowledge/personal",
            params={"page": 0},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_personal_page_size_too_large_rejected(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """page_size > 100 should be rejected by the endpoint validation."""
        response = await authenticated_client.get(
            "/api/v1/knowledge/personal",
            params={"page_size": 101},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Pipeline Stage Time Calculation Tests
# ---------------------------------------------------------------------------


class TestPipelineStageTimeCalculation:
    """Test _calculate_avg_time_per_stage computes average hours per stage
    from PaperStageHistory records."""

    @pytest.mark.asyncio
    async def test_avg_time_empty_project(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_project: Project,
    ) -> None:
        """A project with no papers should return an empty dict."""
        service = ProjectService(db_session)
        result = await service._calculate_avg_time_per_stage(test_project.id)
        assert result == {}

    @pytest.mark.asyncio
    async def test_avg_time_single_transition(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_project: Project,
        test_paper: Paper,
    ) -> None:
        """A single stage transition should produce a correct average."""
        # Arrange -- add paper to project
        status = PaperProjectStatus(
            paper_id=test_paper.id,
            project_id=test_project.id,
            stage="screening",
            position=1,
        )
        db_session.add(status)
        await db_session.flush()

        now = datetime.now(timezone.utc)

        # Create two history entries: inbox -> screening (2 hours apart)
        h1 = PaperStageHistory(
            paper_project_status_id=status.id,
            from_stage=None,
            to_stage="inbox",
            created_at=now - timedelta(hours=2),
        )
        h2 = PaperStageHistory(
            paper_project_status_id=status.id,
            from_stage="inbox",
            to_stage="screening",
            created_at=now,
        )
        db_session.add_all([h1, h2])
        await db_session.flush()

        # Act
        service = ProjectService(db_session)
        result = await service._calculate_avg_time_per_stage(test_project.id)

        # Assert -- paper spent 2 hours in "inbox"
        assert "inbox" in result
        assert abs(result["inbox"] - 2.0) < 0.1

    @pytest.mark.asyncio
    async def test_avg_time_multiple_transitions(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_project: Project,
        test_paper: Paper,
    ) -> None:
        """Multiple transitions should produce correct averages across stages."""
        status = PaperProjectStatus(
            paper_id=test_paper.id,
            project_id=test_project.id,
            stage="evaluation",
            position=1,
        )
        db_session.add(status)
        await db_session.flush()

        now = datetime.now(timezone.utc)

        # inbox (3h) -> screening (1h) -> evaluation
        h1 = PaperStageHistory(
            paper_project_status_id=status.id,
            from_stage=None,
            to_stage="inbox",
            created_at=now - timedelta(hours=4),
        )
        h2 = PaperStageHistory(
            paper_project_status_id=status.id,
            from_stage="inbox",
            to_stage="screening",
            created_at=now - timedelta(hours=1),
        )
        h3 = PaperStageHistory(
            paper_project_status_id=status.id,
            from_stage="screening",
            to_stage="evaluation",
            created_at=now,
        )
        db_session.add_all([h1, h2, h3])
        await db_session.flush()

        service = ProjectService(db_session)
        result = await service._calculate_avg_time_per_stage(test_project.id)

        # inbox duration: 3 hours, screening duration: 1 hour
        assert "inbox" in result
        assert abs(result["inbox"] - 3.0) < 0.1
        assert "screening" in result
        assert abs(result["screening"] - 1.0) < 0.1
        # evaluation has no subsequent transition so it should NOT appear
        assert "evaluation" not in result

    @pytest.mark.asyncio
    async def test_avg_time_statistics_endpoint(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_project: Project,
    ) -> None:
        """The project statistics endpoint should include avg_time_per_stage."""
        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/statistics"
        )

        assert response.status_code == 200
        data = response.json()
        assert "avg_time_per_stage" in data
        assert isinstance(data["avg_time_per_stage"], dict)
        assert "papers_by_stage" in data
        assert data["total_papers"] == 0


# ---------------------------------------------------------------------------
# Search Activity Tracking Tests
# ---------------------------------------------------------------------------


class TestSearchActivityTracking:
    """Test that SearchActivity records are created when searching and
    that they feed into badge stats."""

    @pytest.mark.asyncio
    async def test_search_activity_model_persists(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """SearchActivity records should persist correctly."""
        activity = SearchActivity(
            user_id=test_user.id,
            organization_id=test_organization.id,
            query="CRISPR gene editing",
            mode="hybrid",
            results_count=42,
            search_time_ms=123.45,
        )
        db_session.add(activity)
        await db_session.flush()
        await db_session.refresh(activity)

        assert activity.id is not None
        assert activity.query == "CRISPR gene editing"
        assert activity.mode == "hybrid"
        assert activity.results_count == 42
        assert activity.search_time_ms == 123.45
        assert activity.created_at is not None

    @pytest.mark.asyncio
    async def test_search_activity_feeds_badge_stats(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Badge stats searches_performed should match SearchActivity count."""
        # Arrange -- 5 searches
        for i in range(5):
            db_session.add(SearchActivity(
                user_id=test_user.id,
                organization_id=test_organization.id,
                query=f"query {i}",
                mode="fulltext",
                results_count=0,
            ))
        await db_session.flush()

        # Act
        service = BadgeService(db_session)
        stats = await service.get_user_stats(test_user.id, test_organization.id)

        # Assert
        assert stats.searches_performed == 5
