"""Tests for audit logging module."""

from uuid import uuid4

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.security import create_access_token
from paper_scraper.modules.audit.models import AuditAction, AuditLog
from paper_scraper.modules.audit.schemas import AuditLogFilters
from paper_scraper.modules.audit.service import AuditService
from paper_scraper.modules.auth.models import Organization, User, UserRole

# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def audit_service(db_session: AsyncSession) -> AuditService:
    """Create an audit service instance for testing."""
    return AuditService(db_session)


@pytest_asyncio.fixture
async def second_organization(db_session: AsyncSession) -> Organization:
    """Create a second organization for tenant isolation tests."""
    organization = Organization(
        name="Second Organization",
        type="corporate",
    )
    db_session.add(organization)
    await db_session.flush()
    await db_session.refresh(organization)
    return organization


@pytest_asyncio.fixture
async def regular_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a regular (non-admin) user for testing."""
    from paper_scraper.core.security import get_password_hash

    user = User(
        email="regular@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Regular User",
        organization_id=test_organization.id,
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user_client(
    client: AsyncClient,
    regular_user: User,
) -> AsyncClient:
    """Create an authenticated client for a regular user."""
    token = create_access_token(
        subject=str(regular_user.id),
        extra_claims={
            "org_id": str(regular_user.organization_id),
            "role": regular_user.role.value,
        },
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def sample_audit_logs(
    db_session: AsyncSession,
    test_user: User,
    test_organization: Organization,
) -> list[AuditLog]:
    """Create sample audit logs for testing."""
    logs = []
    actions = [
        (AuditAction.LOGIN, "user", test_user.id),
        (AuditAction.PAPER_CREATE, "paper", uuid4()),
        (AuditAction.PAPER_SCORE, "paper", uuid4()),
        (AuditAction.PROJECT_CREATE, "project", uuid4()),
        (AuditAction.LOGOUT, "user", test_user.id),
    ]

    for i, (action, resource_type, resource_id) in enumerate(actions):
        log = AuditLog(
            action=action.value,
            user_id=test_user.id,
            organization_id=test_organization.id,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"index": i},
            ip_address="127.0.0.1",
            user_agent="TestClient/1.0",
        )
        db_session.add(log)
        logs.append(log)

    await db_session.flush()
    for log in logs:
        await db_session.refresh(log)

    return logs


# =============================================================================
# Service Tests
# =============================================================================


class TestAuditService:
    """Tests for AuditService class."""

    async def test_log_creates_audit_entry(
        self,
        audit_service: AuditService,
        test_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test that log() creates an audit entry in the database."""
        log = await audit_service.log(
            action=AuditAction.LOGIN,
            user_id=test_user.id,
            organization_id=test_organization.id,
            details={"method": "password"},
        )

        assert log.id is not None
        assert log.action == AuditAction.LOGIN.value
        assert log.user_id == test_user.id
        assert log.organization_id == test_organization.id
        assert log.details == {"method": "password"}

        # Verify it's in the database
        result = await db_session.execute(select(AuditLog).where(AuditLog.id == log.id))
        db_log = result.scalar_one()
        assert db_log.action == "login"

    async def test_log_accepts_string_action(
        self,
        audit_service: AuditService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test that log() accepts string action names."""
        log = await audit_service.log(
            action="custom_action",
            user_id=test_user.id,
            organization_id=test_organization.id,
        )

        assert log.action == "custom_action"

    async def test_log_with_resource_info(
        self,
        audit_service: AuditService,
        test_user: User,
        test_organization: Organization,
    ):
        """Test logging with resource type and ID."""
        paper_id = uuid4()
        log = await audit_service.log(
            action=AuditAction.PAPER_CREATE,
            user_id=test_user.id,
            organization_id=test_organization.id,
            resource_type="paper",
            resource_id=paper_id,
        )

        assert log.resource_type == "paper"
        assert log.resource_id == paper_id

    async def test_log_without_user(
        self,
        audit_service: AuditService,
        test_organization: Organization,
    ):
        """Test logging actions without a user (e.g., system events)."""
        log = await audit_service.log(
            action=AuditAction.LOGIN_FAILED,
            organization_id=test_organization.id,
            details={"reason": "invalid_credentials", "email": "unknown@test.com"},
        )

        assert log.user_id is None
        assert log.organization_id == test_organization.id

    async def test_list_logs_returns_paginated_results(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_organization: Organization,
    ):
        """Test that list_logs returns paginated results."""
        response = await audit_service.list_logs(
            organization_id=test_organization.id,
            page=1,
            page_size=3,
        )

        assert len(response.items) == 3
        assert response.total == 5
        assert response.page == 1
        assert response.page_size == 3
        assert response.pages == 2

    async def test_list_logs_second_page(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_organization: Organization,
    ):
        """Test fetching the second page of results."""
        response = await audit_service.list_logs(
            organization_id=test_organization.id,
            page=2,
            page_size=3,
        )

        assert len(response.items) == 2
        assert response.total == 5
        assert response.page == 2

    async def test_list_logs_ordered_by_created_at_desc(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_organization: Organization,
    ):
        """Test that results are ordered by created_at descending."""
        response = await audit_service.list_logs(
            organization_id=test_organization.id,
        )

        # Most recent first
        dates = [item.created_at for item in response.items]
        assert dates == sorted(dates, reverse=True)

    async def test_list_logs_filter_by_action(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_organization: Organization,
    ):
        """Test filtering logs by action type."""
        filters = AuditLogFilters(action=AuditAction.LOGIN)
        response = await audit_service.list_logs(
            organization_id=test_organization.id,
            filters=filters,
        )

        assert len(response.items) == 1
        assert response.items[0].action == "login"

    async def test_list_logs_filter_by_resource_type(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_organization: Organization,
    ):
        """Test filtering logs by resource type."""
        filters = AuditLogFilters(resource_type="paper")
        response = await audit_service.list_logs(
            organization_id=test_organization.id,
            filters=filters,
        )

        assert len(response.items) == 2
        for item in response.items:
            assert item.resource_type == "paper"

    async def test_list_logs_filter_by_user_id(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_user: User,
        test_organization: Organization,
    ):
        """Test filtering logs by user ID."""
        filters = AuditLogFilters(user_id=test_user.id)
        response = await audit_service.list_logs(
            organization_id=test_organization.id,
            filters=filters,
        )

        assert len(response.items) == 5
        for item in response.items:
            assert item.user_id == test_user.id

    async def test_list_logs_tenant_isolation(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        second_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test that list_logs only returns logs for the specified organization."""
        # Create a log for the second organization
        other_log = AuditLog(
            action=AuditAction.LOGIN.value,
            organization_id=second_organization.id,
            details={},
        )
        db_session.add(other_log)
        await db_session.flush()

        # Query for second organization should only return its log
        response = await audit_service.list_logs(
            organization_id=second_organization.id,
        )

        assert len(response.items) == 1
        assert response.items[0].organization_id == second_organization.id

    async def test_get_user_activity(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_user: User,
        test_organization: Organization,
    ):
        """Test getting activity for a specific user."""
        activity = await audit_service.get_user_activity(
            user_id=test_user.id,
            organization_id=test_organization.id,
        )

        assert len(activity) == 5
        for item in activity:
            assert item.user_id == test_user.id

    async def test_get_user_activity_with_limit(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_user: User,
        test_organization: Organization,
    ):
        """Test limiting user activity results."""
        activity = await audit_service.get_user_activity(
            user_id=test_user.id,
            organization_id=test_organization.id,
            limit=2,
        )

        assert len(activity) == 2

    async def test_get_user_activity_tenant_isolation(
        self,
        audit_service: AuditService,
        sample_audit_logs: list[AuditLog],
        test_user: User,
        second_organization: Organization,
    ):
        """Test that get_user_activity respects organization boundaries."""
        # Query with wrong organization should return nothing
        activity = await audit_service.get_user_activity(
            user_id=test_user.id,
            organization_id=second_organization.id,
        )

        assert len(activity) == 0


# =============================================================================
# API Router Tests
# =============================================================================


class TestAuditRouter:
    """Tests for audit API endpoints."""

    async def test_list_audit_logs_as_admin(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test that admins can list audit logs."""
        response = await authenticated_client.get("/api/v1/audit/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 5

    async def test_list_audit_logs_with_pagination(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test pagination parameters for audit logs."""
        response = await authenticated_client.get(
            "/api/v1/audit/", params={"page": 1, "page_size": 2}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["pages"] == 3

    async def test_list_audit_logs_with_action_filter(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test filtering audit logs by action."""
        response = await authenticated_client.get("/api/v1/audit/", params={"action": "login"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["action"] == "login"

    async def test_list_audit_logs_forbidden_for_non_admin(
        self,
        regular_user_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test that non-admin users cannot list audit logs."""
        response = await regular_user_client.get("/api/v1/audit/")

        assert response.status_code == 403

    async def test_list_audit_logs_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/api/v1/audit/")

        assert response.status_code == 401

    async def test_get_user_activity_as_admin(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
        test_user: User,
    ):
        """Test that admins can view user activity."""
        response = await authenticated_client.get(f"/api/v1/audit/users/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    async def test_get_user_activity_with_limit(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
        test_user: User,
    ):
        """Test limiting user activity results via API."""
        response = await authenticated_client.get(
            f"/api/v1/audit/users/{test_user.id}", params={"limit": 2}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_user_activity_forbidden_for_non_admin(
        self,
        regular_user_client: AsyncClient,
        test_user: User,
    ):
        """Test that non-admin users cannot view other user activity."""
        response = await regular_user_client.get(f"/api/v1/audit/users/{test_user.id}")

        assert response.status_code == 403

    async def test_get_my_activity(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test that users can view their own activity."""
        response = await authenticated_client.get("/api/v1/audit/my-activity")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    async def test_get_my_activity_as_regular_user(
        self,
        regular_user_client: AsyncClient,
        db_session: AsyncSession,
        regular_user: User,
        test_organization: Organization,
    ):
        """Test that regular users can view their own activity."""
        # Create some activity for the regular user
        log = AuditLog(
            action=AuditAction.LOGIN.value,
            user_id=regular_user.id,
            organization_id=test_organization.id,
            details={"method": "password"},
        )
        db_session.add(log)
        await db_session.flush()

        response = await regular_user_client.get("/api/v1/audit/my-activity")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "login"

    async def test_get_my_activity_with_limit(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test limiting own activity results."""
        response = await authenticated_client.get("/api/v1/audit/my-activity", params={"limit": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_audit_log_response_structure(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test that audit log response has correct structure."""
        response = await authenticated_client.get("/api/v1/audit/")

        assert response.status_code == 200
        data = response.json()
        log_item = data["items"][0]

        # Verify all expected fields are present
        assert "id" in log_item
        assert "user_id" in log_item
        assert "organization_id" in log_item
        assert "action" in log_item
        assert "resource_type" in log_item
        assert "resource_id" in log_item
        assert "details" in log_item
        assert "ip_address" in log_item
        assert "user_agent" in log_item
        assert "created_at" in log_item
