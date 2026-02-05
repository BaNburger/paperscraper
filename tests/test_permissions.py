"""Tests for RBAC permissions system."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import ForbiddenError
from paper_scraper.core.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    check_permission,
    get_permissions_for_role,
)
from paper_scraper.core.security import create_access_token
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.core.security import get_password_hash


# =============================================================================
# Unit tests for core/permissions.py
# =============================================================================


class TestGetPermissionsForRole:
    """Tests for get_permissions_for_role."""

    def test_admin_has_all_permissions(self):
        perms = get_permissions_for_role("admin")
        assert set(perms) == set(Permission)

    def test_manager_permissions(self):
        perms = get_permissions_for_role("manager")
        assert Permission.PAPERS_READ in perms
        assert Permission.PAPERS_WRITE in perms
        assert Permission.GROUPS_MANAGE in perms
        assert Permission.COMPLIANCE_VIEW in perms
        # manager should NOT have:
        assert Permission.PAPERS_DELETE not in perms
        assert Permission.SETTINGS_ADMIN not in perms
        assert Permission.DEVELOPER_MANAGE not in perms

    def test_member_permissions(self):
        perms = get_permissions_for_role("member")
        assert Permission.PAPERS_READ in perms
        assert Permission.PAPERS_WRITE in perms
        assert Permission.SCORING_TRIGGER in perms
        # member should NOT have:
        assert Permission.GROUPS_MANAGE not in perms
        assert Permission.TRANSFER_MANAGE not in perms
        assert Permission.SUBMISSIONS_REVIEW not in perms

    def test_viewer_permissions(self):
        perms = get_permissions_for_role("viewer")
        assert Permission.PAPERS_READ in perms
        assert Permission.GROUPS_READ in perms
        assert len(perms) == 2

    def test_unknown_role_returns_empty(self):
        perms = get_permissions_for_role("nonexistent")
        assert perms == []


class TestCheckPermission:
    """Tests for check_permission."""

    def test_admin_passes_any_permission(self):
        check_permission("admin", Permission.PAPERS_DELETE)

    def test_viewer_passes_read_permission(self):
        check_permission("viewer", Permission.PAPERS_READ)

    def test_viewer_fails_write_permission(self):
        with pytest.raises(ForbiddenError, match="don't have permission"):
            check_permission("viewer", Permission.PAPERS_WRITE)

    def test_member_fails_delete_permission(self):
        with pytest.raises(ForbiddenError):
            check_permission("member", Permission.PAPERS_DELETE)

    def test_multiple_permissions_all_needed(self):
        # member has both PAPERS_READ and SCORING_TRIGGER
        check_permission("member", Permission.PAPERS_READ, Permission.SCORING_TRIGGER)

    def test_multiple_permissions_missing_one(self):
        # member has PAPERS_READ but NOT PAPERS_DELETE
        with pytest.raises(ForbiddenError):
            check_permission("member", Permission.PAPERS_READ, Permission.PAPERS_DELETE)

    def test_unknown_role_fails(self):
        with pytest.raises(ForbiddenError):
            check_permission("unknown_role", Permission.PAPERS_READ)


# =============================================================================
# Integration tests for permission endpoints
# =============================================================================


@pytest_asyncio.fixture
async def viewer_user(
    db_session: AsyncSession,
    test_organization: Organization,
) -> User:
    """Create a viewer user."""
    user = User(
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpassword123"),
        full_name="Viewer User",
        organization_id=test_organization.id,
        role=UserRole.VIEWER,
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
    """Create a member user."""
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


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        extra_claims={"org_id": str(user.organization_id), "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestPermissionEndpoints:
    """Tests for GET /auth/permissions and GET /auth/roles."""

    async def test_get_my_permissions(self, authenticated_client: AsyncClient):
        """Admin should get all permissions."""
        resp = await authenticated_client.get("/api/v1/auth/permissions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "admin"
        assert len(data["permissions"]) == len(Permission)

    async def test_get_roles(self, authenticated_client: AsyncClient):
        """Should return all role-permission mappings."""
        resp = await authenticated_client.get("/api/v1/auth/roles")
        assert resp.status_code == 200
        data = resp.json()
        assert "roles" in data
        assert "admin" in data["roles"]
        assert "viewer" in data["roles"]
        assert len(data["roles"]["admin"]) == len(Permission)

    async def test_viewer_permissions(self, client: AsyncClient, viewer_user: User):
        """Viewer should have limited permissions."""
        resp = await client.get(
            "/api/v1/auth/permissions", headers=_auth_headers(viewer_user)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "viewer"
        assert "papers:read" in data["permissions"]
        assert "papers:write" not in data["permissions"]

    async def test_viewer_cannot_access_roles(self, client: AsyncClient, viewer_user: User):
        """Viewer should not access the full role-permission matrix."""
        resp = await client.get(
            "/api/v1/auth/roles", headers=_auth_headers(viewer_user)
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestRBACEnforcement:
    """Test that RBAC is enforced on protected endpoints."""

    async def test_viewer_cannot_delete_paper(self, client: AsyncClient, viewer_user: User):
        """Viewer lacks papers:delete and should get 403."""
        from uuid import uuid4

        resp = await client.delete(
            f"/api/v1/papers/{uuid4()}", headers=_auth_headers(viewer_user)
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_create_group(self, client: AsyncClient, viewer_user: User):
        """Viewer lacks groups:manage and should get 403."""
        resp = await client.post(
            "/api/v1/groups/",
            json={"name": "Test Group", "type": "research_team"},
            headers=_auth_headers(viewer_user),
        )
        assert resp.status_code == 403

    async def test_member_cannot_manage_groups(self, client: AsyncClient, member_user: User):
        """Member lacks groups:manage and should get 403."""
        resp = await client.post(
            "/api/v1/groups/",
            json={"name": "Test Group", "type": "research_team"},
            headers=_auth_headers(member_user),
        )
        assert resp.status_code == 403

    async def test_member_cannot_review_submission(self, client: AsyncClient, member_user: User):
        """Member lacks submissions:review and should get 403."""
        from uuid import uuid4

        resp = await client.patch(
            f"/api/v1/submissions/{uuid4()}/review",
            json={"decision": "approve"},
            headers=_auth_headers(member_user),
        )
        assert resp.status_code == 403
