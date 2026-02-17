"""Comprehensive tests for the Badge service layer (Sprint 30 Technical Debt).

Covers:
- get_user_stats() with accurate counts scoped by user/org
- check_and_award_badges() awarding only visible badges (system + org-specific)
- list_badges() org-level filtering
- seed_badges() idempotency
- Tenant isolation for all badge operations
- Level/progress calculation edge cases
"""


import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.authors.models import AuthorContact  # noqa: F401 - table creation
from paper_scraper.modules.badges.models import Badge, BadgeCategory, BadgeTier, UserBadge
from paper_scraper.modules.badges.service import DEFAULT_BADGES, POINTS_PER_LEVEL, BadgeService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote  # noqa: F401 - table creation
from paper_scraper.modules.projects.models import Project
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.search.models import SearchActivity

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def org_a(db_session: AsyncSession) -> Organization:
    """First organization for isolation tests."""
    org = Organization(name="Organization A", type="university")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def org_b(db_session: AsyncSession) -> Organization:
    """Second organization for isolation tests."""
    org = Organization(name="Organization B", type="vc")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def user_a(db_session: AsyncSession, org_a: Organization) -> User:
    """User belonging to org_a."""
    user = User(
        email="user_a@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User A",
        organization_id=org_a.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_a2(db_session: AsyncSession, org_a: Organization) -> User:
    """Second user in org_a -- tests per-user vs per-org scoping."""
    user = User(
        email="user_a2@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User A2",
        organization_id=org_a.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_b(db_session: AsyncSession, org_b: Organization) -> User:
    """User belonging to org_b."""
    user = User(
        email="user_b@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User B",
        organization_id=org_b.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# seed_badges() Tests
# ---------------------------------------------------------------------------


class TestSeedBadges:
    """Test that seed_badges creates default badges idempotently."""

    @pytest.mark.asyncio
    async def test_seed_badges_creates_defaults_when_empty(
        self,
        db_session: AsyncSession,
    ) -> None:
        """seed_badges should create all DEFAULT_BADGES when no badges exist."""
        service = BadgeService(db_session)
        created = await service.seed_badges()

        assert created == len(DEFAULT_BADGES)

        # Verify all badges are in the database
        result = await db_session.execute(select(func.count()).select_from(Badge))
        count = result.scalar()
        assert count == len(DEFAULT_BADGES)

    @pytest.mark.asyncio
    async def test_seed_badges_is_idempotent(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Calling seed_badges when badges already exist should create nothing."""
        service = BadgeService(db_session)

        # First call creates badges
        first_count = await service.seed_badges()
        assert first_count == len(DEFAULT_BADGES)

        # Second call creates nothing
        second_count = await service.seed_badges()
        assert second_count == 0

        # Total badge count is unchanged
        result = await db_session.execute(select(func.count()).select_from(Badge))
        assert result.scalar() == len(DEFAULT_BADGES)

    @pytest.mark.asyncio
    async def test_seed_badges_skips_when_custom_badges_exist(
        self,
        db_session: AsyncSession,
        org_a: Organization,
    ) -> None:
        """seed_badges should not create defaults if any badge already exists,
        even if it is a custom org-specific badge."""
        # Manually add one custom badge
        custom = Badge(
            name="Custom Only",
            description="A custom badge",
            icon="star",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.BRONZE,
            criteria={"action": "custom", "count": 1},
            threshold=1,
            points=5,
            organization_id=org_a.id,
            is_custom=True,
        )
        db_session.add(custom)
        await db_session.flush()

        service = BadgeService(db_session)
        created = await service.seed_badges()

        # Should not create defaults because at least one badge exists
        assert created == 0

    @pytest.mark.asyncio
    async def test_seed_badges_creates_system_badges_without_org_id(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Seeded badges should have organization_id = None (system-wide)."""
        service = BadgeService(db_session)
        await service.seed_badges()

        result = await db_session.execute(select(Badge))
        badges = list(result.scalars().all())

        for badge in badges:
            assert badge.organization_id is None
            assert badge.is_custom is False


# ---------------------------------------------------------------------------
# get_user_stats() Tests
# ---------------------------------------------------------------------------


class TestGetUserStats:
    """Test that get_user_stats returns accurate per-user/per-org counts."""

    @pytest.mark.asyncio
    async def test_fresh_user_all_zeros(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """A user with no activity should have all-zero stats."""
        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_a.id, org_a.id)

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
    async def test_papers_imported_scoped_by_created_by_id(
        self,
        db_session: AsyncSession,
        user_a: User,
        user_a2: User,
        org_a: Organization,
    ) -> None:
        """papers_imported should only count papers created by the specific user,
        not all papers in the org."""
        # user_a imports 3 papers
        for i in range(3):
            db_session.add(Paper(
                title=f"Paper by user_a #{i}",
                abstract=f"Abstract {i}",
                source="openalex",
                organization_id=org_a.id,
                created_by_id=user_a.id,
            ))

        # user_a2 imports 2 papers in the same org
        for i in range(2):
            db_session.add(Paper(
                title=f"Paper by user_a2 #{i}",
                abstract=f"Abstract {i}",
                source="openalex",
                organization_id=org_a.id,
                created_by_id=user_a2.id,
            ))
        await db_session.flush()

        service = BadgeService(db_session)

        stats_a = await service.get_user_stats(user_a.id, org_a.id)
        assert stats_a.papers_imported == 3

        stats_a2 = await service.get_user_stats(user_a2.id, org_a.id)
        assert stats_a2.papers_imported == 2

    @pytest.mark.asyncio
    async def test_papers_scored_scoped_by_org(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
        org_b: Organization,
    ) -> None:
        """papers_scored counts scores in the user's org, not across all orgs."""
        # Create papers in both orgs
        paper_a = Paper(
            title="Org A paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        )
        paper_b = Paper(
            title="Org B paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_b.id,
        )
        db_session.add_all([paper_a, paper_b])
        await db_session.flush()

        # Score in org A
        score_a = PaperScore(
            paper_id=paper_a.id,
            organization_id=org_a.id,
            novelty=7.0,
            ip_potential=6.0,
            marketability=5.0,
            feasibility=8.0,
            commercialization=6.5,
            team_readiness=5.0,
            overall_score=6.5,
            overall_confidence=0.85,
            model_version="test-v1",
        )
        # Score in org B
        score_b = PaperScore(
            paper_id=paper_b.id,
            organization_id=org_b.id,
            novelty=7.0,
            ip_potential=6.0,
            marketability=5.0,
            feasibility=8.0,
            commercialization=6.5,
            team_readiness=5.0,
            overall_score=6.5,
            overall_confidence=0.85,
            model_version="test-v1",
        )
        db_session.add_all([score_a, score_b])
        await db_session.flush()

        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_a.id, org_a.id)

        assert stats.papers_scored == 1  # Only org A score
        assert stats.papers_imported == 1  # Only user_a's paper

    @pytest.mark.asyncio
    async def test_searches_performed_scoped_by_user(
        self,
        db_session: AsyncSession,
        user_a: User,
        user_a2: User,
        org_a: Organization,
    ) -> None:
        """searches_performed should count only the specific user's searches."""
        # user_a: 4 searches
        for i in range(4):
            db_session.add(SearchActivity(
                user_id=user_a.id,
                organization_id=org_a.id,
                query=f"user_a query {i}",
                mode="fulltext",
                results_count=0,
            ))
        # user_a2: 2 searches
        for i in range(2):
            db_session.add(SearchActivity(
                user_id=user_a2.id,
                organization_id=org_a.id,
                query=f"user_a2 query {i}",
                mode="hybrid",
                results_count=0,
            ))
        await db_session.flush()

        service = BadgeService(db_session)

        stats_a = await service.get_user_stats(user_a.id, org_a.id)
        assert stats_a.searches_performed == 4

        stats_a2 = await service.get_user_stats(user_a2.id, org_a.id)
        assert stats_a2.searches_performed == 2

    @pytest.mark.asyncio
    async def test_projects_created_scoped_by_org(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """projects_created counts projects in the user's organization."""
        for i in range(2):
            db_session.add(Project(
                organization_id=org_a.id,
                name=f"Project {i}",
            ))
        await db_session.flush()

        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_a.id, org_a.id)

        assert stats.projects_created == 2

    @pytest.mark.asyncio
    async def test_notes_created_scoped_by_user(
        self,
        db_session: AsyncSession,
        user_a: User,
        user_a2: User,
        org_a: Organization,
    ) -> None:
        """notes_created should count only the specific user's notes."""
        paper = Paper(
            title="Test Paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
        )
        db_session.add(paper)
        await db_session.flush()

        # user_a: 3 notes
        for i in range(3):
            db_session.add(PaperNote(
                organization_id=org_a.id,
                paper_id=paper.id,
                user_id=user_a.id,
                content=f"Note {i} by user_a",
            ))
        # user_a2: 1 note
        db_session.add(PaperNote(
            organization_id=org_a.id,
            paper_id=paper.id,
            user_id=user_a2.id,
            content="Note by user_a2",
        ))
        await db_session.flush()

        service = BadgeService(db_session)

        stats_a = await service.get_user_stats(user_a.id, org_a.id)
        assert stats_a.notes_created == 3

        stats_a2 = await service.get_user_stats(user_a2.id, org_a.id)
        assert stats_a2.notes_created == 1

    @pytest.mark.asyncio
    async def test_badges_earned_and_total_points(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """badges_earned and total_points should reflect awarded UserBadge records."""
        # Create two badges with different point values
        badge1 = Badge(
            name="Badge 10pts",
            description="Ten points",
            icon="test",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.BRONZE,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=10,
        )
        badge2 = Badge(
            name="Badge 50pts",
            description="Fifty points",
            icon="test",
            category=BadgeCategory.SCORING,
            tier=BadgeTier.GOLD,
            criteria={"action": "test2", "count": 1},
            threshold=1,
            points=50,
        )
        db_session.add_all([badge1, badge2])
        await db_session.flush()

        # Award both to user_a
        db_session.add(UserBadge(user_id=user_a.id, badge_id=badge1.id, progress=1))
        db_session.add(UserBadge(user_id=user_a.id, badge_id=badge2.id, progress=1))
        await db_session.flush()

        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_a.id, org_a.id)

        assert stats.badges_earned == 2
        assert stats.total_points == 60

    @pytest.mark.asyncio
    async def test_level_calculation_at_boundary(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """Level should increment exactly at POINTS_PER_LEVEL boundary."""
        # Create a badge worth exactly POINTS_PER_LEVEL
        badge = Badge(
            name="Level Up Badge",
            description="Exactly one level",
            icon="level",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.GOLD,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=POINTS_PER_LEVEL,  # 100
        )
        db_session.add(badge)
        await db_session.flush()

        db_session.add(UserBadge(user_id=user_a.id, badge_id=badge.id, progress=1))
        await db_session.flush()

        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_a.id, org_a.id)

        # 100 points: level = 100//100 + 1 = 2, progress = 0.0
        assert stats.total_points == POINTS_PER_LEVEL
        assert stats.level == 2
        assert stats.level_progress == 0.0

    @pytest.mark.asyncio
    async def test_level_calculation_with_partial_progress(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """Level progress should be the fractional part toward the next level."""
        badge = Badge(
            name="Partial Level Badge",
            description="75 points",
            icon="star",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.SILVER,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=75,
        )
        db_session.add(badge)
        await db_session.flush()

        db_session.add(UserBadge(user_id=user_a.id, badge_id=badge.id, progress=1))
        await db_session.flush()

        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_a.id, org_a.id)

        # 75 points: level = 75//100 + 1 = 1, progress = 75/100 = 0.75
        assert stats.total_points == 75
        assert stats.level == 1
        assert stats.level_progress == 0.75

    @pytest.mark.asyncio
    async def test_stats_not_affected_by_other_org_data(
        self,
        db_session: AsyncSession,
        user_a: User,
        user_b: User,
        org_a: Organization,
        org_b: Organization,
    ) -> None:
        """Stats for user_a should not include data from org_b."""
        # Create papers in org_b
        for i in range(5):
            db_session.add(Paper(
                title=f"Org B paper {i}",
                abstract="Abstract",
                source="openalex",
                organization_id=org_b.id,
                created_by_id=user_b.id,
            ))
        # Create searches in org_b
        for i in range(3):
            db_session.add(SearchActivity(
                user_id=user_b.id,
                organization_id=org_b.id,
                query=f"org_b query {i}",
                mode="fulltext",
                results_count=0,
            ))
        await db_session.flush()

        service = BadgeService(db_session)
        stats_a = await service.get_user_stats(user_a.id, org_a.id)

        assert stats_a.papers_imported == 0
        assert stats_a.searches_performed == 0
        assert stats_a.projects_created == 0


# ---------------------------------------------------------------------------
# list_badges() Tests
# ---------------------------------------------------------------------------


class TestListBadges:
    """Test list_badges organization filtering."""

    @pytest.mark.asyncio
    async def test_list_badges_without_org_returns_all(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
    ) -> None:
        """Calling list_badges(organization_id=None) should return all badges."""
        service = BadgeService(db_session)
        await service.seed_badges()

        # Add custom badges for both orgs
        db_session.add(Badge(
            name="Custom A",
            description="For org A",
            icon="a",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.BRONZE,
            criteria={"action": "a", "count": 1},
            threshold=1,
            points=5,
            organization_id=org_a.id,
            is_custom=True,
        ))
        db_session.add(Badge(
            name="Custom B",
            description="For org B",
            icon="b",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.BRONZE,
            criteria={"action": "b", "count": 1},
            threshold=1,
            points=5,
            organization_id=org_b.id,
            is_custom=True,
        ))
        await db_session.flush()

        result = await service.list_badges(organization_id=None)

        # Should include system + both custom badges
        names = {b.name for b in result.items}
        assert "Custom A" in names
        assert "Custom B" in names
        assert "First Import" in names  # system badge

    @pytest.mark.asyncio
    async def test_list_badges_with_org_shows_system_plus_own(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
    ) -> None:
        """list_badges(org_id=A) shows system badges + org A custom badges."""
        service = BadgeService(db_session)
        await service.seed_badges()

        db_session.add(Badge(
            name="Org A Exclusive",
            description="Only for A",
            icon="a",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.SILVER,
            criteria={"action": "a", "count": 1},
            threshold=1,
            points=20,
            organization_id=org_a.id,
            is_custom=True,
        ))
        db_session.add(Badge(
            name="Org B Exclusive",
            description="Only for B",
            icon="b",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.SILVER,
            criteria={"action": "b", "count": 1},
            threshold=1,
            points=20,
            organization_id=org_b.id,
            is_custom=True,
        ))
        await db_session.flush()

        result = await service.list_badges(organization_id=org_a.id)
        names = {b.name for b in result.items}

        assert "Org A Exclusive" in names
        assert "Org B Exclusive" not in names
        assert "First Import" in names  # system badge

    @pytest.mark.asyncio
    async def test_list_badges_auto_seeds_when_empty(
        self,
        db_session: AsyncSession,
        org_a: Organization,
    ) -> None:
        """list_badges should call seed_badges if no badges exist."""
        service = BadgeService(db_session)
        result = await service.list_badges(organization_id=org_a.id)

        # Should have seeded the defaults
        assert result.total >= len(DEFAULT_BADGES)

    @pytest.mark.asyncio
    async def test_list_badges_total_matches_items_length(
        self,
        db_session: AsyncSession,
        org_a: Organization,
    ) -> None:
        """The total field should match the actual number of items returned."""
        service = BadgeService(db_session)
        result = await service.list_badges(organization_id=org_a.id)

        assert result.total == len(result.items)


# ---------------------------------------------------------------------------
# check_and_award_badges() Tests
# ---------------------------------------------------------------------------


class TestCheckAndAwardBadges:
    """Test the badge awarding logic."""

    @pytest.mark.asyncio
    async def test_awards_first_import_badge_when_threshold_met(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """User with 1 imported paper should earn the 'First Import' badge."""
        # Arrange: user_a imports a paper
        db_session.add(Paper(
            title="First paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        ))
        await db_session.flush()

        service = BadgeService(db_session)
        newly_awarded = await service.check_and_award_badges(user_a.id, org_a.id)

        badge_names = [b.name for b in newly_awarded]
        assert "First Import" in badge_names

    @pytest.mark.asyncio
    async def test_does_not_award_already_earned_badge(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """A badge already earned should not be awarded again."""
        # Arrange: user_a imports a paper
        db_session.add(Paper(
            title="Paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        ))
        await db_session.flush()

        service = BadgeService(db_session)

        # First award
        first = await service.check_and_award_badges(user_a.id, org_a.id)
        assert len(first) > 0

        # Second award attempt -- should return empty
        second = await service.check_and_award_badges(user_a.id, org_a.id)
        first_names = {b.name for b in first}
        second_names = {b.name for b in second}
        # No badge from the first round should appear again
        assert first_names.isdisjoint(second_names)

    @pytest.mark.asyncio
    async def test_does_not_award_unmet_threshold(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """Badges whose threshold is not met should not be awarded."""
        # User has no papers at all
        service = BadgeService(db_session)
        newly_awarded = await service.check_and_award_badges(user_a.id, org_a.id)

        # No badge should be awarded for a user with zero activity
        assert len(newly_awarded) == 0

    @pytest.mark.asyncio
    async def test_awards_multiple_badges_at_once(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """If a user meets thresholds for multiple badges, all should be awarded."""
        # Import 1 paper (triggers First Import)
        db_session.add(Paper(
            title="Paper 1",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        ))
        # Add 1 search (triggers Explorer)
        db_session.add(SearchActivity(
            user_id=user_a.id,
            organization_id=org_a.id,
            query="test search",
            mode="fulltext",
            results_count=5,
        ))
        # Add 1 project (triggers Project Starter)
        db_session.add(Project(
            organization_id=org_a.id,
            name="Test Project",
        ))
        await db_session.flush()

        service = BadgeService(db_session)
        newly_awarded = await service.check_and_award_badges(user_a.id, org_a.id)
        badge_names = {b.name for b in newly_awarded}

        assert "First Import" in badge_names
        assert "Explorer" in badge_names
        assert "Project Starter" in badge_names

    @pytest.mark.asyncio
    async def test_awards_only_visible_badges_not_other_org_custom(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
        org_b: Organization,
    ) -> None:
        """check_and_award_badges should only consider system badges + user's org badges,
        not custom badges from other organizations."""
        service = BadgeService(db_session)
        await service.seed_badges()

        # Create a custom badge for org_b with threshold=1 for paper_imported
        custom_b = Badge(
            name="Org B Only Badge",
            description="Custom for org B",
            icon="lock",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.PLATINUM,
            criteria={"action": "paper_imported", "count": 1},
            threshold=1,
            points=100,
            organization_id=org_b.id,
            is_custom=True,
        )
        db_session.add(custom_b)
        await db_session.flush()

        # user_a imports a paper (meets threshold)
        db_session.add(Paper(
            title="Paper for user_a",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        ))
        await db_session.flush()

        newly_awarded = await service.check_and_award_badges(user_a.id, org_a.id)
        badge_names = {b.name for b in newly_awarded}

        # Should get First Import (system) but NOT Org B Only Badge
        assert "First Import" in badge_names
        assert "Org B Only Badge" not in badge_names

    @pytest.mark.asyncio
    async def test_awards_org_custom_badge_when_visible(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """Custom badges belonging to the user's org should be awardable."""
        service = BadgeService(db_session)
        await service.seed_badges()

        # Create a custom badge for org_a
        custom_a = Badge(
            name="Org A Special",
            description="Custom for org A",
            icon="star",
            category=BadgeCategory.IMPORT,
            tier=BadgeTier.GOLD,
            criteria={"action": "paper_imported", "count": 1},
            threshold=1,
            points=50,
            organization_id=org_a.id,
            is_custom=True,
        )
        db_session.add(custom_a)
        await db_session.flush()

        # user_a imports a paper
        db_session.add(Paper(
            title="Paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        ))
        await db_session.flush()

        newly_awarded = await service.check_and_award_badges(user_a.id, org_a.id)
        badge_names = {b.name for b in newly_awarded}

        assert "Org A Special" in badge_names

    @pytest.mark.asyncio
    async def test_awarded_badges_persist_in_user_badges_table(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """Awarded badges should create UserBadge records in the database."""
        db_session.add(Paper(
            title="Paper",
            abstract="Abstract",
            source="openalex",
            organization_id=org_a.id,
            created_by_id=user_a.id,
        ))
        await db_session.flush()

        service = BadgeService(db_session)
        await service.check_and_award_badges(user_a.id, org_a.id)

        result = await db_session.execute(
            select(UserBadge).where(UserBadge.user_id == user_a.id)
        )
        user_badges = list(result.scalars().all())

        assert len(user_badges) > 0
        # Each user badge should reference our user
        for ub in user_badges:
            assert ub.user_id == user_a.id

    @pytest.mark.asyncio
    async def test_search_badge_awarded_with_enough_searches(
        self,
        db_session: AsyncSession,
        user_a: User,
        org_a: Organization,
    ) -> None:
        """The 'Explorer' badge (1 search) and 'Pathfinder' (25 searches) should
        be awarded based on SearchActivity count."""
        service = BadgeService(db_session)
        await service.seed_badges()

        # Create 25 search activities
        for i in range(25):
            db_session.add(SearchActivity(
                user_id=user_a.id,
                organization_id=org_a.id,
                query=f"query {i}",
                mode="hybrid",
                results_count=i,
            ))
        await db_session.flush()

        newly_awarded = await service.check_and_award_badges(user_a.id, org_a.id)
        badge_names = {b.name for b in newly_awarded}

        assert "Explorer" in badge_names
        assert "Pathfinder" in badge_names


# ---------------------------------------------------------------------------
# get_user_badges() Tests
# ---------------------------------------------------------------------------


class TestGetUserBadges:
    """Test retrieving earned badges for a user."""

    @pytest.mark.asyncio
    async def test_get_user_badges_empty(
        self,
        db_session: AsyncSession,
        user_a: User,
    ) -> None:
        """User with no badges should get empty list with 0 points."""
        service = BadgeService(db_session)
        result = await service.get_user_badges(user_a.id)

        assert result.total == 0
        assert result.total_points == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_user_badges_includes_badge_details(
        self,
        db_session: AsyncSession,
        user_a: User,
    ) -> None:
        """Each UserBadgeResponse should include the nested badge details."""
        badge = Badge(
            name="Detail Test Badge",
            description="Badge with details",
            icon="info",
            category=BadgeCategory.SCORING,
            tier=BadgeTier.SILVER,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=30,
        )
        db_session.add(badge)
        await db_session.flush()

        db_session.add(UserBadge(
            user_id=user_a.id,
            badge_id=badge.id,
            progress=5,
        ))
        await db_session.flush()

        service = BadgeService(db_session)
        result = await service.get_user_badges(user_a.id)

        assert result.total == 1
        assert result.total_points == 30
        assert result.items[0].badge.name == "Detail Test Badge"
        assert result.items[0].badge.tier == BadgeTier.SILVER
        assert result.items[0].progress == 5


# ---------------------------------------------------------------------------
# Tenant Isolation Tests
# ---------------------------------------------------------------------------


class TestBadgeTenantIsolation:
    """Verify that badge operations respect tenant boundaries."""

    @pytest.mark.asyncio
    async def test_user_badges_not_visible_to_other_users(
        self,
        db_session: AsyncSession,
        user_a: User,
        user_b: User,
    ) -> None:
        """Badges earned by user_a should not appear in user_b's badges."""
        badge = Badge(
            name="Isolation Badge",
            description="Test",
            icon="lock",
            category=BadgeCategory.MILESTONE,
            tier=BadgeTier.BRONZE,
            criteria={"action": "test", "count": 1},
            threshold=1,
            points=10,
        )
        db_session.add(badge)
        await db_session.flush()

        db_session.add(UserBadge(
            user_id=user_a.id,
            badge_id=badge.id,
            progress=1,
        ))
        await db_session.flush()

        service = BadgeService(db_session)

        result_a = await service.get_user_badges(user_a.id)
        result_b = await service.get_user_badges(user_b.id)

        assert result_a.total == 1
        assert result_b.total == 0

    @pytest.mark.asyncio
    async def test_stats_isolated_between_orgs(
        self,
        db_session: AsyncSession,
        user_a: User,
        user_b: User,
        org_a: Organization,
        org_b: Organization,
    ) -> None:
        """Stats for one org should not leak into another org's stats."""
        # user_b creates papers in org_b
        for i in range(10):
            db_session.add(Paper(
                title=f"Org B paper {i}",
                abstract="Abstract",
                source="openalex",
                organization_id=org_b.id,
                created_by_id=user_b.id,
            ))
        await db_session.flush()

        service = BadgeService(db_session)

        stats_a = await service.get_user_stats(user_a.id, org_a.id)
        stats_b = await service.get_user_stats(user_b.id, org_b.id)

        assert stats_a.papers_imported == 0
        assert stats_b.papers_imported == 10
