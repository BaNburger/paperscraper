"""Tests for scheduled reports module."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.auth.models import Organization, User
from paper_scraper.modules.reports.models import (
    ReportFormat,
    ReportSchedule,
    ReportType,
    ScheduledReport,
)


class TestScheduledReportsEndpoints:
    """Test scheduled reports CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_list_reports_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test listing reports when none exist."""
        response = await client.get("/api/v1/reports/scheduled", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating a scheduled report."""
        report_data = {
            "name": "Weekly Dashboard Summary",
            "report_type": "dashboard_summary",
            "schedule": "weekly",
            "format": "pdf",
            "recipients": ["test@example.com"],
        }

        response = await client.post(
            "/api/v1/reports/scheduled",
            json=report_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Weekly Dashboard Summary"
        assert data["report_type"] == "dashboard_summary"
        assert data["schedule"] == "weekly"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_report_with_all_fields(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating a report with all optional fields."""
        report_data = {
            "name": "Monthly Trends Report",
            "report_type": "paper_trends",
            "schedule": "monthly",
            "format": "pdf",
            "recipients": ["admin@example.com", "team@example.com"],
            "is_active": False,
        }

        response = await client.post(
            "/api/v1/reports/scheduled",
            json=report_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is False
        assert len(data["recipients"]) == 2

    @pytest.mark.asyncio
    async def test_get_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test retrieving a single report."""
        # Create report directly in DB
        report = ScheduledReport(
            organization_id=test_user.organization_id,
            created_by_id=test_user.id,
            name="Test Report",
            report_type=ReportType.DASHBOARD_SUMMARY,
            schedule=ReportSchedule.DAILY,
            format=ReportFormat.PDF,
            recipients=["test@example.com"],
        )
        db_session.add(report)
        await db_session.flush()

        response = await client.get(f"/api/v1/reports/scheduled/{report.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(report.id)
        assert data["name"] == "Test Report"

    @pytest.mark.asyncio
    async def test_get_report_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting non-existent report returns 404."""
        import uuid

        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/reports/scheduled/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test updating a scheduled report."""
        # Create report
        report = ScheduledReport(
            organization_id=test_user.organization_id,
            created_by_id=test_user.id,
            name="Original Name",
            report_type=ReportType.DASHBOARD_SUMMARY,
            schedule=ReportSchedule.DAILY,
            format=ReportFormat.PDF,
            recipients=["old@example.com"],
        )
        db_session.add(report)
        await db_session.flush()

        # Update it
        update_data = {
            "name": "Updated Name",
            "recipients": ["new@example.com"],
            "is_active": False,
        }

        response = await client.patch(
            f"/api/v1/reports/scheduled/{report.id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["is_active"] is False
        assert "new@example.com" in data["recipients"]

    @pytest.mark.asyncio
    async def test_delete_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test deleting a scheduled report."""
        # Create report
        report = ScheduledReport(
            organization_id=test_user.organization_id,
            created_by_id=test_user.id,
            name="To Delete",
            report_type=ReportType.TEAM_ACTIVITY,
            schedule=ReportSchedule.WEEKLY,
            format=ReportFormat.PDF,
            recipients=["test@example.com"],
        )
        db_session.add(report)
        await db_session.flush()

        # Delete it
        response = await client.delete(
            f"/api/v1/reports/scheduled/{report.id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(f"/api/v1/reports/scheduled/{report.id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_reports_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test listing reports returns all reports for organization."""
        # Create multiple reports
        for i in range(3):
            report = ScheduledReport(
                organization_id=test_user.organization_id,
                created_by_id=test_user.id,
                name=f"Report {i}",
                report_type=ReportType.DASHBOARD_SUMMARY,
                schedule=ReportSchedule.DAILY,
                format=ReportFormat.PDF,
                recipients=["test@example.com"],
            )
            db_session.add(report)
        await db_session.flush()

        response = await client.get("/api/v1/reports/scheduled", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_run_report(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test manually triggering a report run."""
        # Create report
        report = ScheduledReport(
            organization_id=test_user.organization_id,
            created_by_id=test_user.id,
            name="Manual Run Report",
            report_type=ReportType.DASHBOARD_SUMMARY,
            schedule=ReportSchedule.DAILY,
            format=ReportFormat.PDF,
            recipients=["test@example.com"],
        )
        db_session.add(report)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/reports/scheduled/{report.id}/run", headers=auth_headers
        )
        # Should queue the job successfully
        assert response.status_code in [200, 202]  # Might be async

    @pytest.mark.asyncio
    async def test_report_tenant_isolation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that users can only see reports from their organization."""
        # Create a real organization for the other tenant
        other_org = Organization(name="Other Org", type="university")
        db_session.add(other_org)
        await db_session.flush()
        await db_session.refresh(other_org)

        # Create report for test user's org
        my_report = ScheduledReport(
            organization_id=test_user.organization_id,
            created_by_id=test_user.id,
            name="My Report",
            report_type=ReportType.DASHBOARD_SUMMARY,
            schedule=ReportSchedule.DAILY,
            format=ReportFormat.PDF,
            recipients=["test@example.com"],
        )
        db_session.add(my_report)

        # Create report for different org
        other_report = ScheduledReport(
            organization_id=other_org.id,
            created_by_id=None,
            name="Other Org Report",
            report_type=ReportType.PAPER_TRENDS,
            schedule=ReportSchedule.WEEKLY,
            format=ReportFormat.PDF,
            recipients=["other@example.com"],
        )
        db_session.add(other_report)
        await db_session.flush()

        # List should only show my report
        response = await client.get("/api/v1/reports/scheduled", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "My Report"

        # Trying to get other org's report should fail
        response = await client.get(
            f"/api/v1/reports/scheduled/{other_report.id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_access(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot access reports."""
        response = await client.get("/api/v1/reports/scheduled")
        assert response.status_code == 401

        response = await client.post(
            "/api/v1/reports/scheduled",
            json={"name": "Test", "report_type": "dashboard_summary"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_report_invalid_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating report with invalid report type fails."""
        report_data = {
            "name": "Invalid Report",
            "report_type": "invalid_type",
            "schedule": "daily",
            "format": "pdf",
            "recipients": ["test@example.com"],
        }

        response = await client.post(
            "/api/v1/reports/scheduled",
            json=report_data,
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_report_empty_recipients(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating report with no recipients fails."""
        report_data = {
            "name": "No Recipients",
            "report_type": "dashboard_summary",
            "schedule": "daily",
            "format": "pdf",
            "recipients": [],
        }

        response = await client.post(
            "/api/v1/reports/scheduled",
            json=report_data,
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error
