"""Tests for knowledge sources module."""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import ForbiddenError, NotFoundError
from paper_scraper.core.security import create_access_token, get_password_hash
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.knowledge.models import (
    KnowledgeScope,
    KnowledgeSource,
    KnowledgeType,
)
from paper_scraper.modules.knowledge.schemas import (
    KnowledgeSourceCreate,
    KnowledgeSourceUpdate,
)
from paper_scraper.modules.knowledge.service import KnowledgeService

# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def knowledge_service(db_session: AsyncSession) -> KnowledgeService:
    """Create a knowledge service instance for testing."""
    return KnowledgeService(db_session)


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    organization = Organization(
        name="Second Organization",
        type="university",
    )
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def member_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a non-admin user."""
    user = User(
        email="member@example.com",
        hashed_password=get_password_hash("testpassword123"),
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
    client: AsyncClient,
    member_user: User,
) -> AsyncClient:
    """Create an authenticated client for a non-admin user."""
    token = create_access_token(
        subject=str(member_user.id),
        extra_claims={
            "org_id": str(member_user.organization_id),
            "role": member_user.role.value,
        },
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def personal_source(
    db_session: AsyncSession,
    test_user: User,
    test_organization: Organization,
) -> KnowledgeSource:
    """Create a personal knowledge source."""
    source = KnowledgeSource(
        organization_id=test_organization.id,
        user_id=test_user.id,
        scope=KnowledgeScope.PERSONAL,
        type=KnowledgeType.RESEARCH_FOCUS,
        title="My Research Focus",
        content="I focus on machine learning and NLP.",
        tags=["ml", "nlp"],
    )
    db_session.add(source)
    await db_session.flush()
    await db_session.refresh(source)
    return source


@pytest_asyncio.fixture
async def org_source(
    db_session: AsyncSession,
    test_organization: Organization,
) -> KnowledgeSource:
    """Create an organization knowledge source."""
    source = KnowledgeSource(
        organization_id=test_organization.id,
        user_id=None,
        scope=KnowledgeScope.ORGANIZATION,
        type=KnowledgeType.INDUSTRY_CONTEXT,
        title="Our Industry Focus",
        content="We focus on biotech and pharma innovations.",
        tags=["biotech", "pharma"],
    )
    db_session.add(source)
    await db_session.flush()
    await db_session.refresh(source)
    return source


# =============================================================================
# Service Tests
# =============================================================================


class TestKnowledgeService:
    """Tests for KnowledgeService class."""

    # --- Personal sources ---

    async def test_create_personal(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test creating a personal knowledge source."""
        data = KnowledgeSourceCreate(
            title="My Expertise",
            content="Expert in quantum computing.",
            type=KnowledgeType.DOMAIN_EXPERTISE,
            tags=["quantum"],
        )

        source = await knowledge_service.create_personal(test_user.id, test_organization.id, data)

        assert source.id is not None
        assert source.title == "My Expertise"
        assert source.scope == KnowledgeScope.PERSONAL
        assert source.user_id == test_user.id
        assert source.organization_id == test_organization.id
        assert source.type == KnowledgeType.DOMAIN_EXPERTISE
        assert source.tags == ["quantum"]

    async def test_list_personal(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test listing personal knowledge sources."""
        response = await knowledge_service.list_personal(test_user.id, test_organization.id)

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].title == "My Research Focus"
        assert response.items[0].scope == KnowledgeScope.PERSONAL

    async def test_list_personal_empty(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test listing personal sources when none exist."""
        response = await knowledge_service.list_personal(test_user.id, test_organization.id)

        assert response.total == 0
        assert len(response.items) == 0

    async def test_list_personal_excludes_org_sources(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
        org_source: KnowledgeSource,
    ):
        """Test that listing personal sources excludes org sources."""
        response = await knowledge_service.list_personal(test_user.id, test_organization.id)
        assert response.total == 0

    async def test_update_personal(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test updating a personal knowledge source."""
        data = KnowledgeSourceUpdate(
            title="Updated Focus",
            tags=["updated"],
        )

        source = await knowledge_service.update_personal(
            personal_source.id, test_user.id, test_organization.id, data
        )

        assert source.title == "Updated Focus"
        assert source.tags == ["updated"]
        assert source.content == "I focus on machine learning and NLP."

    async def test_update_personal_not_found(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test updating a non-existent personal source."""
        with pytest.raises(NotFoundError):
            await knowledge_service.update_personal(
                uuid4(),
                test_user.id,
                test_organization.id,
                KnowledgeSourceUpdate(title="X"),
            )

    async def test_update_personal_wrong_user(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test that updating someone else's source is forbidden."""
        other_user_id = uuid4()
        with pytest.raises(ForbiddenError):
            await knowledge_service.update_personal(
                personal_source.id,
                other_user_id,
                test_organization.id,
                KnowledgeSourceUpdate(title="Hacked"),
            )

    async def test_update_personal_wrong_scope(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
        org_source: KnowledgeSource,
    ):
        """Test that updating an org source via personal endpoint is forbidden."""
        with pytest.raises(ForbiddenError):
            await knowledge_service.update_personal(
                org_source.id,
                test_user.id,
                test_organization.id,
                KnowledgeSourceUpdate(title="X"),
            )

    async def test_delete_personal(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
        personal_source: KnowledgeSource,
        db_session: AsyncSession,
    ):
        """Test deleting a personal knowledge source."""
        await knowledge_service.delete_personal(
            personal_source.id, test_user.id, test_organization.id
        )

        result = await db_session.execute(
            select(KnowledgeSource).where(KnowledgeSource.id == personal_source.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_delete_personal_not_found(
        self,
        knowledge_service: KnowledgeService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test deleting a non-existent source."""
        with pytest.raises(NotFoundError):
            await knowledge_service.delete_personal(uuid4(), test_user.id, test_organization.id)

    async def test_delete_personal_wrong_user(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test that deleting someone else's source is forbidden."""
        with pytest.raises(ForbiddenError):
            await knowledge_service.delete_personal(
                personal_source.id, uuid4(), test_organization.id
            )

    # --- Organization sources ---

    async def test_create_organization(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
    ):
        """Test creating an organization knowledge source."""
        data = KnowledgeSourceCreate(
            title="Org Criteria",
            content="We evaluate patents based on broad claims.",
            type=KnowledgeType.EVALUATION_CRITERIA,
        )

        source = await knowledge_service.create_organization(test_organization.id, data)

        assert source.scope == KnowledgeScope.ORGANIZATION
        assert source.user_id is None
        assert source.title == "Org Criteria"

    async def test_list_organization(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        org_source: KnowledgeSource,
    ):
        """Test listing org knowledge sources."""
        response = await knowledge_service.list_organization(test_organization.id)

        assert response.total == 1
        assert response.items[0].title == "Our Industry Focus"

    async def test_list_organization_excludes_personal(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test that listing org sources excludes personal ones."""
        response = await knowledge_service.list_organization(test_organization.id)
        assert response.total == 0

    async def test_list_organization_tenant_isolation(
        self,
        knowledge_service: KnowledgeService,
        second_organization: Organization,
        org_source: KnowledgeSource,
    ):
        """Test org source listing respects tenant boundaries."""
        response = await knowledge_service.list_organization(second_organization.id)
        assert response.total == 0

    async def test_update_organization(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        org_source: KnowledgeSource,
    ):
        """Test updating an org knowledge source."""
        data = KnowledgeSourceUpdate(title="Updated Org Focus")

        source = await knowledge_service.update_organization(
            org_source.id, test_organization.id, data
        )

        assert source.title == "Updated Org Focus"
        assert source.content == "We focus on biotech and pharma innovations."

    async def test_update_organization_wrong_scope(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test that updating a personal source via org endpoint is forbidden."""
        with pytest.raises(ForbiddenError):
            await knowledge_service.update_organization(
                personal_source.id,
                test_organization.id,
                KnowledgeSourceUpdate(title="X"),
            )

    async def test_update_organization_tenant_isolation(
        self,
        knowledge_service: KnowledgeService,
        second_organization: Organization,
        org_source: KnowledgeSource,
    ):
        """Test that updating from wrong org raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await knowledge_service.update_organization(
                org_source.id,
                second_organization.id,
                KnowledgeSourceUpdate(title="Hacked"),
            )

    async def test_delete_organization(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        org_source: KnowledgeSource,
        db_session: AsyncSession,
    ):
        """Test deleting an org knowledge source."""
        await knowledge_service.delete_organization(org_source.id, test_organization.id)

        result = await db_session.execute(
            select(KnowledgeSource).where(KnowledgeSource.id == org_source.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_delete_organization_wrong_scope(
        self,
        knowledge_service: KnowledgeService,
        test_organization: Organization,
        personal_source: KnowledgeSource,
    ):
        """Test that deleting a personal source via org endpoint is forbidden."""
        with pytest.raises(ForbiddenError):
            await knowledge_service.delete_organization(personal_source.id, test_organization.id)


# =============================================================================
# API Router Tests
# =============================================================================


class TestKnowledgeRouter:
    """Tests for knowledge API endpoints."""

    # --- Personal endpoints ---

    async def test_list_personal(
        self,
        authenticated_client: AsyncClient,
        personal_source: KnowledgeSource,
    ):
        """Test listing personal sources via API."""
        response = await authenticated_client.get("/api/v1/knowledge/personal")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "My Research Focus"

    async def test_create_personal(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a personal source via API."""
        response = await authenticated_client.post(
            "/api/v1/knowledge/personal",
            json={
                "title": "New Source",
                "content": "Some content",
                "type": "domain_expertise",
                "tags": ["test"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Source"
        assert data["scope"] == "personal"
        assert data["type"] == "domain_expertise"
        assert data["tags"] == ["test"]

    async def test_create_personal_empty_title(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that creating with empty title returns 422."""
        response = await authenticated_client.post(
            "/api/v1/knowledge/personal",
            json={"title": "", "content": "Some content"},
        )
        assert response.status_code == 422

    async def test_create_personal_empty_content(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that creating with empty content returns 422."""
        response = await authenticated_client.post(
            "/api/v1/knowledge/personal",
            json={"title": "Title", "content": ""},
        )
        assert response.status_code == 422

    async def test_update_personal(
        self,
        authenticated_client: AsyncClient,
        personal_source: KnowledgeSource,
    ):
        """Test updating a personal source via API."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge/personal/{personal_source.id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"

    async def test_update_personal_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test updating a non-existent personal source returns 404."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge/personal/{uuid4()}",
            json={"title": "X"},
        )
        assert response.status_code == 404

    async def test_delete_personal(
        self,
        authenticated_client: AsyncClient,
        personal_source: KnowledgeSource,
    ):
        """Test deleting a personal source via API."""
        response = await authenticated_client.delete(
            f"/api/v1/knowledge/personal/{personal_source.id}"
        )
        assert response.status_code == 204

    async def test_delete_personal_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test deleting non-existent source returns 404."""
        response = await authenticated_client.delete(f"/api/v1/knowledge/personal/{uuid4()}")
        assert response.status_code == 404

    # --- Organization endpoints ---

    async def test_list_organization(
        self,
        authenticated_client: AsyncClient,
        org_source: KnowledgeSource,
    ):
        """Test listing org sources via API (admin)."""
        response = await authenticated_client.get("/api/v1/knowledge/organization")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Our Industry Focus"

    async def test_create_organization(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating an org source via API (admin)."""
        response = await authenticated_client.post(
            "/api/v1/knowledge/organization",
            json={
                "title": "Org Evaluation",
                "content": "Broad patent claims preferred.",
                "type": "evaluation_criteria",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Org Evaluation"
        assert data["scope"] == "organization"
        assert data["user_id"] is None

    async def test_update_organization(
        self,
        authenticated_client: AsyncClient,
        org_source: KnowledgeSource,
    ):
        """Test updating an org source via API (admin)."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge/organization/{org_source.id}",
            json={"title": "Updated Org"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Org"

    async def test_delete_organization(
        self,
        authenticated_client: AsyncClient,
        org_source: KnowledgeSource,
    ):
        """Test deleting an org source via API (admin)."""
        response = await authenticated_client.delete(
            f"/api/v1/knowledge/organization/{org_source.id}"
        )
        assert response.status_code == 204

    # --- Access control ---

    async def test_org_endpoints_require_admin(
        self,
        member_client: AsyncClient,
    ):
        """Test that org endpoints require admin role."""
        response = await member_client.get("/api/v1/knowledge/organization")
        assert response.status_code == 403

    async def test_org_create_requires_admin(
        self,
        member_client: AsyncClient,
    ):
        """Test that creating org sources requires admin."""
        response = await member_client.post(
            "/api/v1/knowledge/organization",
            json={"title": "Test", "content": "Test"},
        )
        assert response.status_code == 403

    async def test_org_delete_requires_admin(
        self,
        member_client: AsyncClient,
        org_source: KnowledgeSource,
    ):
        """Test that deleting org sources requires admin."""
        response = await member_client.delete(f"/api/v1/knowledge/organization/{org_source.id}")
        assert response.status_code == 403

    async def test_unauthorized_personal(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated personal access is rejected."""
        response = await client.get("/api/v1/knowledge/personal")
        assert response.status_code == 401

    async def test_unauthorized_organization(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated org access is rejected."""
        response = await client.get("/api/v1/knowledge/organization")
        assert response.status_code == 401
