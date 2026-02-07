"""Comprehensive tests for SearchActivity tracking, Knowledge pagination,
and retention policy application to search activities (Sprint 30 Technical Debt).

Covers:
- SearchActivity model creation and field validation
- SearchActivity integration with BadgeService stats
- Knowledge pagination (page count calculation, edge cases)
- Compliance retention policy for search_activities entity type
- Tenant isolation for search activities and knowledge sources
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.badges.service import BadgeService
from paper_scraper.modules.compliance.models import RetentionEntityType, RetentionPolicy
from paper_scraper.modules.compliance.service import ComplianceService
from paper_scraper.modules.knowledge.models import KnowledgeScope, KnowledgeSource, KnowledgeType
from paper_scraper.modules.knowledge.service import KnowledgeService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.papers.notes import PaperNote  # noqa: F401 - table creation
from paper_scraper.modules.search.models import SearchActivity
from paper_scraper.modules.authors.models import AuthorContact  # noqa: F401 - table creation
from paper_scraper.core.security import get_password_hash


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def org_alpha(db_session: AsyncSession) -> Organization:
    """Organization for search activity tests."""
    org = Organization(name="Alpha Corp", type="corporate")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def org_beta(db_session: AsyncSession) -> Organization:
    """Second organization for tenant isolation tests."""
    org = Organization(name="Beta University", type="university")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def user_alpha(db_session: AsyncSession, org_alpha: Organization) -> User:
    """User belonging to org_alpha."""
    user = User(
        email="alpha_user@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Alpha User",
        organization_id=org_alpha.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_beta(db_session: AsyncSession, org_beta: Organization) -> User:
    """User belonging to org_beta."""
    user = User(
        email="beta_user@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Beta User",
        organization_id=org_beta.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def search_activities_alpha(
    db_session: AsyncSession,
    user_alpha: User,
    org_alpha: Organization,
) -> list[SearchActivity]:
    """Create multiple search activities for user_alpha."""
    activities = []
    for i in range(5):
        activity = SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query=f"machine learning query {i}",
            mode="hybrid" if i % 2 == 0 else "fulltext",
            results_count=i * 10,
            search_time_ms=50.0 + i * 10,
        )
        db_session.add(activity)
        activities.append(activity)
    await db_session.flush()
    for a in activities:
        await db_session.refresh(a)
    return activities


# ---------------------------------------------------------------------------
# SearchActivity Model Tests
# ---------------------------------------------------------------------------


class TestSearchActivityModel:
    """Test the SearchActivity model creation and field persistence."""

    @pytest.mark.asyncio
    async def test_create_search_activity_all_fields(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """All fields should persist correctly after creation."""
        activity = SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query="quantum computing applications",
            mode="semantic",
            results_count=15,
            search_time_ms=234.56,
        )
        db_session.add(activity)
        await db_session.flush()
        await db_session.refresh(activity)

        assert activity.id is not None
        assert activity.user_id == user_alpha.id
        assert activity.organization_id == org_alpha.id
        assert activity.query == "quantum computing applications"
        assert activity.mode == "semantic"
        assert activity.results_count == 15
        assert activity.search_time_ms == 234.56
        assert activity.created_at is not None

    @pytest.mark.asyncio
    async def test_create_search_activity_with_default_mode(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Default mode should be 'hybrid' when not specified."""
        activity = SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query="test query",
            results_count=0,
        )
        db_session.add(activity)
        await db_session.flush()
        await db_session.refresh(activity)

        assert activity.mode == "hybrid"

    @pytest.mark.asyncio
    async def test_search_activity_null_search_time(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """search_time_ms should be nullable."""
        activity = SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query="quick search",
            mode="fulltext",
            results_count=3,
            search_time_ms=None,
        )
        db_session.add(activity)
        await db_session.flush()
        await db_session.refresh(activity)

        assert activity.search_time_ms is None

    @pytest.mark.asyncio
    async def test_search_activity_long_query_truncated(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Query field should accept up to 1000 characters."""
        long_query = "a" * 1000
        activity = SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query=long_query,
            mode="fulltext",
            results_count=0,
        )
        db_session.add(activity)
        await db_session.flush()
        await db_session.refresh(activity)

        assert len(activity.query) == 1000

    @pytest.mark.asyncio
    async def test_search_activity_repr(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """The repr should contain user ID and truncated query."""
        activity = SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query="CRISPR gene editing in stem cells",
            mode="hybrid",
            results_count=42,
        )
        db_session.add(activity)
        await db_session.flush()

        repr_str = repr(activity)
        assert "SearchActivity" in repr_str
        assert "CRISPR gene editing" in repr_str

    @pytest.mark.asyncio
    async def test_multiple_activities_same_user(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """A single user should be able to have many search activities."""
        for i in range(20):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"query number {i}",
                mode="fulltext",
                results_count=i,
            ))
        await db_session.flush()

        result = await db_session.execute(
            select(func.count()).select_from(SearchActivity).where(
                SearchActivity.user_id == user_alpha.id
            )
        )
        count = result.scalar()
        assert count == 20


# ---------------------------------------------------------------------------
# SearchActivity Integration with Badge Stats
# ---------------------------------------------------------------------------


class TestSearchActivityBadgeIntegration:
    """Test that SearchActivity records integrate correctly with badge stats."""

    @pytest.mark.asyncio
    async def test_search_count_in_stats_matches_actual_records(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
        search_activities_alpha: list[SearchActivity],
    ) -> None:
        """Badge stats searches_performed should match actual SearchActivity count."""
        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_alpha.id, org_alpha.id)

        assert stats.searches_performed == len(search_activities_alpha)

    @pytest.mark.asyncio
    async def test_search_activities_isolated_between_users(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        user_beta: User,
        org_alpha: Organization,
        org_beta: Organization,
        search_activities_alpha: list[SearchActivity],
    ) -> None:
        """user_beta should not see user_alpha's search activities in stats."""
        service = BadgeService(db_session)

        stats_alpha = await service.get_user_stats(user_alpha.id, org_alpha.id)
        stats_beta = await service.get_user_stats(user_beta.id, org_beta.id)

        assert stats_alpha.searches_performed == 5
        assert stats_beta.searches_performed == 0

    @pytest.mark.asyncio
    async def test_search_activities_from_different_modes_all_counted(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """All search modes (fulltext, semantic, hybrid) should be counted."""
        modes = ["fulltext", "semantic", "hybrid"]
        for mode in modes:
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"{mode} search",
                mode=mode,
                results_count=10,
            ))
        await db_session.flush()

        service = BadgeService(db_session)
        stats = await service.get_user_stats(user_alpha.id, org_alpha.id)

        assert stats.searches_performed == 3


# ---------------------------------------------------------------------------
# Knowledge Pagination Tests
# ---------------------------------------------------------------------------


class TestKnowledgePaginationComprehensive:
    """Comprehensive tests for knowledge service pagination."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero_pages(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Empty result should return pages=0."""
        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
        )

        assert result.total == 0
        assert result.pages == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_page_count_exact_division(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """When total divides evenly by page_size, pages should be exact."""
        # Create exactly 10 sources
        for i in range(10):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Source {i}",
                content=f"Content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            page=1,
            page_size=5,
        )

        assert result.total == 10
        assert result.pages == 2  # 10 / 5 = 2 exactly

    @pytest.mark.asyncio
    async def test_page_count_with_remainder(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """When total does not divide evenly, pages should round up."""
        # Create 7 sources
        for i in range(7):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Source {i}",
                content=f"Content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            page=1,
            page_size=3,
        )

        assert result.total == 7
        assert result.pages == 3  # ceil(7/3) = 3

    @pytest.mark.asyncio
    async def test_last_page_has_remaining_items(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """The last page should contain only the remaining items."""
        for i in range(7):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Source {i}",
                content=f"Content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            page=3,
            page_size=3,
        )

        assert result.total == 7
        assert len(result.items) == 1  # Only 1 remaining on page 3

    @pytest.mark.asyncio
    async def test_page_beyond_data_returns_empty(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Requesting a page beyond the data should return empty items."""
        for i in range(3):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Source {i}",
                content=f"Content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            page=100,
            page_size=10,
        )

        assert result.total == 3
        assert len(result.items) == 0
        assert result.page == 100

    @pytest.mark.asyncio
    async def test_page_size_one_returns_single_items(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """page_size=1 should return exactly one item per page."""
        for i in range(3):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Source {i}",
                content=f"Content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)
        result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            page=1,
            page_size=1,
        )

        assert result.total == 3
        assert result.pages == 3
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_organization_pagination_independent_of_personal(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Organization sources should not include personal sources and vice versa."""
        # Add 3 personal sources
        for i in range(3):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Personal {i}",
                content=f"Personal content {i}",
                tags=[],
            ))
        # Add 2 organization sources
        for i in range(2):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=None,
                scope=KnowledgeScope.ORGANIZATION,
                type=KnowledgeType.INDUSTRY_CONTEXT,
                title=f"Org {i}",
                content=f"Org content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)

        personal_result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
        )
        org_result = await service.list_organization(
            organization_id=org_alpha.id,
        )

        assert personal_result.total == 3
        assert org_result.total == 2

    @pytest.mark.asyncio
    async def test_personal_sources_isolated_between_users(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        user_beta: User,
        org_alpha: Organization,
        org_beta: Organization,
    ) -> None:
        """Personal knowledge sources should be visible only to the owning user."""
        # user_alpha has 4 personal sources
        for i in range(4):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=user_alpha.id,
                scope=KnowledgeScope.PERSONAL,
                type=KnowledgeType.CUSTOM,
                title=f"Alpha personal {i}",
                content=f"Content {i}",
                tags=[],
            ))
        await db_session.flush()

        service = KnowledgeService(db_session)

        alpha_result = await service.list_personal(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
        )
        beta_result = await service.list_personal(
            user_id=user_beta.id,
            organization_id=org_beta.id,
        )

        assert alpha_result.total == 4
        assert beta_result.total == 0

    @pytest.mark.asyncio
    async def test_organization_sources_isolated_between_orgs(
        self,
        db_session: AsyncSession,
        org_alpha: Organization,
        org_beta: Organization,
    ) -> None:
        """Organization knowledge sources should be org-scoped."""
        for i in range(3):
            db_session.add(KnowledgeSource(
                organization_id=org_alpha.id,
                user_id=None,
                scope=KnowledgeScope.ORGANIZATION,
                type=KnowledgeType.RESEARCH_FOCUS,
                title=f"Alpha org source {i}",
                content=f"Content {i}",
                tags=[],
            ))
        db_session.add(KnowledgeSource(
            organization_id=org_beta.id,
            user_id=None,
            scope=KnowledgeScope.ORGANIZATION,
            type=KnowledgeType.RESEARCH_FOCUS,
            title="Beta org source",
            content="Content",
            tags=[],
        ))
        await db_session.flush()

        service = KnowledgeService(db_session)

        alpha_result = await service.list_organization(organization_id=org_alpha.id)
        beta_result = await service.list_organization(organization_id=org_beta.id)

        assert alpha_result.total == 3
        assert beta_result.total == 1


# ---------------------------------------------------------------------------
# Retention Policy for Search Activities Tests
# ---------------------------------------------------------------------------


class TestRetentionPolicySearchActivities:
    """Test the compliance service's _apply_to_search_activities method."""

    @pytest.mark.asyncio
    async def test_dry_run_counts_without_deleting(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Dry run should count affected records but not delete them."""
        # Create activities with old timestamps
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        old_time = cutoff - timedelta(days=10)

        for i in range(3):
            activity = SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"old query {i}",
                mode="fulltext",
                results_count=0,
            )
            db_session.add(activity)
        await db_session.flush()

        # Manually update created_at to be old (bypass server_default)
        result = await db_session.execute(
            select(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        activities = list(result.scalars().all())
        for a in activities:
            a.created_at = old_time
        await db_session.flush()

        service = ComplianceService(db_session)
        count = await service._apply_to_search_activities(
            organization_id=org_alpha.id,
            cutoff_date=cutoff,
            action="delete",
            dry_run=True,
        )

        assert count == 3

        # Verify records still exist
        remaining = await db_session.execute(
            select(func.count()).select_from(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        assert remaining.scalar() == 3

    @pytest.mark.asyncio
    async def test_actual_run_deletes_old_records(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Non-dry-run should actually delete records older than cutoff."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        old_time = cutoff - timedelta(days=10)
        recent_time = cutoff + timedelta(days=5)

        # Create 3 old activities and 2 recent ones
        for i in range(3):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"old query {i}",
                mode="fulltext",
                results_count=0,
            ))
        for i in range(2):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"recent query {i}",
                mode="hybrid",
                results_count=10,
            ))
        await db_session.flush()

        # Set timestamps
        result = await db_session.execute(
            select(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        all_activities = list(result.scalars().all())

        for a in all_activities:
            if "old" in a.query:
                a.created_at = old_time
            else:
                a.created_at = recent_time
        await db_session.flush()

        service = ComplianceService(db_session)
        count = await service._apply_to_search_activities(
            organization_id=org_alpha.id,
            cutoff_date=cutoff,
            action="delete",
            dry_run=False,
        )

        assert count == 3

        # Verify only recent records remain
        remaining = await db_session.execute(
            select(func.count()).select_from(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        assert remaining.scalar() == 2

    @pytest.mark.asyncio
    async def test_no_records_to_delete(
        self,
        db_session: AsyncSession,
        org_alpha: Organization,
    ) -> None:
        """When no records match the cutoff, count should be 0."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)

        service = ComplianceService(db_session)
        count = await service._apply_to_search_activities(
            organization_id=org_alpha.id,
            cutoff_date=cutoff,
            action="delete",
            dry_run=False,
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_retention_only_affects_target_organization(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        user_beta: User,
        org_alpha: Organization,
        org_beta: Organization,
    ) -> None:
        """Retention should only delete records from the specified organization."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        old_time = cutoff - timedelta(days=10)

        # Create old activities in both orgs
        for i in range(3):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"alpha old {i}",
                mode="fulltext",
                results_count=0,
            ))
        for i in range(2):
            db_session.add(SearchActivity(
                user_id=user_beta.id,
                organization_id=org_beta.id,
                query=f"beta old {i}",
                mode="fulltext",
                results_count=0,
            ))
        await db_session.flush()

        # Make all activities old
        result = await db_session.execute(select(SearchActivity))
        for a in result.scalars().all():
            a.created_at = old_time
        await db_session.flush()

        # Apply retention only to org_alpha
        service = ComplianceService(db_session)
        count = await service._apply_to_search_activities(
            organization_id=org_alpha.id,
            cutoff_date=cutoff,
            action="delete",
            dry_run=False,
        )

        assert count == 3

        # org_beta's records should be untouched
        remaining_beta = await db_session.execute(
            select(func.count()).select_from(SearchActivity).where(
                SearchActivity.organization_id == org_beta.id
            )
        )
        assert remaining_beta.scalar() == 2

    @pytest.mark.asyncio
    async def test_apply_retention_policies_with_search_activities_type(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Integration test: apply_retention_policies should handle search_activities type."""
        cutoff_days = 30
        old_time = datetime.now(timezone.utc) - timedelta(days=cutoff_days + 10)

        # Create retention policy for search_activities
        policy = RetentionPolicy(
            organization_id=org_alpha.id,
            entity_type=RetentionEntityType.SEARCH_ACTIVITIES.value,
            retention_days=cutoff_days,
            action="delete",
            is_active=True,
            description="Delete old search activities",
        )
        db_session.add(policy)
        await db_session.flush()

        # Create old activities
        for i in range(4):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"policy test query {i}",
                mode="hybrid",
                results_count=0,
            ))
        await db_session.flush()

        # Make activities old
        result = await db_session.execute(
            select(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        for a in result.scalars().all():
            a.created_at = old_time
        await db_session.flush()

        # Apply policies (dry run)
        service = ComplianceService(db_session)
        results = await service.apply_retention_policies(
            organization_id=org_alpha.id,
            dry_run=True,
        )

        assert len(results) == 1
        assert results[0].entity_type == RetentionEntityType.SEARCH_ACTIVITIES.value
        assert results[0].records_affected == 4
        assert results[0].is_dry_run is True
        assert results[0].status == "completed"

    @pytest.mark.asyncio
    async def test_inactive_policy_not_applied(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Inactive retention policies should not be applied."""
        old_time = datetime.now(timezone.utc) - timedelta(days=100)

        # Create inactive policy
        policy = RetentionPolicy(
            organization_id=org_alpha.id,
            entity_type=RetentionEntityType.SEARCH_ACTIVITIES.value,
            retention_days=30,
            action="delete",
            is_active=False,  # Inactive
            description="Inactive policy",
        )
        db_session.add(policy)

        # Create old activities
        for i in range(3):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"inactive test {i}",
                mode="fulltext",
                results_count=0,
            ))
        await db_session.flush()

        # Make activities old
        result = await db_session.execute(
            select(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        for a in result.scalars().all():
            a.created_at = old_time
        await db_session.flush()

        # Apply policies
        service = ComplianceService(db_session)
        results = await service.apply_retention_policies(
            organization_id=org_alpha.id,
            dry_run=False,
        )

        # No results because policy is inactive
        assert len(results) == 0

        # Records should still exist
        remaining = await db_session.execute(
            select(func.count()).select_from(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        assert remaining.scalar() == 3

    @pytest.mark.asyncio
    async def test_retention_log_created_after_application(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        org_alpha: Organization,
    ) -> None:
        """Applying retention should create a RetentionLog entry."""
        from paper_scraper.modules.compliance.models import RetentionLog

        old_time = datetime.now(timezone.utc) - timedelta(days=100)

        policy = RetentionPolicy(
            organization_id=org_alpha.id,
            entity_type=RetentionEntityType.SEARCH_ACTIVITIES.value,
            retention_days=30,
            action="delete",
            is_active=True,
        )
        db_session.add(policy)

        db_session.add(SearchActivity(
            user_id=user_alpha.id,
            organization_id=org_alpha.id,
            query="to be logged",
            mode="fulltext",
            results_count=0,
        ))
        await db_session.flush()

        # Make activity old
        result = await db_session.execute(
            select(SearchActivity).where(
                SearchActivity.organization_id == org_alpha.id
            )
        )
        for a in result.scalars().all():
            a.created_at = old_time
        await db_session.flush()

        service = ComplianceService(db_session)
        await service.apply_retention_policies(
            organization_id=org_alpha.id,
            dry_run=True,
        )
        await db_session.flush()

        # Check RetentionLog was created
        log_result = await db_session.execute(
            select(RetentionLog).where(
                RetentionLog.organization_id == org_alpha.id,
                RetentionLog.entity_type == RetentionEntityType.SEARCH_ACTIVITIES.value,
            )
        )
        logs = list(log_result.scalars().all())
        assert len(logs) >= 1
        assert logs[0].records_affected == 1
        assert logs[0].is_dry_run is True


# ---------------------------------------------------------------------------
# SearchActivity Tenant Isolation Tests
# ---------------------------------------------------------------------------


class TestSearchActivityTenantIsolation:
    """Verify that search activity data respects tenant boundaries."""

    @pytest.mark.asyncio
    async def test_activities_not_visible_across_orgs(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        user_beta: User,
        org_alpha: Organization,
        org_beta: Organization,
    ) -> None:
        """Activities from one org should not appear in queries for another org."""
        # Create activities for org_alpha
        for i in range(5):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"alpha query {i}",
                mode="fulltext",
                results_count=0,
            ))
        await db_session.flush()

        # Count for org_beta should be zero
        result = await db_session.execute(
            select(func.count()).select_from(SearchActivity).where(
                SearchActivity.organization_id == org_beta.id
            )
        )
        assert result.scalar() == 0

    @pytest.mark.asyncio
    async def test_badge_stats_isolated_for_search_activities(
        self,
        db_session: AsyncSession,
        user_alpha: User,
        user_beta: User,
        org_alpha: Organization,
        org_beta: Organization,
    ) -> None:
        """Badge stats searches_performed should be user-scoped."""
        # user_alpha has 10 searches
        for i in range(10):
            db_session.add(SearchActivity(
                user_id=user_alpha.id,
                organization_id=org_alpha.id,
                query=f"alpha search {i}",
                mode="hybrid",
                results_count=0,
            ))
        # user_beta has 3 searches
        for i in range(3):
            db_session.add(SearchActivity(
                user_id=user_beta.id,
                organization_id=org_beta.id,
                query=f"beta search {i}",
                mode="fulltext",
                results_count=0,
            ))
        await db_session.flush()

        service = BadgeService(db_session)

        stats_alpha = await service.get_user_stats(user_alpha.id, org_alpha.id)
        stats_beta = await service.get_user_stats(user_beta.id, org_beta.id)

        assert stats_alpha.searches_performed == 10
        assert stats_beta.searches_performed == 3
