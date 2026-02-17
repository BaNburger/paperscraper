"""Tests for the model settings module.

Covers:
- CRUD operations on model configurations (create, list, update, delete)
- Hosting info retrieval
- Usage statistics (empty state)
- Default model flag toggling (creating a new default unsets the previous one)
- Nonexistent resource handling (404)
- Unauthenticated access denial (401)
- Non-admin (MEMBER) access denial for admin-only endpoints (403)
- API key secrecy (has_api_key=true, raw key never exposed)
- Tenant isolation (org B cannot see org A configurations)
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
# Fixtures
# ---------------------------------------------------------------------------

CREATE_PAYLOAD = {
    "provider": "openai",
    "model_name": "gpt-5-mini",
    "is_default": True,
    "api_key": "sk-test-key-12345",
    "hosting_info": {"region": "us-east-1", "certifications": ["SOC2", "HIPAA"]},
    "max_tokens": 4096,
    "temperature": 0.3,
}

UPDATE_PAYLOAD = {
    "model_name": "gpt-5",
    "is_default": False,
    "temperature": 0.7,
}


@pytest_asyncio.fixture
async def member_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a non-admin (MEMBER) user in the test organization."""
    user = User(
        email="member@example.com",
        hashed_password=get_password_hash("memberpassword123"),
        full_name="Member User",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def member_client(
    db_session: AsyncSession,
    member_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Independent client for MEMBER user (avoids header conflicts with authenticated_client)."""
    from paper_scraper.api.main import app
    from paper_scraper.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject=str(member_user.id),
        extra_claims={
            "org_id": str(member_user.organization_id),
            "role": member_user.role.value,
        },
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


@pytest_asyncio.fixture
async def other_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    org = Organization(
        name="Other Organization",
        type="vc",
    )
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def other_org_admin(
    db_session: AsyncSession,
    other_organization: Organization,
) -> User:
    """Create an admin user in the other organization."""
    user = User(
        email="other-admin@example.com",
        hashed_password=get_password_hash("otheradmin123"),
        full_name="Other Admin",
        organization_id=other_organization.id,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_org_client(
    db_session: AsyncSession,
    other_org_admin: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Independent client for other-org admin (avoids header conflicts with authenticated_client)."""
    from paper_scraper.api.main import app
    from paper_scraper.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject=str(other_org_admin.id),
        extra_claims={
            "org_id": str(other_org_admin.organization_id),
            "role": other_org_admin.role.value,
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


class TestModelSettingsCRUD:
    """Test create, list, update, and delete operations on model configurations."""

    @pytest.mark.asyncio
    async def test_create_model_configuration(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Creating a model configuration with valid data returns 201
        and the response matches the input."""
        response = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        assert data["model_name"] == "gpt-5-mini"
        assert data["is_default"] is True
        assert data["max_tokens"] == 4096
        assert data["temperature"] == 0.3
        assert data["hosting_info"]["region"] == "us-east-1"
        assert "id" in data
        assert "organization_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_list_models_includes_created_model(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """After creating a model, GET /models should return it in the list."""
        # Arrange: create a model
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        created_id = create_resp.json()["id"]

        # Act
        response = await authenticated_client.get("/api/v1/settings/models")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        ids = [item["id"] for item in data["items"]]
        assert created_id in ids

    @pytest.mark.asyncio
    async def test_update_model_configuration(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """PATCH /models/{id} should update only the provided fields."""
        # Arrange: create a model
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act
        response = await authenticated_client.patch(
            f"/api/v1/settings/models/{config_id}",
            json=UPDATE_PAYLOAD,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["model_name"] == "gpt-5"
        assert data["is_default"] is False
        assert data["temperature"] == 0.7
        # Fields not in the update payload should remain unchanged
        assert data["provider"] == "openai"
        assert data["max_tokens"] == 4096

    @pytest.mark.asyncio
    async def test_delete_model_configuration(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """DELETE /models/{id} should return 204 and the model should no longer
        appear in the list."""
        # Arrange
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act
        delete_resp = await authenticated_client.delete(
            f"/api/v1/settings/models/{config_id}",
        )

        # Assert
        assert delete_resp.status_code == 204

        # Verify: model should not be in the list anymore
        list_resp = await authenticated_client.get("/api/v1/settings/models")
        ids = [item["id"] for item in list_resp.json()["items"]]
        assert config_id not in ids


# ---------------------------------------------------------------------------
# Hosting Info Tests
# ---------------------------------------------------------------------------


class TestHostingInfo:
    """Test the hosting/compliance information endpoint."""

    @pytest.mark.asyncio
    async def test_get_hosting_info(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """GET /models/{id}/hosting should return hosting details with
        data_processing_region and compliance_certifications extracted
        from the hosting_info dict."""
        # Arrange
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act
        response = await authenticated_client.get(
            f"/api/v1/settings/models/{config_id}/hosting",
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["model_configuration_id"] == config_id
        assert data["provider"] == "openai"
        assert data["model_name"] == "gpt-5-mini"
        assert data["data_processing_region"] == "us-east-1"
        assert "SOC2" in data["compliance_certifications"]
        assert "HIPAA" in data["compliance_certifications"]
        assert data["hosting_info"]["region"] == "us-east-1"


# ---------------------------------------------------------------------------
# Usage Statistics Tests
# ---------------------------------------------------------------------------


class TestUsageStatistics:
    """Test the usage statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_usage_stats_empty(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """GET /models/usage should return all-zero aggregations when no
        usage records exist."""
        response = await authenticated_client.get("/api/v1/settings/models/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0
        assert data["total_input_tokens"] == 0
        assert data["total_output_tokens"] == 0
        assert data["total_tokens"] == 0
        assert data["total_cost_usd"] == 0.0
        assert data["by_operation"] == {}
        assert data["by_model"] == {}
        assert data["by_day"] == []

    @pytest.mark.asyncio
    async def test_get_usage_stats_accepts_days_parameter(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """GET /models/usage?days=7 should accept the days query parameter
        and return 200."""
        response = await authenticated_client.get(
            "/api/v1/settings/models/usage",
            params={"days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0


# ---------------------------------------------------------------------------
# Default Model Toggle Tests
# ---------------------------------------------------------------------------


class TestDefaultModelToggle:
    """Test that setting a model as default unsets any previous default."""

    @pytest.mark.asyncio
    async def test_creating_default_model_unsets_previous_default(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """When a second model is created with is_default=True, the first
        model should have its is_default flag set to False."""
        # Arrange: create first default model
        first_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert first_resp.status_code == 201
        first_id = first_resp.json()["id"]
        assert first_resp.json()["is_default"] is True

        # Act: create second default model
        second_payload = {
            "provider": "anthropic",
            "model_name": "claude-4-sonnet",
            "is_default": True,
            "max_tokens": 8192,
            "temperature": 0.5,
        }
        second_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=second_payload,
        )
        assert second_resp.status_code == 201
        assert second_resp.json()["is_default"] is True

        # Assert: list models and verify only the second one is default
        list_resp = await authenticated_client.get("/api/v1/settings/models")
        items = list_resp.json()["items"]

        defaults = [item for item in items if item["is_default"] is True]
        assert len(defaults) == 1
        assert defaults[0]["model_name"] == "claude-4-sonnet"

        # The first model should no longer be default
        first_item = next(item for item in items if item["id"] == first_id)
        assert first_item["is_default"] is False


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestModelSettingsErrors:
    """Test error responses for nonexistent resources and invalid operations."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_model_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """DELETE /models/{id} with a nonexistent UUID should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.delete(
            f"/api/v1/settings/models/{fake_id}",
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_model_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """PATCH /models/{id} with a nonexistent UUID should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.patch(
            f"/api/v1/settings/models/{fake_id}",
            json=UPDATE_PAYLOAD,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_hosting_info_nonexistent_model_returns_404(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """GET /models/{id}/hosting with a nonexistent UUID should return 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.get(
            f"/api/v1/settings/models/{fake_id}/hosting",
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------


class TestModelSettingsAuthentication:
    """Test that unauthenticated requests are rejected with 401."""

    @pytest.mark.asyncio
    async def test_list_models_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /models without an Authorization header should return 401."""
        response = await client.get("/api/v1/settings/models")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_model_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """POST /models without an Authorization header should return 401."""
        response = await client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_usage_unauthenticated_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /models/usage without auth should return 401."""
        response = await client.get("/api/v1/settings/models/usage")

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Authorization Tests (non-admin)
# ---------------------------------------------------------------------------


class TestModelSettingsAuthorization:
    """Test that MEMBER users are denied access to admin-only endpoints (403)."""

    @pytest.mark.asyncio
    async def test_create_model_as_member_returns_403(
        self,
        member_client: AsyncClient,
    ) -> None:
        """POST /models by a MEMBER user should return 403 Forbidden."""
        response = await member_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_model_as_member_returns_403(
        self,
        member_client: AsyncClient,
    ) -> None:
        """DELETE /models/{id} by a MEMBER user should return 403."""
        fake_id = str(uuid4())
        response = await member_client.delete(
            f"/api/v1/settings/models/{fake_id}",
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_model_as_member_returns_403(
        self,
        member_client: AsyncClient,
    ) -> None:
        """PATCH /models/{id} by a MEMBER user should return 403."""
        fake_id = str(uuid4())
        response = await member_client.patch(
            f"/api/v1/settings/models/{fake_id}",
            json=UPDATE_PAYLOAD,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_member_can_list_models(
        self,
        member_client: AsyncClient,
    ) -> None:
        """GET /models is accessible to MEMBER users (requires auth, not admin)."""
        response = await member_client.get("/api/v1/settings/models")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_member_can_get_usage(
        self,
        member_client: AsyncClient,
    ) -> None:
        """GET /models/usage is accessible to MEMBER users (requires auth, not admin)."""
        response = await member_client.get("/api/v1/settings/models/usage")

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# API Key Secrecy Tests
# ---------------------------------------------------------------------------


class TestAPIKeySecrecy:
    """Test that raw API keys are never exposed in responses."""

    @pytest.mark.asyncio
    async def test_api_key_not_exposed_in_create_response(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """The create response should have has_api_key=True but never contain
        the raw api_key or api_key_encrypted fields."""
        response = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["has_api_key"] is True
        assert "api_key" not in data
        assert "api_key_encrypted" not in data
        assert "sk-test-key-12345" not in str(data)

    @pytest.mark.asyncio
    async def test_api_key_not_exposed_in_list_response(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """Listed models should indicate has_api_key without exposing the key."""
        # Arrange
        await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )

        # Act
        response = await authenticated_client.get("/api/v1/settings/models")

        # Assert
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert "api_key" not in item
            assert "api_key_encrypted" not in item

    @pytest.mark.asyncio
    async def test_has_api_key_false_when_no_key_provided(
        self,
        authenticated_client: AsyncClient,
    ) -> None:
        """When creating a model without an api_key, has_api_key should be False."""
        payload_no_key = {
            "provider": "ollama",
            "model_name": "llama3",
            "is_default": False,
            "max_tokens": 2048,
            "temperature": 0.5,
        }
        response = await authenticated_client.post(
            "/api/v1/settings/models",
            json=payload_no_key,
        )

        assert response.status_code == 201
        assert response.json()["has_api_key"] is False


# ---------------------------------------------------------------------------
# Tenant Isolation Tests
# ---------------------------------------------------------------------------


class TestModelSettingsTenantIsolation:
    """Test that model configurations are isolated between organizations."""

    @pytest.mark.asyncio
    async def test_model_not_visible_to_other_organization(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """A model created by org A should not appear in org B's model list."""
        # Arrange: org A (authenticated_client) creates a model
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act: org B lists their models
        list_resp = await other_org_client.get("/api/v1/settings/models")

        # Assert: org B should not see org A's model
        assert list_resp.status_code == 200
        ids = [item["id"] for item in list_resp.json()["items"]]
        assert config_id not in ids

    @pytest.mark.asyncio
    async def test_other_org_cannot_delete_model(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """An admin from org B should not be able to delete org A's model (404
        because tenant-isolated lookup fails)."""
        # Arrange: org A creates a model
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act: org B tries to delete it
        delete_resp = await other_org_client.delete(
            f"/api/v1/settings/models/{config_id}",
        )

        # Assert: should be 404 (not found within org B's scope)
        assert delete_resp.status_code == 404

        # Verify: the model still exists for org A
        list_resp = await authenticated_client.get("/api/v1/settings/models")
        ids = [item["id"] for item in list_resp.json()["items"]]
        assert config_id in ids

    @pytest.mark.asyncio
    async def test_other_org_cannot_update_model(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """An admin from org B should not be able to update org A's model."""
        # Arrange: org A creates a model
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act: org B tries to update it
        update_resp = await other_org_client.patch(
            f"/api/v1/settings/models/{config_id}",
            json=UPDATE_PAYLOAD,
        )

        # Assert
        assert update_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_other_org_cannot_access_hosting_info(
        self,
        authenticated_client: AsyncClient,
        other_org_client: AsyncClient,
    ) -> None:
        """An authenticated user from org B should not be able to read org A's
        model hosting info."""
        # Arrange: org A creates a model
        create_resp = await authenticated_client.post(
            "/api/v1/settings/models",
            json=CREATE_PAYLOAD,
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]

        # Act: org B tries to access hosting info
        hosting_resp = await other_org_client.get(
            f"/api/v1/settings/models/{config_id}/hosting",
        )

        # Assert
        assert hosting_resp.status_code == 404
