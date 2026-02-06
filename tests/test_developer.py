"""Tests for developer module: API keys, webhooks, and repository sources."""

import pytest
import pytest_asyncio
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.developer.models import (
    APIKey,
    Webhook,
    RepositorySource,
    WebhookEvent,
    RepositoryProvider,
)
from paper_scraper.modules.developer import service
from paper_scraper.modules.developer.schemas import (
    APIKeyCreate,
    WebhookCreate,
    WebhookUpdate,
    RepositorySourceCreate,
    RepositorySourceUpdate,
    RepositorySourceConfig,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_api_key(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> tuple[APIKey, str]:
    """Create a test API key and return both the model and plain key."""
    data = APIKeyCreate(
        name="Test Key",
        permissions=["papers:read", "search:query"],
    )
    api_key, plain_key = await service.create_api_key(
        db_session, test_organization.id, test_user.id, data
    )
    await db_session.flush()
    return api_key, plain_key


@pytest_asyncio.fixture
async def test_webhook(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> Webhook:
    """Create a test webhook."""
    data = WebhookCreate(
        name="Test Webhook",
        url="https://example.com/webhook",
        events=[WebhookEvent.PAPER_CREATED, WebhookEvent.PAPER_SCORED],
    )
    webhook = await service.create_webhook(
        db_session, test_organization.id, test_user.id, data
    )
    await db_session.flush()
    return webhook


@pytest_asyncio.fixture
async def test_repository(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> RepositorySource:
    """Create a test repository source."""
    data = RepositorySourceCreate(
        name="Test Source",
        provider=RepositoryProvider.OPENALEX,
        config=RepositorySourceConfig(
            query="machine learning",
            max_results=50,
        ),
    )
    source = await service.create_repository_source(
        db_session, test_organization.id, test_user.id, data
    )
    await db_session.flush()
    return source


@pytest_asyncio.fixture
async def admin_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create an admin user."""
    from paper_scraper.core.security import get_password_hash

    user = User(
        email=f"admin-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Admin User",
        organization_id=test_organization.id,
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def member_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a member (non-admin) user."""
    from paper_scraper.core.security import get_password_hash

    user = User(
        email=f"member-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Member User",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def member_client(
    client: AsyncClient,
    member_user: User,
) -> AsyncClient:
    """Create an authenticated client for member user."""
    from paper_scraper.core.security import create_access_token

    token = create_access_token(
        str(member_user.id),
        extra_claims={
            "org_id": str(member_user.organization_id),
            "role": member_user.role.value,
        },
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def admin_client(
    client: AsyncClient,
    admin_user: User,
) -> AsyncClient:
    """Create an authenticated client for admin user."""
    from paper_scraper.core.security import create_access_token

    token = create_access_token(str(admin_user.id))
    client.headers["Authorization"] = f"Bearer {token}"
    return client


# =============================================================================
# API Key Service Tests
# =============================================================================


class TestAPIKeyService:
    """Tests for API key service functions."""

    async def test_generate_api_key(self):
        """Test API key generation format."""
        key = service.generate_api_key()
        assert key.startswith("ps_")
        assert len(key) > 40

    async def test_hash_api_key(self):
        """Test API key hashing."""
        key = "ps_testkeyvalue123"
        hash1 = service.hash_api_key(key)
        hash2 = service.hash_api_key(key)

        assert hash1 == hash2  # Deterministic
        assert len(hash1) == 64  # SHA-256 hex

    async def test_get_key_prefix(self):
        """Test key prefix extraction."""
        key = "ps_testkeyvalue123"
        prefix = service.get_key_prefix(key)
        assert prefix == "ps_testkeyva"  # First 12 characters
        assert len(prefix) == 12

    async def test_create_api_key(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating an API key."""
        data = APIKeyCreate(
            name="My API Key",
            permissions=["papers:read"],
        )
        api_key, plain_key = await service.create_api_key(
            db_session, test_organization.id, test_user.id, data
        )

        assert api_key.name == "My API Key"
        assert api_key.organization_id == test_organization.id
        assert api_key.is_active is True
        assert plain_key.startswith("ps_")
        assert api_key.key_prefix in plain_key

    async def test_list_api_keys(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_api_key: tuple[APIKey, str],
    ):
        """Test listing API keys."""
        keys = await service.list_api_keys(db_session, test_organization.id)
        assert len(keys) >= 1
        assert any(k.name == "Test Key" for k in keys)

    async def test_get_api_key_by_hash(
        self,
        db_session: AsyncSession,
        test_api_key: tuple[APIKey, str],
    ):
        """Test looking up API key by hash."""
        api_key, plain_key = test_api_key
        key_hash = service.hash_api_key(plain_key)

        found = await service.get_api_key_by_hash(db_session, key_hash)
        assert found is not None
        assert found.id == api_key.id

    async def test_get_api_key_by_hash_invalid(
        self,
        db_session: AsyncSession,
    ):
        """Test that invalid hash returns None."""
        found = await service.get_api_key_by_hash(db_session, "invalid_hash")
        assert found is None

    async def test_revoke_api_key(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_api_key: tuple[APIKey, str],
    ):
        """Test revoking an API key."""
        api_key, _ = test_api_key
        await service.revoke_api_key(db_session, test_organization.id, api_key.id)

        # Verify deleted
        keys = await service.list_api_keys(db_session, test_organization.id)
        assert not any(k.id == api_key.id for k in keys)


# =============================================================================
# Webhook Service Tests
# =============================================================================


class TestWebhookService:
    """Tests for webhook service functions."""

    async def test_generate_webhook_secret(self):
        """Test webhook secret generation."""
        secret = service.generate_webhook_secret()
        assert len(secret) == 64  # 32 bytes hex

    async def test_sign_webhook_payload(self):
        """Test webhook payload signing."""
        payload = b'{"event": "test"}'
        secret = "testsecret123"

        signature = service.sign_webhook_payload(payload, secret)
        assert len(signature) == 64  # HMAC-SHA256 hex

    async def test_create_webhook(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating a webhook."""
        data = WebhookCreate(
            name="My Webhook",
            url="https://example.com/hook",
            events=[WebhookEvent.PAPER_CREATED],
        )
        webhook = await service.create_webhook(
            db_session, test_organization.id, test_user.id, data
        )

        assert webhook.name == "My Webhook"
        assert webhook.url == "https://example.com/hook"
        assert webhook.is_active is True
        assert len(webhook.secret) == 64

    async def test_list_webhooks(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_webhook: Webhook,
    ):
        """Test listing webhooks."""
        webhooks = await service.list_webhooks(db_session, test_organization.id)
        assert len(webhooks) >= 1
        assert any(w.name == "Test Webhook" for w in webhooks)

    async def test_update_webhook(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_webhook: Webhook,
    ):
        """Test updating a webhook."""
        data = WebhookUpdate(
            name="Updated Webhook",
            is_active=False,
        )
        updated = await service.update_webhook(
            db_session, test_organization.id, test_webhook.id, data
        )

        assert updated.name == "Updated Webhook"
        assert updated.is_active is False

    async def test_delete_webhook(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_webhook: Webhook,
    ):
        """Test deleting a webhook."""
        await service.delete_webhook(db_session, test_organization.id, test_webhook.id)

        webhooks = await service.list_webhooks(db_session, test_organization.id)
        assert not any(w.id == test_webhook.id for w in webhooks)

    async def test_get_webhooks_for_event(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_webhook: Webhook,
    ):
        """Test getting webhooks for a specific event."""
        webhooks = await service.get_webhooks_for_event(
            db_session, test_organization.id, "paper.created"
        )
        assert len(webhooks) >= 1

        # Event not subscribed
        webhooks = await service.get_webhooks_for_event(
            db_session, test_organization.id, "submission.created"
        )
        # test_webhook doesn't have submission.created
        # (it has paper.created and paper.scored)
        assert len(webhooks) == 0


# =============================================================================
# Repository Source Service Tests
# =============================================================================


class TestRepositorySourceService:
    """Tests for repository source service functions."""

    async def test_create_repository_source(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating a repository source."""
        data = RepositorySourceCreate(
            name="OpenAlex Biotech",
            provider=RepositoryProvider.OPENALEX,
            config=RepositorySourceConfig(
                query="biotechnology",
                max_results=100,
            ),
            schedule="0 6 * * *",
        )
        source = await service.create_repository_source(
            db_session, test_organization.id, test_user.id, data
        )

        assert source.name == "OpenAlex Biotech"
        assert source.provider == "openalex"
        assert source.is_active is True
        assert source.schedule == "0 6 * * *"

    async def test_list_repository_sources(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_repository: RepositorySource,
    ):
        """Test listing repository sources."""
        sources = await service.list_repository_sources(db_session, test_organization.id)
        assert len(sources) >= 1
        assert any(s.name == "Test Source" for s in sources)

    async def test_update_repository_source(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_repository: RepositorySource,
    ):
        """Test updating a repository source."""
        data = RepositorySourceUpdate(
            name="Updated Source",
            is_active=False,
        )
        updated = await service.update_repository_source(
            db_session, test_organization.id, test_repository.id, data
        )

        assert updated.name == "Updated Source"
        assert updated.is_active is False

    async def test_delete_repository_source(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_repository: RepositorySource,
    ):
        """Test deleting a repository source."""
        await service.delete_repository_source(
            db_session, test_organization.id, test_repository.id
        )

        sources = await service.list_repository_sources(db_session, test_organization.id)
        assert not any(s.id == test_repository.id for s in sources)

    async def test_validate_cron_expression(self):
        """Test cron expression validation."""
        # Valid expressions
        assert service._validate_cron_expression("0 6 * * *") is True
        assert service._validate_cron_expression("*/15 * * * *") is True
        assert service._validate_cron_expression("0 0,12 * * *") is True

        # Invalid expressions
        assert service._validate_cron_expression("invalid") is False
        assert service._validate_cron_expression("0 6 * *") is False  # Only 4 parts


# =============================================================================
# API Router Tests
# =============================================================================


class TestDeveloperRouter:
    """Tests for developer API endpoints."""

    # API Keys

    async def test_list_api_keys(
        self,
        admin_client: AsyncClient,
    ):
        """Test listing API keys via API."""
        response = await admin_client.get("/api/v1/developer/api-keys/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_create_api_key(
        self,
        admin_client: AsyncClient,
    ):
        """Test creating an API key via API."""
        response = await admin_client.post(
            "/api/v1/developer/api-keys/",
            json={
                "name": "Test API Key",
                "permissions": ["papers:read"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test API Key"
        assert "key" in data  # Full key returned on creation
        assert data["key"].startswith("ps_")

    async def test_revoke_api_key(
        self,
        admin_client: AsyncClient,
        test_api_key: tuple[APIKey, str],
    ):
        """Test revoking an API key via API."""
        api_key, _ = test_api_key
        response = await admin_client.delete(f"/api/v1/developer/api-keys/{api_key.id}/")
        assert response.status_code == 204

    # Webhooks

    async def test_list_webhooks(
        self,
        admin_client: AsyncClient,
    ):
        """Test listing webhooks via API."""
        response = await admin_client.get("/api/v1/developer/webhooks/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_create_webhook(
        self,
        admin_client: AsyncClient,
    ):
        """Test creating a webhook via API."""
        response = await admin_client.post(
            "/api/v1/developer/webhooks/",
            json={
                "name": "Test Webhook",
                "url": "https://example.com/hook",
                "events": ["paper.created"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Webhook"
        assert data["is_active"] is True

    async def test_update_webhook(
        self,
        admin_client: AsyncClient,
        test_webhook: Webhook,
    ):
        """Test updating a webhook via API."""
        response = await admin_client.patch(
            f"/api/v1/developer/webhooks/{test_webhook.id}/",
            json={
                "name": "Updated Webhook",
                "is_active": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Webhook"
        assert data["is_active"] is False

    async def test_delete_webhook(
        self,
        admin_client: AsyncClient,
        test_webhook: Webhook,
    ):
        """Test deleting a webhook via API."""
        response = await admin_client.delete(f"/api/v1/developer/webhooks/{test_webhook.id}/")
        assert response.status_code == 204

    # Repository Sources

    async def test_list_repositories(
        self,
        admin_client: AsyncClient,
    ):
        """Test listing repository sources via API."""
        response = await admin_client.get("/api/v1/developer/repositories/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_create_repository(
        self,
        admin_client: AsyncClient,
    ):
        """Test creating a repository source via API."""
        response = await admin_client.post(
            "/api/v1/developer/repositories/",
            json={
                "name": "Test Source",
                "provider": "openalex",
                "config": {
                    "query": "test query",
                    "max_results": 50,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Source"
        assert data["provider"] == "openalex"

    async def test_update_repository(
        self,
        admin_client: AsyncClient,
        test_repository: RepositorySource,
    ):
        """Test updating a repository source via API."""
        response = await admin_client.patch(
            f"/api/v1/developer/repositories/{test_repository.id}/",
            json={
                "name": "Updated Source",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Source"

    async def test_delete_repository(
        self,
        admin_client: AsyncClient,
        test_repository: RepositorySource,
    ):
        """Test deleting a repository source via API."""
        response = await admin_client.delete(f"/api/v1/developer/repositories/{test_repository.id}/")
        assert response.status_code == 204

    # Authorization

    async def test_unauthorized_api_keys(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/developer/api-keys/")
        assert response.status_code == 401

    async def test_non_admin_forbidden(
        self,
        member_client: AsyncClient,
    ):
        """Test that non-admin users are forbidden from developer endpoints."""
        response = await member_client.get("/api/v1/developer/api-keys/")
        # Regular users (member role) don't have DEVELOPER_MANAGE permission
        assert response.status_code == 403
