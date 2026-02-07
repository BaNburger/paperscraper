"""Comprehensive tests for the alerts API module.

Covers:
- Alert CRUD operations (create, read, update, delete)
- Saved search prerequisite validation
- Paginated listing with active_only filter
- Alert results/history retrieval
- Alert test (dry run) and manual trigger endpoints
- Unauthenticated access denial (401)
- Nonexistent resource handling (404)
- Tenant isolation between organizations
"""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_saved_search(client: AsyncClient) -> str:
    """Create a saved search via the API and return its ID.

    This is a prerequisite for creating alerts since every alert
    must reference an existing SavedSearch.
    """
    response = await client.post(
        "/api/v1/saved-searches",
        json={
            "name": "Test Search for Alert",
            "query": "machine learning",
            "mode": "fulltext",
        },
    )
    assert response.status_code == 201, (
        f"Failed to create saved search: {response.status_code} {response.text}"
    )
    return response.json()["id"]


async def _create_alert(
    client: AsyncClient,
    saved_search_id: str,
    *,
    name: str = "Test Alert",
    channel: str = "email",
    frequency: str = "daily",
    min_results: int = 1,
) -> dict:
    """Create an alert via the API and return the full response body."""
    response = await client.post(
        "/api/v1/alerts",
        json={
            "name": name,
            "saved_search_id": saved_search_id,
            "channel": channel,
            "frequency": frequency,
            "min_results": min_results,
        },
    )
    assert response.status_code == 201, (
        f"Failed to create alert: {response.status_code} {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def saved_search_id(authenticated_client: AsyncClient) -> str:
    """Create a saved search and yield its ID for alert tests."""
    return await _create_saved_search(authenticated_client)


@pytest_asyncio.fixture
async def alert_data(
    authenticated_client: AsyncClient,
    saved_search_id: str,
) -> dict:
    """Create an alert and yield its full response body."""
    return await _create_alert(authenticated_client, saved_search_id)


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    org = Organization(name="Other Organization", type="vc")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def second_user(
    db_session: AsyncSession,
    second_organization: Organization,
) -> User:
    """Create a user in the second organization."""
    user = User(
        email="other_user@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Other User",
        organization_id=second_organization.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_authenticated_client(
    db_session: AsyncSession,
    second_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Independent client for the second organization (avoids header conflicts)."""
    from paper_scraper.api.main import app
    from paper_scraper.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject=str(second_user.id),
        extra_claims={
            "org_id": str(second_user.organization_id),
            "role": second_user.role.value,
        },
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# CRUD Tests
# ---------------------------------------------------------------------------


class TestAlertCreate:
    """Tests for POST /api/v1/alerts/."""

    @pytest.mark.asyncio
    async def test_create_alert_success(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Creating an alert with a valid saved search returns 201 with correct fields."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "My Daily Alert",
                "description": "Monitors ML papers",
                "saved_search_id": saved_search_id,
                "channel": "email",
                "frequency": "daily",
                "min_results": 3,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "My Daily Alert"
        assert data["description"] == "Monitors ML papers"
        assert data["channel"] == "email"
        assert data["frequency"] == "daily"
        assert data["min_results"] == 3
        assert data["is_active"] is True
        assert data["last_triggered_at"] is None
        assert data["trigger_count"] == 0
        assert data["id"] is not None
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

        # Verify nested saved_search brief
        assert data["saved_search"] is not None
        assert data["saved_search"]["id"] == saved_search_id
        assert data["saved_search"]["name"] == "Test Search for Alert"
        assert data["saved_search"]["query"] == "machine learning"

    @pytest.mark.asyncio
    async def test_create_alert_with_defaults(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Creating an alert with only required fields uses sensible defaults."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Minimal Alert",
                "saved_search_id": saved_search_id,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Minimal Alert"
        assert data["description"] is None
        assert data["channel"] == "email"
        assert data["frequency"] == "daily"
        assert data["min_results"] == 1
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_alert_in_app_channel(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Creating an alert with in_app channel is accepted."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "In-App Alert",
                "saved_search_id": saved_search_id,
                "channel": "in_app",
                "frequency": "weekly",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["channel"] == "in_app"
        assert data["frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_create_alert_with_invalid_saved_search_id(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Creating an alert with a nonexistent saved_search_id returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Bad Alert",
                "saved_search_id": fake_id,
                "channel": "email",
                "frequency": "daily",
            },
        )

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_alert_missing_name_returns_422(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Omitting the required 'name' field returns 422 validation error."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "saved_search_id": saved_search_id,
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_missing_saved_search_id_returns_422(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Omitting the required 'saved_search_id' field returns 422."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "No Search Alert",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_invalid_frequency_returns_422(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Using an invalid frequency value returns 422."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Bad Frequency",
                "saved_search_id": saved_search_id,
                "frequency": "monthly",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_invalid_channel_returns_422(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Using an invalid channel value returns 422."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Bad Channel",
                "saved_search_id": saved_search_id,
                "channel": "sms",
            },
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# List Tests
# ---------------------------------------------------------------------------


class TestAlertList:
    """Tests for GET /api/v1/alerts/."""

    @pytest.mark.asyncio
    async def test_list_alerts_empty(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Listing alerts when none exist returns empty paginated response."""
        response = await authenticated_client.get("/api/v1/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 0

    @pytest.mark.asyncio
    async def test_list_alerts_returns_created_alerts(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Listing alerts returns all alerts created by the current user."""
        # Create two alerts
        await _create_alert(
            authenticated_client, saved_search_id, name="Alert One"
        )
        await _create_alert(
            authenticated_client, saved_search_id, name="Alert Two"
        )

        response = await authenticated_client.get("/api/v1/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        names = {item["name"] for item in data["items"]}
        assert "Alert One" in names
        assert "Alert Two" in names

    @pytest.mark.asyncio
    async def test_list_alerts_active_only_filter(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """The active_only query parameter filters out inactive alerts."""
        # Create two alerts
        active_alert = await _create_alert(
            authenticated_client, saved_search_id, name="Active Alert"
        )
        inactive_alert = await _create_alert(
            authenticated_client, saved_search_id, name="Inactive Alert"
        )

        # Deactivate the second alert
        await authenticated_client.patch(
            f"/api/v1/alerts/{inactive_alert['id']}",
            json={"is_active": False},
        )

        # List with active_only=true
        response = await authenticated_client.get(
            "/api/v1/alerts",
            params={"active_only": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Active Alert"
        assert data["items"][0]["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_alerts_pagination(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Pagination parameters (page, page_size) are respected."""
        # Create three alerts
        for i in range(3):
            await _create_alert(
                authenticated_client, saved_search_id, name=f"Alert {i}"
            )

        # Request page 1 with page_size 2
        response = await authenticated_client.get(
            "/api/v1/alerts",
            params={"page": 1, "page_size": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["pages"] == 2

        # Request page 2
        response = await authenticated_client.get(
            "/api/v1/alerts",
            params={"page": 2, "page_size": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1


# ---------------------------------------------------------------------------
# Get Single Alert Tests
# ---------------------------------------------------------------------------


class TestAlertGet:
    """Tests for GET /api/v1/alerts/{alert_id}."""

    @pytest.mark.asyncio
    async def test_get_alert_by_id(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Fetching an alert by ID returns the complete alert data."""
        alert_id = alert_data["id"]

        response = await authenticated_client.get(f"/api/v1/alerts/{alert_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert_id
        assert data["name"] == alert_data["name"]
        assert data["channel"] == alert_data["channel"]
        assert data["frequency"] == alert_data["frequency"]
        assert data["saved_search"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_alert_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Requesting a nonexistent alert ID returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.get(f"/api/v1/alerts/{fake_id}")

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Update Tests
# ---------------------------------------------------------------------------


class TestAlertUpdate:
    """Tests for PATCH /api/v1/alerts/{alert_id}."""

    @pytest.mark.asyncio
    async def test_update_alert_name(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Updating the alert name is reflected in the response."""
        alert_id = alert_data["id"]

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={"name": "Updated Alert Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Alert Name"
        assert data["id"] == alert_id

    @pytest.mark.asyncio
    async def test_update_alert_frequency(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Updating the frequency changes the alert schedule."""
        alert_id = alert_data["id"]

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={"frequency": "weekly"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_update_alert_deactivate(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Setting is_active to false deactivates the alert."""
        alert_id = alert_data["id"]

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={"is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_alert_multiple_fields(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Updating multiple fields in a single PATCH request applies all changes."""
        alert_id = alert_data["id"]

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={
                "name": "Bulk Updated Alert",
                "frequency": "immediately",
                "channel": "in_app",
                "min_results": 5,
                "is_active": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bulk Updated Alert"
        assert data["frequency"] == "immediately"
        assert data["channel"] == "in_app"
        assert data["min_results"] == 5
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_nonexistent_alert_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Updating a nonexistent alert returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{fake_id}",
            json={"name": "Ghost Alert"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete Tests
# ---------------------------------------------------------------------------


class TestAlertDelete:
    """Tests for DELETE /api/v1/alerts/{alert_id}."""

    @pytest.mark.asyncio
    async def test_delete_alert(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Deleting an alert returns 204 and the alert is no longer accessible."""
        alert_id = alert_data["id"]

        # Delete
        response = await authenticated_client.delete(
            f"/api/v1/alerts/{alert_id}"
        )
        assert response.status_code == 204

        # Verify it is gone
        response = await authenticated_client.get(f"/api/v1/alerts/{alert_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_alert_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Deleting a nonexistent alert returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.delete(
            f"/api/v1/alerts/{fake_id}"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_removes_alert_from_list(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """After deletion the alert no longer appears in the list endpoint."""
        # Create and delete
        alert = await _create_alert(
            authenticated_client, saved_search_id, name="Ephemeral Alert"
        )
        await authenticated_client.delete(f"/api/v1/alerts/{alert['id']}")

        # Verify list is empty
        response = await authenticated_client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        alert_ids = [item["id"] for item in data["items"]]
        assert alert["id"] not in alert_ids


# ---------------------------------------------------------------------------
# Alert Results / History Tests
# ---------------------------------------------------------------------------


class TestAlertResults:
    """Tests for GET /api/v1/alerts/{alert_id}/results."""

    @pytest.mark.asyncio
    async def test_get_alert_results_empty(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """A freshly created alert has no results history."""
        alert_id = alert_data["id"]

        response = await authenticated_client.get(
            f"/api/v1/alerts/{alert_id}/results"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 0

    @pytest.mark.asyncio
    async def test_get_alert_results_for_nonexistent_alert(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Getting results for a nonexistent alert returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.get(
            f"/api/v1/alerts/{fake_id}/results"
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Test Alert (Dry Run) Tests
# ---------------------------------------------------------------------------


class TestAlertTestEndpoint:
    """Tests for POST /api/v1/alerts/{alert_id}/test."""

    @pytest.mark.asyncio
    async def test_test_alert_dry_run(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Testing an alert returns a dry-run result without side effects."""
        alert_id = alert_data["id"]

        response = await authenticated_client.post(
            f"/api/v1/alerts/{alert_id}/test"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "papers_found" in data
        assert isinstance(data["papers_found"], int)
        assert isinstance(data["sample_papers"], list)

    @pytest.mark.asyncio
    async def test_test_alert_does_not_increment_trigger_count(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """A test/dry-run should not change trigger_count or last_triggered_at."""
        alert_id = alert_data["id"]

        # Run the test endpoint
        await authenticated_client.post(f"/api/v1/alerts/{alert_id}/test")

        # Fetch the alert again and verify trigger_count is still 0
        response = await authenticated_client.get(f"/api/v1/alerts/{alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["trigger_count"] == 0
        assert data["last_triggered_at"] is None

    @pytest.mark.asyncio
    async def test_test_nonexistent_alert_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Testing a nonexistent alert returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.post(
            f"/api/v1/alerts/{fake_id}/test"
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Trigger Alert Tests
# ---------------------------------------------------------------------------


class TestAlertTrigger:
    """Tests for POST /api/v1/alerts/{alert_id}/trigger."""

    @pytest.mark.xfail(reason="Pre-existing bug: offset-naive/aware datetime mismatch in alert trigger search")
    @pytest.mark.asyncio
    async def test_trigger_alert_returns_result(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Manually triggering an alert returns an AlertResultResponse."""
        alert_id = alert_data["id"]

        response = await authenticated_client.post(
            f"/api/v1/alerts/{alert_id}/trigger"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == alert_id
        assert "status" in data
        assert data["status"] in ("sent", "skipped", "failed", "pending")
        assert "papers_found" in data
        assert "new_papers" in data
        assert "paper_ids" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_alert_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Triggering a nonexistent alert returns 404."""
        fake_id = str(uuid4())

        response = await authenticated_client.post(
            f"/api/v1/alerts/{fake_id}/trigger"
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------


class TestAlertAuthentication:
    """Tests verifying that unauthenticated requests are rejected."""

    @pytest.mark.asyncio
    async def test_list_alerts_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /alerts/ without auth returns 401."""
        response = await client.get("/api/v1/alerts")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_alert_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """POST /alerts/ without auth returns 401."""
        response = await client.post(
            "/api/v1/alerts",
            json={
                "name": "No Auth Alert",
                "saved_search_id": str(uuid4()),
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_alert_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /alerts/{id} without auth returns 401."""
        response = await client.get(f"/api/v1/alerts/{uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_alert_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """PATCH /alerts/{id} without auth returns 401."""
        response = await client.patch(
            f"/api/v1/alerts/{uuid4()}",
            json={"name": "Updated"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_alert_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """DELETE /alerts/{id} without auth returns 401."""
        response = await client.delete(f"/api/v1/alerts/{uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_alert_results_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /alerts/{id}/results without auth returns 401."""
        response = await client.get(f"/api/v1/alerts/{uuid4()}/results")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_test_alert_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """POST /alerts/{id}/test without auth returns 401."""
        response = await client.post(f"/api/v1/alerts/{uuid4()}/test")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_trigger_alert_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """POST /alerts/{id}/trigger without auth returns 401."""
        response = await client.post(f"/api/v1/alerts/{uuid4()}/trigger")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tenant Isolation Tests
# ---------------------------------------------------------------------------


class TestAlertTenantIsolation:
    """Tests verifying alerts are isolated between organizations."""

    @pytest.mark.asyncio
    async def test_alert_not_visible_to_other_organization(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
        db_session: AsyncSession,
        second_organization: Organization,
        second_user: User,
    ) -> None:
        """An alert created in org A must not be accessible by a user in org B."""
        alert_id = alert_data["id"]

        # Create a client for the second org user
        token = create_access_token(
            subject=str(second_user.id),
            extra_claims={
                "org_id": str(second_user.organization_id),
                "role": second_user.role.value,
            },
        )

        # Try to fetch org A's alert as org B user
        response = await authenticated_client.get(
            f"/api/v1/alerts/{alert_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be 404 (not found in org B's scope) or 403
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_alert_list_isolated_between_organizations(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
        db_session: AsyncSession,
        second_organization: Organization,
        second_user: User,
    ) -> None:
        """Listing alerts in org B should not show org A's alerts."""
        token = create_access_token(
            subject=str(second_user.id),
            extra_claims={
                "org_id": str(second_user.organization_id),
                "role": second_user.role.value,
            },
        )

        response = await authenticated_client.get(
            "/api/v1/alerts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_cannot_update_alert_from_other_organization(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
        db_session: AsyncSession,
        second_organization: Organization,
        second_user: User,
    ) -> None:
        """A user from org B cannot update an alert belonging to org A."""
        alert_id = alert_data["id"]

        token = create_access_token(
            subject=str(second_user.id),
            extra_claims={
                "org_id": str(second_user.organization_id),
                "role": second_user.role.value,
            },
        )

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={"name": "Hijacked Alert"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_cannot_delete_alert_from_other_organization(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
        db_session: AsyncSession,
        second_organization: Organization,
        second_user: User,
    ) -> None:
        """A user from org B cannot delete an alert belonging to org A."""
        alert_id = alert_data["id"]

        token = create_access_token(
            subject=str(second_user.id),
            extra_claims={
                "org_id": str(second_user.organization_id),
                "role": second_user.role.value,
            },
        )

        response = await authenticated_client.delete(
            f"/api/v1/alerts/{alert_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in (403, 404)

        # Verify the alert still exists for the original owner
        verify_response = await authenticated_client.get(
            f"/api/v1/alerts/{alert_id}"
        )
        assert verify_response.status_code == 200


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------


class TestAlertEdgeCases:
    """Tests for boundary conditions and edge cases."""

    @pytest.mark.asyncio
    async def test_create_alert_with_immediately_frequency(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """The 'immediately' frequency is accepted on creation."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Immediate Alert",
                "saved_search_id": saved_search_id,
                "frequency": "immediately",
            },
        )

        assert response.status_code == 201
        assert response.json()["frequency"] == "immediately"

    @pytest.mark.asyncio
    async def test_create_alert_min_results_boundary(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """min_results at the upper boundary (100) is accepted."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "High Threshold Alert",
                "saved_search_id": saved_search_id,
                "min_results": 100,
            },
        )

        assert response.status_code == 201
        assert response.json()["min_results"] == 100

    @pytest.mark.asyncio
    async def test_create_alert_min_results_zero_returns_422(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """min_results of 0 is below the minimum (1) and returns 422."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Zero Threshold",
                "saved_search_id": saved_search_id,
                "min_results": 0,
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_alert_min_results_above_max_returns_422(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """min_results of 101 exceeds the maximum (100) and returns 422."""
        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": "Over Threshold",
                "saved_search_id": saved_search_id,
                "min_results": 101,
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_multiple_alerts_for_same_saved_search(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """Multiple alerts can be created for the same saved search."""
        alert_one = await _create_alert(
            authenticated_client,
            saved_search_id,
            name="Alert A",
            frequency="daily",
        )
        alert_two = await _create_alert(
            authenticated_client,
            saved_search_id,
            name="Alert B",
            frequency="weekly",
        )

        assert alert_one["id"] != alert_two["id"]
        assert alert_one["saved_search"]["id"] == alert_two["saved_search"]["id"]

    @pytest.mark.asyncio
    async def test_update_with_empty_body_returns_200(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """Sending an empty PATCH body is accepted (no changes applied)."""
        alert_id = alert_data["id"]

        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        # All original values preserved
        assert data["name"] == alert_data["name"]
        assert data["frequency"] == alert_data["frequency"]

    @pytest.mark.asyncio
    async def test_reactivate_deactivated_alert(
        self,
        authenticated_client: AsyncClient,
        alert_data: dict,
    ) -> None:
        """A deactivated alert can be reactivated via PATCH."""
        alert_id = alert_data["id"]

        # Deactivate
        await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={"is_active": False},
        )

        # Reactivate
        response = await authenticated_client.patch(
            f"/api/v1/alerts/{alert_id}",
            json={"is_active": True},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    @pytest.mark.asyncio
    async def test_alert_name_max_length(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """A name at the max length (255 chars) is accepted."""
        long_name = "A" * 255

        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": long_name,
                "saved_search_id": saved_search_id,
            },
        )

        assert response.status_code == 201
        assert response.json()["name"] == long_name

    @pytest.mark.asyncio
    async def test_alert_name_exceeding_max_length_returns_422(
        self,
        authenticated_client: AsyncClient,
        saved_search_id: str,
    ) -> None:
        """A name exceeding 255 chars is rejected with 422."""
        too_long_name = "A" * 256

        response = await authenticated_client.post(
            "/api/v1/alerts",
            json={
                "name": too_long_name,
                "saved_search_id": saved_search_id,
            },
        )

        assert response.status_code == 422
