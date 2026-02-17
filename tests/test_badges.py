"""Tests for badges and gamification module."""

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.badges.models import (
    Badge,
    BadgeCategory,
    BadgeTier,
    UserBadge,
)
from paper_scraper.modules.badges.service import DEFAULT_BADGES, BadgeService
from paper_scraper.modules.papers.models import Paper, PaperSource

# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def badge_service(db_session: AsyncSession) -> BadgeService:
    """Create a badge service instance for testing."""
    return BadgeService(db_session)


@pytest_asyncio.fixture
async def test_badge(db_session: AsyncSession) -> Badge:
    """Create a single test badge."""
    badge = Badge(
        name="Test Badge",
        description="A test badge",
        icon="star",
        category=BadgeCategory.MILESTONE,
        tier=BadgeTier.BRONZE,
        criteria={"action": "test_action", "count": 1},
        threshold=1,
        points=10,
    )
    db_session.add(badge)
    await db_session.flush()
    await db_session.refresh(badge)
    return badge


@pytest_asyncio.fixture
async def user_badge(
    db_session: AsyncSession,
    test_user: User,
    test_badge: Badge,
) -> UserBadge:
    """Create a user badge."""
    ub = UserBadge(
        user_id=test_user.id,
        badge_id=test_badge.id,
        progress=1,
    )
    db_session.add(ub)
    await db_session.flush()
    await db_session.refresh(ub)
    return ub


@pytest_asyncio.fixture
async def seeded_badges(
    badge_service: BadgeService,
) -> int:
    """Seed default badges."""
    return await badge_service.seed_badges()


@pytest_asyncio.fixture
async def papers_for_stats(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> list[Paper]:
    """Create test papers for stats calculation."""
    papers = []
    for i in range(3):
        paper = Paper(
            title=f"Test Paper {i}",
            source=PaperSource.DOI,
            organization_id=test_organization.id,
            created_by_id=test_user.id,
        )
        db_session.add(paper)
        papers.append(paper)
    await db_session.flush()
    for p in papers:
        await db_session.refresh(p)
    return papers


# =============================================================================
# Service Tests
# =============================================================================


class TestBadgeService:
    """Tests for BadgeService class."""

    async def test_seed_badges(
        self,
        badge_service: BadgeService,
        db_session: AsyncSession,
    ):
        """Test that default badges are seeded."""
        count = await badge_service.seed_badges()
        assert count == len(DEFAULT_BADGES)

        result = await db_session.execute(select(Badge))
        badges = list(result.scalars().all())
        assert len(badges) == len(DEFAULT_BADGES)

    async def test_seed_badges_idempotent(
        self,
        badge_service: BadgeService,
    ):
        """Test that seeding twice does not duplicate badges."""
        first = await badge_service.seed_badges()
        second = await badge_service.seed_badges()

        assert first == len(DEFAULT_BADGES)
        assert second == 0

    async def test_seed_badges_does_not_run_when_badges_exist(
        self,
        badge_service: BadgeService,
        test_badge: Badge,
    ):
        """Test that seeding is skipped when badges already exist."""
        count = await badge_service.seed_badges()
        assert count == 0

    async def test_list_badges(
        self,
        badge_service: BadgeService,
        seeded_badges: int,
    ):
        """Test listing all available badges."""
        response = await badge_service.list_badges()
        assert response.total == len(DEFAULT_BADGES)
        assert len(response.items) == len(DEFAULT_BADGES)

    async def test_list_badges_seeds_automatically(
        self,
        badge_service: BadgeService,
    ):
        """Test that listing badges auto-seeds if empty."""
        response = await badge_service.list_badges()
        assert response.total == len(DEFAULT_BADGES)

    async def test_get_user_badges_empty(
        self,
        badge_service: BadgeService,
        test_user: User,
    ):
        """Test getting badges for user with none earned."""
        response = await badge_service.get_user_badges(test_user.id)
        assert response.total == 0
        assert response.total_points == 0
        assert response.items == []

    async def test_get_user_badges(
        self,
        badge_service: BadgeService,
        test_user: User,
        user_badge: UserBadge,
    ):
        """Test getting user's earned badges."""
        response = await badge_service.get_user_badges(test_user.id)
        assert response.total == 1
        assert response.total_points == 10
        assert response.items[0].badge.name == "Test Badge"
        assert response.items[0].progress == 1

    async def test_get_user_stats_empty(
        self,
        badge_service: BadgeService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test user stats when no activity exists."""
        stats = await badge_service.get_user_stats(
            test_user.id, test_organization.id
        )
        assert stats.papers_imported == 0
        assert stats.papers_scored == 0
        assert stats.projects_created == 0
        assert stats.notes_created == 0
        assert stats.authors_contacted == 0
        assert stats.badges_earned == 0
        assert stats.total_points == 0
        assert stats.level == 1
        assert stats.level_progress == 0.0

    async def test_get_user_stats_with_data(
        self,
        badge_service: BadgeService,
        test_user: User,
        test_organization: Organization,
        papers_for_stats: list[Paper],
    ):
        """Test user stats with some papers imported."""
        stats = await badge_service.get_user_stats(
            test_user.id, test_organization.id
        )
        assert stats.papers_imported == 3

    async def test_get_user_stats_level_calculation(
        self,
        badge_service: BadgeService,
        test_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test that level is calculated correctly from points."""
        # Create badges worth 250 points total
        badge1 = Badge(
            name="Big Badge",
            description="x",
            icon="star",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.GOLD,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=250,
        )
        db_session.add(badge1)
        await db_session.flush()
        await db_session.refresh(badge1)

        ub = UserBadge(
            user_id=test_user.id,
            badge_id=badge1.id,
            progress=1,
        )
        db_session.add(ub)
        await db_session.flush()

        stats = await badge_service.get_user_stats(
            test_user.id, test_organization.id
        )
        assert stats.total_points == 250
        # 250 // 100 + 1 = 3
        assert stats.level == 3
        # 250 % 100 / 100 = 0.5
        assert stats.level_progress == 0.5

    async def test_check_and_award_badges_no_progress(
        self,
        badge_service: BadgeService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test badge checking when user has no progress."""
        awarded = await badge_service.check_and_award_badges(
            test_user.id, test_organization.id
        )
        # No papers, so no import badges earned
        assert len(awarded) == 0

    async def test_check_and_award_badges_with_papers(
        self,
        badge_service: BadgeService,
        test_user: User,
        test_organization: Organization,
        papers_for_stats: list[Paper],
    ):
        """Test that importing papers triggers import badges."""
        awarded = await badge_service.check_and_award_badges(
            test_user.id, test_organization.id
        )
        # Should earn "First Import" (threshold=1)
        badge_names = [b.name for b in awarded]
        assert "First Import" in badge_names

    async def test_check_and_award_badges_not_duplicate(
        self,
        badge_service: BadgeService,
        test_user: User,
        test_organization: Organization,
        papers_for_stats: list[Paper],
    ):
        """Test that already-earned badges are not re-awarded."""
        await badge_service.check_and_award_badges(
            test_user.id, test_organization.id
        )
        second_award = await badge_service.check_and_award_badges(
            test_user.id, test_organization.id
        )
        assert len(second_award) == 0


# =============================================================================
# API Router Tests
# =============================================================================


class TestBadgesRouter:
    """Tests for badges API endpoints."""

    async def test_list_badges(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing all badges via API."""
        response = await authenticated_client.get("/api/v1/badges/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == len(DEFAULT_BADGES)

    async def test_get_my_badges_empty(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting my badges when none earned."""
        response = await authenticated_client.get("/api/v1/badges/me")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["total_points"] == 0
        assert data["items"] == []

    async def test_get_my_badges(
        self,
        authenticated_client: AsyncClient,
        user_badge: UserBadge,
    ):
        """Test getting my badges when some earned."""
        response = await authenticated_client.get("/api/v1/badges/me")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["total_points"] == 10
        assert data["items"][0]["badge"]["name"] == "Test Badge"

    async def test_get_my_stats(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting my stats via API."""
        response = await authenticated_client.get("/api/v1/badges/me/stats")
        assert response.status_code == 200
        data = response.json()
        assert "papers_imported" in data
        assert "papers_scored" in data
        assert "level" in data
        assert "level_progress" in data
        assert data["level"] >= 1

    async def test_get_my_stats_with_papers(
        self,
        authenticated_client: AsyncClient,
        papers_for_stats: list[Paper],
    ):
        """Test stats reflect imported papers."""
        response = await authenticated_client.get("/api/v1/badges/me/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["papers_imported"] == 3

    async def test_check_badges(
        self,
        authenticated_client: AsyncClient,
        papers_for_stats: list[Paper],
    ):
        """Test checking and awarding badges via API."""
        response = await authenticated_client.post("/api/v1/badges/me/check")
        assert response.status_code == 200
        data = response.json()
        # Should have earned at least "First Import"
        assert data["total"] >= 1
        badge_names = [item["badge"]["name"] for item in data["items"]]
        assert "First Import" in badge_names

    async def test_check_badges_idempotent(
        self,
        authenticated_client: AsyncClient,
        papers_for_stats: list[Paper],
    ):
        """Test that checking twice doesn't duplicate badges."""
        first = await authenticated_client.post("/api/v1/badges/me/check")
        second = await authenticated_client.post("/api/v1/badges/me/check")
        assert first.json()["total"] == second.json()["total"]

    async def test_unauthorized_list_badges(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/badges/")
        assert response.status_code == 401

    async def test_unauthorized_get_my_badges(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/badges/me")
        assert response.status_code == 401

    async def test_unauthorized_get_my_stats(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated stats are rejected."""
        response = await client.get("/api/v1/badges/me/stats")
        assert response.status_code == 401
