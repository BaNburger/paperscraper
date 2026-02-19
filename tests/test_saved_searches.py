"""Tests for the saved searches module.

Covers:
- CRUD operations (create, read, update, delete)
- Duplicate name detection
- Share link generation and revocation
- Public share token access (unauthenticated)
- Executing saved searches (run)
- Unauthenticated access denial on protected endpoints
- Tenant isolation between organizations
- Ownership enforcement (ForbiddenError on non-owner actions)
- Pagination of list results
- Edge cases (empty query, nonexistent IDs, revoked tokens)
"""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.papers.models import Paper

# =============================================================================
# Constants
# =============================================================================

BASE_URL = "/api/v1/saved-searches"

VALID_SEARCH_PAYLOAD = {
    "name": "ML Research",
    "description": "Machine learning papers",
    "query": "machine learning",
    "mode": "fulltext",
    "filters": None,
    "is_public": False,
    "alert_enabled": False,
    "alert_frequency": None,
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    org = Organization(name="Second Organization", type="vc")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def second_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a second (non-admin) user in the same organization."""
    user = User(
        email="second_user@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Second User",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_org_user(
    db_session: AsyncSession,
    second_organization: Organization,
) -> User:
    """Create a user belonging to a different organization."""
    user = User(
        email="other_org@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Other Org User",
        organization_id=second_organization.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_org_client(
    db_session: AsyncSession,
    other_org_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Independent client for other-org user (avoids header conflicts)."""
    from paper_scraper.api.main import app
    from paper_scraper.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject=str(other_org_user.id),
        extra_claims={
            "org_id": str(other_org_user.organization_id),
            "role": other_org_user.role.value,
        },
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


@pytest_asyncio.fixture
async def second_user_client(
    db_session: AsyncSession,
    second_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Independent client for second user in same org (avoids header conflicts)."""
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


async def _create_saved_search(
    client: AsyncClient,
    payload: dict | None = None,
) -> dict:
    """Helper to create a saved search and return the response data."""
    body = payload or VALID_SEARCH_PAYLOAD.copy()
    response = await client.post(BASE_URL, json=body)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    return response.json()


# =============================================================================
# CRUD Tests
# =============================================================================


class TestSavedSearchCRUD:
    """Tests for saved search CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_saved_search_success(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Creating a saved search with valid data should return 201."""
        response = await authenticated_client.post(
            BASE_URL,
            json=VALID_SEARCH_PAYLOAD,
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "ML Research"
        assert data["description"] == "Machine learning papers"
        assert data["query"] == "machine learning"
        assert data["mode"] == "fulltext"
        assert data["is_public"] is False
        assert data["alert_enabled"] is False
        assert data["alert_frequency"] is None
        assert data["share_token"] is None
        assert data["share_url"] is None
        assert data["run_count"] == 0
        assert data["last_run_at"] is None
        assert data["id"] is not None
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        assert data["created_by"] is not None
        assert data["created_by"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_create_saved_search_minimal_payload(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Creating a saved search with only required fields should succeed."""
        response = await authenticated_client.post(
            BASE_URL,
            json={
                "name": "Quick Search",
                "query": "quantum computing",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Quick Search"
        assert data["query"] == "quantum computing"
        # Defaults
        assert data["mode"] == "hybrid"
        assert data["is_public"] is False
        assert data["alert_enabled"] is False

    @pytest.mark.asyncio
    async def test_create_saved_search_with_alert_config(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Creating a saved search with alerts enabled should persist alert settings."""
        payload = {
            "name": "Alerted Search",
            "query": "CRISPR gene editing",
            "mode": "semantic",
            "alert_enabled": True,
            "alert_frequency": "daily",
        }
        response = await authenticated_client.post(BASE_URL, json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["alert_enabled"] is True
        assert data["alert_frequency"] == "daily"

    @pytest.mark.asyncio
    async def test_create_duplicate_name_fails(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Creating a second saved search with the same name should return 409."""
        # First creation
        await _create_saved_search(authenticated_client)

        # Duplicate name
        response = await authenticated_client.post(
            BASE_URL,
            json=VALID_SEARCH_PAYLOAD,
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_same_name_different_users_allowed(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """Different users in the same org can have saved searches with the same name."""
        # User 1 creates
        response1 = await authenticated_client.post(
            BASE_URL,
            json=VALID_SEARCH_PAYLOAD,
        )
        assert response1.status_code == 201

        # User 2 creates with same name -- should succeed (different user scope)
        response2 = await second_user_client.post(
            BASE_URL,
            json=VALID_SEARCH_PAYLOAD,
        )
        assert response2.status_code == 201

    @pytest.mark.asyncio
    async def test_create_saved_search_empty_name_rejected(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """An empty name should be rejected by Pydantic validation (422)."""
        response = await authenticated_client.post(
            BASE_URL,
            json={"name": "", "query": "test"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_saved_search_empty_query_rejected(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """An empty query should be rejected by Pydantic validation (422)."""
        response = await authenticated_client.post(
            BASE_URL,
            json={"name": "Valid Name", "query": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_saved_searches(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Listing saved searches should return paginated results."""
        # Create two searches
        await _create_saved_search(
            authenticated_client,
            {"name": "Search A", "query": "alpha"},
        )
        await _create_saved_search(
            authenticated_client,
            {"name": "Search B", "query": "beta"},
        )

        response = await authenticated_client.get(BASE_URL)
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_saved_searches_pagination(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Listing with page_size=1 should paginate correctly."""
        await _create_saved_search(
            authenticated_client,
            {"name": "Page 1", "query": "first"},
        )
        await _create_saved_search(
            authenticated_client,
            {"name": "Page 2", "query": "second"},
        )

        response = await authenticated_client.get(BASE_URL, params={"page": 1, "page_size": 1})
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2
        assert data["pages"] == 2
        assert len(data["items"]) == 1

    @pytest.mark.asyncio
    async def test_list_includes_public_searches_from_org(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """Public searches from other users in the same org should be visible."""
        # Second user creates a public search
        await _create_saved_search(
            second_user_client,
            {"name": "Public Search", "query": "public query", "is_public": True},
        )

        # First user should see it in their list
        response = await authenticated_client.get(BASE_URL)
        assert response.status_code == 200

        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert "Public Search" in names

    @pytest.mark.asyncio
    async def test_list_excludes_public_when_include_public_false(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """Setting include_public=false should exclude other users' public searches."""
        # Second user creates a public search
        await _create_saved_search(
            second_user_client,
            {"name": "Public Search", "query": "public query", "is_public": True},
        )

        response = await authenticated_client.get(BASE_URL, params={"include_public": False})
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_saved_search_by_id(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Getting a saved search by ID should return the correct data."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await authenticated_client.get(f"{BASE_URL}/{search_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == search_id
        assert data["name"] == "ML Research"
        assert data["query"] == "machine learning"

    @pytest.mark.asyncio
    async def test_get_nonexistent_saved_search_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Getting a non-existent saved search should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.get(f"{BASE_URL}/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_saved_search(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Updating a saved search should apply the changes."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        update_payload = {
            "name": "Updated ML Research",
            "description": "Updated description",
            "query": "deep learning",
            "is_public": True,
        }
        response = await authenticated_client.patch(
            f"{BASE_URL}/{search_id}",
            json=update_payload,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated ML Research"
        assert data["description"] == "Updated description"
        assert data["query"] == "deep learning"
        assert data["is_public"] is True
        # Unchanged fields
        assert data["mode"] == "fulltext"

    @pytest.mark.asyncio
    async def test_update_name_to_duplicate_fails(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Updating a saved search name to a name that already exists should return 409."""
        await _create_saved_search(
            authenticated_client,
            {"name": "First Search", "query": "first"},
        )
        second = await _create_saved_search(
            authenticated_client,
            {"name": "Second Search", "query": "second"},
        )

        response = await authenticated_client.patch(
            f"{BASE_URL}/{second['id']}",
            json={"name": "First Search"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Updating a non-existent saved search should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.patch(
            f"{BASE_URL}/{fake_id}",
            json={"name": "Ghost"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_saved_search(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Deleting a saved search should return 204 and remove it."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Delete
        response = await authenticated_client.delete(f"{BASE_URL}/{search_id}")
        assert response.status_code == 204

        # Verify it is gone
        response = await authenticated_client.get(f"{BASE_URL}/{search_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Deleting a non-existent saved search should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.delete(f"{BASE_URL}/{fake_id}")
        assert response.status_code == 404


# =============================================================================
# Share Link Tests
# =============================================================================


class TestSavedSearchSharing:
    """Tests for share link generation, access, and revocation."""

    @pytest.mark.asyncio
    async def test_generate_share_link(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Generating a share link should return a share_token and share_url."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await authenticated_client.post(f"{BASE_URL}/{search_id}/share")
        assert response.status_code == 200

        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
        assert data["share_token"] is not None
        assert len(data["share_token"]) > 0
        assert data["share_token"] in data["share_url"]

    @pytest.mark.asyncio
    async def test_get_shared_search_via_token_no_auth(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient,
    ) -> None:
        """Accessing a shared search via share token should work without auth."""
        # Create and share with authenticated client
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        share_response = await authenticated_client.post(f"{BASE_URL}/{search_id}/share")
        share_token = share_response.json()["share_token"]

        # Access via unauthenticated client
        # Remove auth header to simulate unauthenticated access
        unauthenticated_client = AsyncClient(
            transport=client._transport,
            base_url=str(client.base_url),
        )
        async with unauthenticated_client:
            response = await unauthenticated_client.get(f"{BASE_URL}/shared/{share_token}")
            assert response.status_code == 200

            data = response.json()
            assert data["id"] == search_id
            assert data["name"] == "ML Research"
            assert data["query"] == "machine learning"

    @pytest.mark.asyncio
    async def test_get_shared_search_invalid_token_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Accessing a shared search with an invalid token should return 404."""
        response = await client.get(f"{BASE_URL}/shared/nonexistent_token_abc123")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_share_link(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient,
    ) -> None:
        """Revoking a share link should return 204 and invalidate the token."""
        # Create and share
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        share_response = await authenticated_client.post(f"{BASE_URL}/{search_id}/share")
        share_token = share_response.json()["share_token"]

        # Revoke
        revoke_response = await authenticated_client.delete(f"{BASE_URL}/{search_id}/share")
        assert revoke_response.status_code == 204

        # Token should no longer work
        response = await client.get(f"{BASE_URL}/shared/{share_token}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_share_link_replaces_existing_token(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Generating a share link a second time should produce a new token."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # First share
        response1 = await authenticated_client.post(f"{BASE_URL}/{search_id}/share")
        token1 = response1.json()["share_token"]

        # Second share
        response2 = await authenticated_client.post(f"{BASE_URL}/{search_id}/share")
        token2 = response2.json()["share_token"]

        assert token1 != token2

    @pytest.mark.asyncio
    async def test_share_link_reflects_in_get_response(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """After generating a share link, GET should include the share_token and share_url."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        share_response = await authenticated_client.post(f"{BASE_URL}/{search_id}/share")
        share_token = share_response.json()["share_token"]

        get_response = await authenticated_client.get(f"{BASE_URL}/{search_id}")
        data = get_response.json()
        assert data["share_token"] == share_token
        assert data["share_url"] is not None
        assert share_token in data["share_url"]


# =============================================================================
# Run (Execute) Tests
# =============================================================================


class TestSavedSearchRun:
    """Tests for executing a saved search."""

    @pytest.mark.asyncio
    async def test_run_saved_search_returns_search_results(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
    ) -> None:
        """Running a saved search should return search results and increment run_count."""
        # Create a paper so fulltext search has something to find
        paper = Paper(
            title="Machine Learning Advances",
            abstract="Recent advances in machine learning and deep learning techniques",
            source="openalex",
            organization_id=test_organization.id,
        )
        db_session.add(paper)
        await db_session.flush()

        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await authenticated_client.post(f"{BASE_URL}/{search_id}/run")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "machine learning"

    @pytest.mark.asyncio
    async def test_run_increments_run_count(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Running a saved search should increment the run_count."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]
        assert created["run_count"] == 0

        # Run once
        await authenticated_client.post(f"{BASE_URL}/{search_id}/run")

        # Fetch and check run_count
        get_response = await authenticated_client.get(f"{BASE_URL}/{search_id}")
        data = get_response.json()
        assert data["run_count"] == 1
        assert data["last_run_at"] is not None

    @pytest.mark.asyncio
    async def test_run_nonexistent_search_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Running a non-existent saved search should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(f"{BASE_URL}/{fake_id}/run")
        assert response.status_code == 404


# =============================================================================
# Authentication Tests
# =============================================================================


class TestSavedSearchAuthentication:
    """Tests that protected endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_create_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Creating a saved search without auth should return 401."""
        response = await client.post(BASE_URL, json=VALID_SEARCH_PAYLOAD)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Listing saved searches without auth should return 401."""
        response = await client.get(BASE_URL)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_by_id_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Getting a saved search by ID without auth should return 401."""
        fake_id = str(uuid4())
        response = await client.get(f"{BASE_URL}/{fake_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Updating a saved search without auth should return 401."""
        fake_id = str(uuid4())
        response = await client.patch(f"{BASE_URL}/{fake_id}", json={"name": "Hacked"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Deleting a saved search without auth should return 401."""
        fake_id = str(uuid4())
        response = await client.delete(f"{BASE_URL}/{fake_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_share_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Generating a share link without auth should return 401."""
        fake_id = str(uuid4())
        response = await client.post(f"{BASE_URL}/{fake_id}/share")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_share_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Revoking a share link without auth should return 401."""
        fake_id = str(uuid4())
        response = await client.delete(f"{BASE_URL}/{fake_id}/share")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_run_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Running a saved search without auth should return 401."""
        fake_id = str(uuid4())
        response = await client.post(f"{BASE_URL}/{fake_id}/run")
        assert response.status_code == 401


# =============================================================================
# Tenant Isolation Tests
# =============================================================================


class TestSavedSearchTenantIsolation:
    """Tests that saved searches respect organization boundaries."""

    @pytest.mark.asyncio
    async def test_search_not_visible_to_other_organization(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """A saved search in org A should not appear in org B's list."""
        await _create_saved_search(authenticated_client)

        response = await other_org_client.get(BASE_URL)
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_by_id_cross_org_returns_404(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """Getting a saved search from another org by ID should return 404."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await other_org_client.get(f"{BASE_URL}/{search_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_cross_org_returns_404(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """Updating a saved search from another org should return 404."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await other_org_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"name": "Hijacked"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cross_org_returns_404(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """Deleting a saved search from another org should return 404."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await other_org_client.delete(f"{BASE_URL}/{search_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_share_cross_org_returns_404(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """Generating a share link for a search in another org should return 404."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await other_org_client.post(f"{BASE_URL}/{search_id}/share")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_cross_org_returns_404(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """Running a saved search from another org should return 404."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        response = await other_org_client.post(f"{BASE_URL}/{search_id}/run")
        assert response.status_code == 404


# =============================================================================
# Ownership Enforcement Tests
# =============================================================================


class TestSavedSearchOwnership:
    """Tests that only the owner can modify or share a saved search."""

    @pytest.mark.asyncio
    async def test_non_owner_cannot_update(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """A user who is not the owner should get 403 when updating."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Make it public so second user can see it
        await authenticated_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"is_public": True},
        )

        # Second user tries to update -- should fail
        response = await second_user_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"name": "Hijacked Name"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_owner_cannot_delete(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """A user who is not the owner should get 403 when deleting."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Make it public so second user can find it
        await authenticated_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"is_public": True},
        )

        response = await second_user_client.delete(f"{BASE_URL}/{search_id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_owner_cannot_generate_share_link(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """A user who is not the owner should get 403 when generating a share link."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Make it public so second user can find it
        await authenticated_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"is_public": True},
        )

        response = await second_user_client.post(f"{BASE_URL}/{search_id}/share")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_owner_cannot_revoke_share_link(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """A user who is not the owner should get 403 when revoking a share link."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Share it first
        await authenticated_client.post(f"{BASE_URL}/{search_id}/share")

        # Make public so second user can find it
        await authenticated_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"is_public": True},
        )

        response = await second_user_client.delete(f"{BASE_URL}/{search_id}/share")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_owner_can_read_public_search(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """A user who is not the owner should be able to read a public search."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Make it public
        await authenticated_client.patch(
            f"{BASE_URL}/{search_id}",
            json={"is_public": True},
        )

        response = await second_user_client.get(f"{BASE_URL}/{search_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == search_id

    @pytest.mark.asyncio
    async def test_non_owner_cannot_read_private_search(
        self,
        authenticated_client: AsyncClient,
        second_user_client: AsyncClient,
    ) -> None:
        """A user who is not the owner should get 403 when reading a private search."""
        created = await _create_saved_search(authenticated_client)
        search_id = created["id"]

        # Search is private by default
        response = await second_user_client.get(f"{BASE_URL}/{search_id}")
        assert response.status_code == 403


# =============================================================================
# Response Schema Validation Tests
# =============================================================================


class TestSavedSearchResponseSchema:
    """Tests verifying the response schema structure."""

    @pytest.mark.asyncio
    async def test_response_contains_all_expected_fields(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """The response should contain all documented fields."""
        created = await _create_saved_search(authenticated_client)

        expected_fields = {
            "id",
            "name",
            "description",
            "query",
            "mode",
            "filters",
            "is_public",
            "share_token",
            "share_url",
            "alert_enabled",
            "alert_frequency",
            "last_alert_at",
            "run_count",
            "last_run_at",
            "created_at",
            "updated_at",
            "created_by",
        }
        assert expected_fields.issubset(set(created.keys()))

    @pytest.mark.asyncio
    async def test_created_by_contains_user_info(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """The created_by field should contain user id, email, and full_name."""
        created = await _create_saved_search(authenticated_client)

        creator = created["created_by"]
        assert "id" in creator
        assert "email" in creator
        assert "full_name" in creator
        assert creator["email"] == "test@example.com"
        assert creator["full_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_list_response_schema(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """The list response should have items, total, page, page_size, pages."""
        await _create_saved_search(authenticated_client)

        response = await authenticated_client.get(BASE_URL)
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    @pytest.mark.asyncio
    async def test_filters_defaults_to_empty_dict(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """When no filters are provided, the response should have an empty dict."""
        created = await _create_saved_search(authenticated_client)
        assert created["filters"] == {}
