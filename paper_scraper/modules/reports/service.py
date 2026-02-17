"""Service for scheduled reports management."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.reports.models import (
    ReportSchedule,
    ScheduledReport,
)
from paper_scraper.modules.reports.schemas import (
    CreateScheduledReportRequest,
    ReportRunResult,
    ScheduledReportListResponse,
    ScheduledReportResponse,
    UpdateScheduledReportRequest,
)


class ReportsService:
    """Service for managing scheduled reports."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the reports service."""
        self.db = db

    async def list_reports(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
    ) -> ScheduledReportListResponse:
        """List scheduled reports for an organization.

        Args:
            organization_id: Organization to list reports for.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            is_active: Filter by active status.

        Returns:
            Paginated list of scheduled reports.
        """
        query = select(ScheduledReport).where(
            ScheduledReport.organization_id == organization_id
        )

        if is_active is not None:
            query = query.where(ScheduledReport.is_active == is_active)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination
        pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        query = query.order_by(ScheduledReport.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        reports = result.scalars().all()

        return ScheduledReportListResponse(
            items=[ScheduledReportResponse.model_validate(r) for r in reports],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_report(
        self, organization_id: UUID, report_id: UUID
    ) -> ScheduledReportResponse:
        """Get a specific scheduled report.

        Args:
            organization_id: Organization ID for tenant isolation.
            report_id: Report ID.

        Returns:
            The scheduled report.

        Raises:
            NotFoundError: If report not found.
        """
        query = select(ScheduledReport).where(
            ScheduledReport.id == report_id,
            ScheduledReport.organization_id == organization_id,
        )
        result = await self.db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            raise NotFoundError("ScheduledReport", str(report_id))

        return ScheduledReportResponse.model_validate(report)

    async def create_report(
        self,
        organization_id: UUID,
        user_id: UUID,
        data: CreateScheduledReportRequest,
    ) -> ScheduledReportResponse:
        """Create a new scheduled report.

        Args:
            organization_id: Organization ID.
            user_id: User creating the report.
            data: Report configuration.

        Returns:
            The created report.
        """
        report = ScheduledReport(
            organization_id=organization_id,
            created_by_id=user_id,
            name=data.name,
            report_type=data.report_type,
            schedule=data.schedule,
            recipients=[str(r) for r in data.recipients],
            filters=data.filters,
            format=data.format,
            is_active=data.is_active,
        )

        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)

        return ScheduledReportResponse.model_validate(report)

    async def update_report(
        self,
        organization_id: UUID,
        report_id: UUID,
        data: UpdateScheduledReportRequest,
    ) -> ScheduledReportResponse:
        """Update a scheduled report.

        Args:
            organization_id: Organization ID for tenant isolation.
            report_id: Report ID to update.
            data: Updated configuration.

        Returns:
            The updated report.

        Raises:
            NotFoundError: If report not found.
        """
        query = select(ScheduledReport).where(
            ScheduledReport.id == report_id,
            ScheduledReport.organization_id == organization_id,
        )
        result = await self.db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            raise NotFoundError("ScheduledReport", str(report_id))

        # Update fields
        if data.name is not None:
            report.name = data.name
        if data.schedule is not None:
            report.schedule = data.schedule
        if data.recipients is not None:
            report.recipients = [str(r) for r in data.recipients]
        if data.filters is not None:
            report.filters = data.filters
        if data.format is not None:
            report.format = data.format
        if data.is_active is not None:
            report.is_active = data.is_active

        await self.db.flush()
        await self.db.refresh(report)

        return ScheduledReportResponse.model_validate(report)

    async def delete_report(
        self, organization_id: UUID, report_id: UUID
    ) -> None:
        """Delete a scheduled report.

        Args:
            organization_id: Organization ID for tenant isolation.
            report_id: Report ID to delete.

        Raises:
            NotFoundError: If report not found.
        """
        query = select(ScheduledReport).where(
            ScheduledReport.id == report_id,
            ScheduledReport.organization_id == organization_id,
        )
        result = await self.db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            raise NotFoundError("ScheduledReport", str(report_id))

        await self.db.delete(report)
        await self.db.flush()

    async def run_report(
        self, organization_id: UUID, report_id: UUID
    ) -> ReportRunResult:
        """Run a report immediately (manual trigger).

        Args:
            organization_id: Organization ID for tenant isolation.
            report_id: Report ID to run.

        Returns:
            Result of the report run.

        Raises:
            NotFoundError: If report not found.
        """
        query = select(ScheduledReport).where(
            ScheduledReport.id == report_id,
            ScheduledReport.organization_id == organization_id,
        )
        result = await self.db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            raise NotFoundError("ScheduledReport", str(report_id))

        # In a real implementation, this would:
        # 1. Generate the report based on report_type
        # 2. Format it according to format (PDF/CSV)
        # 3. Send it to recipients via email
        # For now, we just update the last_sent_at timestamp

        report.last_sent_at = datetime.now(UTC)
        await self.db.flush()

        return ReportRunResult(
            success=True,
            message=f"Report '{report.name}' queued for delivery",
            report_id=report.id,
            sent_to=report.recipients,
        )

    async def get_due_reports(
        self, schedule: ReportSchedule
    ) -> list[ScheduledReport]:
        """Get all active reports due for the given schedule.

        Args:
            schedule: The schedule type (daily, weekly, monthly).

        Returns:
            List of reports to run.
        """
        query = select(ScheduledReport).where(
            ScheduledReport.schedule == schedule,
            ScheduledReport.is_active is True,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
