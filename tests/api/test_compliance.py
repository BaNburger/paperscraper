"""Tests for compliance API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.audit.models import AuditLog
from paper_scraper.modules.auth.models import Organization, User, UserRole
from paper_scraper.modules.compliance.models import RetentionPolicy


@pytest.fixture
async def sample_retention_policy(
    db_session: AsyncSession,
    test_organization: Organization,
) -> RetentionPolicy:
    """Create a sample retention policy."""
    policy = RetentionPolicy(
        organization_id=test_organization.id,
        entity_type="papers",
        retention_days=365,
        action="archive",
        is_active=True,
        description="Archive papers after 1 year",
    )
    db_session.add(policy)
    await db_session.flush()
    await db_session.refresh(policy)
    return policy


@pytest.fixture
async def sample_audit_logs(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
) -> list[AuditLog]:
    """Create sample audit logs for testing."""
    logs = []
    actions = ["login", "paper_create", "paper_score", "logout", "password_change"]

    for _i, action in enumerate(actions):
        log = AuditLog(
            user_id=test_user.id,
            organization_id=test_organization.id,
            action=action,
            resource_type="paper" if "paper" in action else None,
            resource_id=uuid4() if "paper" in action else None,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            details={"test": True},
        )
        db_session.add(log)
        logs.append(log)

    await db_session.flush()
    return logs


class TestRetentionPolicyEndpoints:
    """Test retention policy CRUD endpoints."""

    async def test_list_retention_policies_empty(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing retention policies when none exist."""
        response = await authenticated_client.get("/api/v1/compliance/retention")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_retention_policies(
        self,
        authenticated_client: AsyncClient,
        sample_retention_policy: RetentionPolicy,
    ):
        """Test listing retention policies."""
        response = await authenticated_client.get("/api/v1/compliance/retention")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["entity_type"] == "papers"
        assert data["items"][0]["retention_days"] == 365

    async def test_create_retention_policy(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a retention policy."""
        response = await authenticated_client.post(
            "/api/v1/compliance/retention",
            json={
                "entity_type": "audit_logs",
                "retention_days": 90,
                "action": "delete",
                "description": "Delete old audit logs",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "audit_logs"
        assert data["retention_days"] == 90
        assert data["action"] == "delete"
        assert data["is_active"] is True

    async def test_create_duplicate_policy_fails(
        self,
        authenticated_client: AsyncClient,
        sample_retention_policy: RetentionPolicy,
    ):
        """Test that duplicate entity type policies are rejected."""
        response = await authenticated_client.post(
            "/api/v1/compliance/retention",
            json={
                "entity_type": "papers",
                "retention_days": 180,
                "action": "delete",
            },
        )
        # ValidationError returns 400, duplicate entity policy returns 400
        assert response.status_code in (400, 422)

    async def test_update_retention_policy(
        self,
        authenticated_client: AsyncClient,
        sample_retention_policy: RetentionPolicy,
    ):
        """Test updating a retention policy."""
        response = await authenticated_client.patch(
            f"/api/v1/compliance/retention/{sample_retention_policy.id}",
            json={
                "retention_days": 180,
                "action": "delete",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["retention_days"] == 180
        assert data["action"] == "delete"

    async def test_delete_retention_policy(
        self,
        authenticated_client: AsyncClient,
        sample_retention_policy: RetentionPolicy,
    ):
        """Test deleting a retention policy."""
        response = await authenticated_client.delete(
            f"/api/v1/compliance/retention/{sample_retention_policy.id}"
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await authenticated_client.get("/api/v1/compliance/retention")
        assert response.json()["total"] == 0

    async def test_apply_retention_dry_run(
        self,
        authenticated_client: AsyncClient,
        sample_retention_policy: RetentionPolicy,
    ):
        """Test dry run of retention policy application."""
        response = await authenticated_client.post(
            "/api/v1/compliance/retention/apply",
            json={"dry_run": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_dry_run"] is True
        assert "results" in data


class TestAuditLogEndpoints:
    """Test audit log search and export endpoints."""

    async def test_search_audit_logs(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test searching audit logs."""
        response = await authenticated_client.get(
            "/api/v1/compliance/audit-logs",
            params={"page": 1, "page_size": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(sample_audit_logs)
        assert len(data["items"]) == len(sample_audit_logs)

    async def test_search_audit_logs_with_filter(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test searching audit logs with action filter."""
        response = await authenticated_client.get(
            "/api/v1/compliance/audit-logs",
            params={"action": "login"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(log["action"] == "login" for log in data["items"])

    async def test_get_audit_log_summary(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test getting audit log summary."""
        response = await authenticated_client.get(
            "/api/v1/compliance/audit-logs/summary"
        )
        assert response.status_code == 200
        data = response.json()
        # At least the sample logs should be present (may have more from other operations)
        assert data["total_logs"] >= len(sample_audit_logs)
        assert "logs_by_action" in data
        assert "logs_by_user" in data
        assert "time_range" in data

    async def test_export_audit_logs_csv(
        self,
        authenticated_client: AsyncClient,
        sample_audit_logs: list[AuditLog],
    ):
        """Test exporting audit logs as CSV."""
        response = await authenticated_client.get(
            "/api/v1/compliance/audit-logs/export"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Check CSV content
        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) == len(sample_audit_logs) + 1  # Header + data rows


class TestSOC2Endpoints:
    """Test SOC2 control status endpoints."""

    async def test_get_soc2_status(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting SOC2 control status."""
        response = await authenticated_client.get("/api/v1/compliance/soc2/status")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "summary" in data
        assert data["summary"]["total_controls"] > 0
        assert "compliance_percentage" in data["summary"]

    async def test_get_soc2_evidence(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting evidence for a SOC2 control."""
        response = await authenticated_client.get(
            "/api/v1/compliance/soc2/evidence/CC6.1"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["control_id"] == "CC6.1"
        assert "evidence_items" in data

    async def test_get_soc2_evidence_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting evidence for non-existent control."""
        # Valid format but non-existent control returns 404
        response = await authenticated_client.get(
            "/api/v1/compliance/soc2/evidence/CC99.99"
        )
        assert response.status_code == 404

    async def test_get_soc2_evidence_invalid_format(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting evidence with invalid control ID format returns 422."""
        response = await authenticated_client.get(
            "/api/v1/compliance/soc2/evidence/INVALID.99"
        )
        assert response.status_code == 422

    async def test_export_soc2_report(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test exporting SOC2 report."""
        response = await authenticated_client.post(
            "/api/v1/compliance/soc2/export",
            params={"include_evidence": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "generated_at" in data
        assert "organization_id" in data


class TestDataProcessingEndpoints:
    """Test data processing transparency endpoints."""

    async def test_get_data_processing_info(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting data processing info."""
        response = await authenticated_client.get(
            "/api/v1/compliance/data-processing"
        )
        assert response.status_code == 200
        data = response.json()
        assert "hosting_info" in data
        assert "data_locations" in data
        assert "processors" in data
        assert "data_categories" in data
        assert "legal_basis" in data


class TestComplianceAuthorization:
    """Test that non-admin users cannot access compliance endpoints."""

    async def test_member_cannot_access_retention_policies(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
    ):
        """Test that members cannot access retention policies."""
        from paper_scraper.core.security import create_access_token, get_password_hash

        # Create a member user
        member = User(
            email="member@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Member User",
            organization_id=test_organization.id,
            role=UserRole.MEMBER,
        )
        db_session.add(member)
        await db_session.flush()

        # Create token for member
        token = create_access_token(
            subject=str(member.id),
            extra_claims={
                "org_id": str(member.organization_id),
                "role": member.role.value,
            },
        )
        client.headers["Authorization"] = f"Bearer {token}"

        # Try to access retention policies
        response = await client.get("/api/v1/compliance/retention")
        assert response.status_code == 403

    async def test_viewer_cannot_access_audit_logs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
    ):
        """Test that viewers cannot access audit logs."""
        from paper_scraper.core.security import create_access_token, get_password_hash

        # Create a viewer user
        viewer = User(
            email="viewer@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Viewer User",
            organization_id=test_organization.id,
            role=UserRole.VIEWER,
        )
        db_session.add(viewer)
        await db_session.flush()

        # Create token for viewer
        token = create_access_token(
            subject=str(viewer.id),
            extra_claims={
                "org_id": str(viewer.organization_id),
                "role": viewer.role.value,
            },
        )
        client.headers["Authorization"] = f"Bearer {token}"

        # Try to access audit logs
        response = await client.get("/api/v1/compliance/audit-logs")
        assert response.status_code == 403
