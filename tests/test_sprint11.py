"""Tests for Sprint 11: Search & Discovery Enhancements."""

import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.saved_searches.models import SavedSearch
from paper_scraper.modules.saved_searches.service import SavedSearchService
from paper_scraper.modules.saved_searches.schemas import SavedSearchCreate, AlertFrequency
from paper_scraper.modules.alerts.models import Alert, AlertChannel, AlertStatus
from paper_scraper.modules.alerts.service import AlertService
from paper_scraper.modules.alerts.schemas import AlertCreate
from paper_scraper.modules.papers.models import Paper, PaperSource, PaperType


# =============================================================================
# Module-level fixtures (shared across test classes)
# =============================================================================


@pytest_asyncio.fixture
async def sample_saved_search(
    db_session: AsyncSession,
    test_organization,
    test_user,
) -> SavedSearch:
    """Create a sample saved search for testing."""
    saved_search = SavedSearch(
        organization_id=test_organization.id,
        created_by_id=test_user.id,
        name="Test Search",
        description="A test saved search",
        query="machine learning",
        mode="fulltext",  # Use fulltext to avoid OpenAI API calls in tests
        filters={"sources": ["openalex"]},
        is_public=False,
        alert_enabled=False,
    )
    db_session.add(saved_search)
    await db_session.flush()
    return saved_search


# =============================================================================
# Saved Searches Tests
# =============================================================================


class TestSavedSearchService:
    """Tests for SavedSearchService."""

    @pytest.fixture
    async def saved_search_service(self, db_session: AsyncSession) -> SavedSearchService:
        """Get SavedSearchService instance."""
        return SavedSearchService(db_session)

    async def test_create_saved_search(
        self,
        saved_search_service: SavedSearchService,
        test_organization,
        test_user,
    ):
        """Test creating a saved search."""
        data = SavedSearchCreate(
            name="My Search",
            query="cancer research",
            mode="fulltext",
            is_public=True,
        )

        result = await saved_search_service.create(
            data=data,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert result.name == "My Search"
        assert result.query == "cancer research"
        assert result.mode == "fulltext"
        assert result.is_public is True
        assert result.organization_id == test_organization.id
        assert result.created_by_id == test_user.id

    async def test_create_duplicate_name_raises_error(
        self,
        saved_search_service: SavedSearchService,
        sample_saved_search: SavedSearch,
        test_organization,
        test_user,
    ):
        """Test that creating a saved search with duplicate name raises error."""
        from paper_scraper.core.exceptions import DuplicateError

        data = SavedSearchCreate(
            name=sample_saved_search.name,  # Same name
            query="different query",
        )

        with pytest.raises(DuplicateError):
            await saved_search_service.create(
                data=data,
                organization_id=test_organization.id,
                user_id=test_user.id,
            )

    async def test_get_saved_search(
        self,
        saved_search_service: SavedSearchService,
        sample_saved_search: SavedSearch,
        test_organization,
        test_user,
    ):
        """Test getting a saved search by ID."""
        result = await saved_search_service.get(
            search_id=sample_saved_search.id,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert result.id == sample_saved_search.id
        assert result.name == sample_saved_search.name

    async def test_get_saved_search_not_found(
        self,
        saved_search_service: SavedSearchService,
        test_organization,
        test_user,
    ):
        """Test that getting non-existent saved search raises error."""
        from paper_scraper.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await saved_search_service.get(
                search_id=uuid4(),
                organization_id=test_organization.id,
                user_id=test_user.id,
            )

    async def test_list_saved_searches(
        self,
        saved_search_service: SavedSearchService,
        sample_saved_search: SavedSearch,
        test_organization,
        test_user,
    ):
        """Test listing saved searches."""
        results, total = await saved_search_service.list_searches(
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert total >= 1
        assert any(s.id == sample_saved_search.id for s in results)

    async def test_generate_share_token(
        self,
        saved_search_service: SavedSearchService,
        sample_saved_search: SavedSearch,
        test_organization,
        test_user,
    ):
        """Test generating a share token."""
        share_token, share_url = await saved_search_service.generate_share_token(
            search_id=sample_saved_search.id,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert share_token is not None
        assert len(share_token) > 20
        assert share_url.endswith(share_token)

    async def test_get_by_share_token(
        self,
        saved_search_service: SavedSearchService,
        sample_saved_search: SavedSearch,
        test_organization,
        test_user,
    ):
        """Test getting saved search by share token."""
        share_token, _ = await saved_search_service.generate_share_token(
            search_id=sample_saved_search.id,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        result = await saved_search_service.get_by_share_token(share_token)

        assert result.id == sample_saved_search.id


# =============================================================================
# Alerts Tests
# =============================================================================


class TestAlertService:
    """Tests for AlertService."""

    @pytest.fixture
    async def alert_service(self, db_session: AsyncSession) -> AlertService:
        """Get AlertService instance."""
        return AlertService(db_session)

    @pytest.fixture
    async def sample_alert(
        self,
        db_session: AsyncSession,
        test_organization,
        test_user,
        sample_saved_search,
    ) -> Alert:
        """Create a sample alert for testing."""
        alert = Alert(
            organization_id=test_organization.id,
            user_id=test_user.id,
            saved_search_id=sample_saved_search.id,
            name="Test Alert",
            channel=AlertChannel.EMAIL,
            frequency="daily",
            min_results=1,
            is_active=True,
        )
        db_session.add(alert)
        await db_session.flush()
        return alert

    async def test_create_alert(
        self,
        alert_service: AlertService,
        sample_saved_search,
        test_organization,
        test_user,
    ):
        """Test creating an alert."""
        from paper_scraper.modules.alerts.schemas import AlertCreate, AlertFrequency, AlertChannel

        data = AlertCreate(
            name="New Paper Alert",
            saved_search_id=sample_saved_search.id,
            frequency=AlertFrequency.DAILY,
            min_results=5,
        )

        result = await alert_service.create(
            data=data,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert result.name == "New Paper Alert"
        assert result.saved_search_id == sample_saved_search.id
        assert result.frequency == "daily"
        assert result.min_results == 5
        assert result.is_active is True

    async def test_list_alerts(
        self,
        alert_service: AlertService,
        sample_alert: Alert,
        test_organization,
        test_user,
    ):
        """Test listing alerts."""
        results, total = await alert_service.list_alerts(
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert total >= 1
        assert any(a.id == sample_alert.id for a in results)

    async def test_toggle_alert_active(
        self,
        alert_service: AlertService,
        sample_alert: Alert,
        test_organization,
        test_user,
    ):
        """Test toggling alert active status."""
        from paper_scraper.modules.alerts.schemas import AlertUpdate

        # Deactivate
        data = AlertUpdate(is_active=False)
        result = await alert_service.update(
            alert_id=sample_alert.id,
            data=data,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert result.is_active is False

        # Reactivate
        data = AlertUpdate(is_active=True)
        result = await alert_service.update(
            alert_id=sample_alert.id,
            data=data,
            organization_id=test_organization.id,
            user_id=test_user.id,
        )

        assert result.is_active is True


# =============================================================================
# Paper Classification Tests
# =============================================================================


class TestPaperClassification:
    """Tests for paper classification."""

    async def test_paper_type_enum_values(self):
        """Test that PaperType enum has expected values."""
        assert PaperType.ORIGINAL_RESEARCH.value == "original_research"
        assert PaperType.REVIEW.value == "review"
        assert PaperType.CASE_STUDY.value == "case_study"
        assert PaperType.METHODOLOGY.value == "methodology"
        assert PaperType.THEORETICAL.value == "theoretical"
        assert PaperType.COMMENTARY.value == "commentary"
        assert PaperType.PREPRINT.value == "preprint"
        assert PaperType.OTHER.value == "other"

    async def test_paper_can_have_paper_type(
        self,
        db_session: AsyncSession,
        test_organization,
    ):
        """Test that paper model accepts paper_type field."""
        paper = Paper(
            organization_id=test_organization.id,
            title="Test Paper",
            source=PaperSource.MANUAL,
            paper_type=PaperType.ORIGINAL_RESEARCH,
        )
        db_session.add(paper)
        await db_session.flush()

        assert paper.paper_type == PaperType.ORIGINAL_RESEARCH


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestSavedSearchesAPI:
    """API tests for saved searches endpoints."""

    async def test_create_saved_search_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test POST /saved-searches endpoint."""
        response = await client.post(
            "/api/v1/saved-searches",
            json={
                "name": "API Test Search",
                "query": "genomics research",
                "mode": "hybrid",
                "is_public": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Search"
        assert data["query"] == "genomics research"

    async def test_list_saved_searches_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /saved-searches endpoint."""
        response = await client.get(
            "/api/v1/saved-searches",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.skip(reason="Requires PostgreSQL similarity() function - SQLite incompatible")
    async def test_run_saved_search_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_saved_search,
    ):
        """Test POST /saved-searches/{id}/run endpoint.

        Note: This test requires PostgreSQL as it uses the similarity() function
        for fulltext search. It will be skipped when running with SQLite.
        """
        response = await client.post(
            f"/api/v1/saved-searches/{sample_saved_search.id}/run",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestAlertsAPI:
    """API tests for alerts endpoints."""

    async def test_create_alert_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_saved_search,
    ):
        """Test POST /alerts endpoint."""
        response = await client.post(
            "/api/v1/alerts",
            json={
                "name": "API Test Alert",
                "saved_search_id": str(sample_saved_search.id),
                "frequency": "daily",
                "min_results": 1,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Alert"

    async def test_list_alerts_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /alerts endpoint."""
        response = await client.get(
            "/api/v1/alerts",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestClassificationAPI:
    """API tests for classification endpoints."""

    async def test_get_unclassified_papers_api(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /scoring/classification/unclassified endpoint."""
        response = await client.get(
            "/api/v1/scoring/classification/unclassified",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "papers" in data
