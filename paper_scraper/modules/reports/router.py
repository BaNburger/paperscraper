"""FastAPI router for scheduled reports endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser, require_permission
from paper_scraper.core.database import get_db
from paper_scraper.core.permissions import Permission
from paper_scraper.modules.reports.schemas import (
    CreateScheduledReportRequest,
    ReportRunResult,
    ScheduledReportListResponse,
    ScheduledReportResponse,
    UpdateScheduledReportRequest,
)
from paper_scraper.modules.reports.service import ReportsService

router = APIRouter()


def get_reports_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportsService:
    """Dependency to get reports service instance."""
    return ReportsService(db)


@router.get(
    "/scheduled",
    response_model=ScheduledReportListResponse,
    summary="List scheduled reports",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def list_scheduled_reports(
    current_user: CurrentUser,
    reports_service: Annotated[ReportsService, Depends(get_reports_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
) -> ScheduledReportListResponse:
    """List all scheduled reports for the organization.

    Returns paginated list of scheduled reports.
    """
    return await reports_service.list_reports(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        is_active=is_active,
    )


@router.get(
    "/scheduled/{report_id}",
    response_model=ScheduledReportResponse,
    summary="Get scheduled report",
    dependencies=[Depends(require_permission(Permission.PAPERS_READ))],
)
async def get_scheduled_report(
    report_id: UUID,
    current_user: CurrentUser,
    reports_service: Annotated[ReportsService, Depends(get_reports_service)],
) -> ScheduledReportResponse:
    """Get a specific scheduled report."""
    return await reports_service.get_report(
        organization_id=current_user.organization_id,
        report_id=report_id,
    )


@router.post(
    "/scheduled",
    response_model=ScheduledReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create scheduled report",
    dependencies=[Depends(require_permission(Permission.SETTINGS_ADMIN))],
)
async def create_scheduled_report(
    data: CreateScheduledReportRequest,
    current_user: CurrentUser,
    reports_service: Annotated[ReportsService, Depends(get_reports_service)],
) -> ScheduledReportResponse:
    """Create a new scheduled report.

    The report will be sent to the specified recipients
    according to the schedule (daily, weekly, or monthly).
    """
    return await reports_service.create_report(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        data=data,
    )


@router.patch(
    "/scheduled/{report_id}",
    response_model=ScheduledReportResponse,
    summary="Update scheduled report",
    dependencies=[Depends(require_permission(Permission.SETTINGS_ADMIN))],
)
async def update_scheduled_report(
    report_id: UUID,
    data: UpdateScheduledReportRequest,
    current_user: CurrentUser,
    reports_service: Annotated[ReportsService, Depends(get_reports_service)],
) -> ScheduledReportResponse:
    """Update a scheduled report configuration."""
    return await reports_service.update_report(
        organization_id=current_user.organization_id,
        report_id=report_id,
        data=data,
    )


@router.delete(
    "/scheduled/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete scheduled report",
    dependencies=[Depends(require_permission(Permission.SETTINGS_ADMIN))],
)
async def delete_scheduled_report(
    report_id: UUID,
    current_user: CurrentUser,
    reports_service: Annotated[ReportsService, Depends(get_reports_service)],
) -> None:
    """Delete a scheduled report."""
    await reports_service.delete_report(
        organization_id=current_user.organization_id,
        report_id=report_id,
    )


@router.post(
    "/scheduled/{report_id}/run",
    response_model=ReportRunResult,
    summary="Run report immediately",
    dependencies=[Depends(require_permission(Permission.SETTINGS_ADMIN))],
)
async def run_scheduled_report(
    report_id: UUID,
    current_user: CurrentUser,
    reports_service: Annotated[ReportsService, Depends(get_reports_service)],
) -> ReportRunResult:
    """Run a scheduled report immediately.

    This triggers an immediate generation and delivery of the report,
    regardless of its schedule.
    """
    return await reports_service.run_report(
        organization_id=current_user.organization_id,
        report_id=report_id,
    )
