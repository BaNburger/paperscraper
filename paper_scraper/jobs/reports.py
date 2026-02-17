"""Background jobs for scheduled report generation and delivery."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.database import get_db_session
from paper_scraper.modules.analytics.service import AnalyticsService
from paper_scraper.modules.email.service import email_service
from paper_scraper.modules.reports.models import (
    ReportSchedule,
    ReportType,
    ScheduledReport,
)

logger = logging.getLogger(__name__)


async def generate_report_content(
    db: AsyncSession,
    report: ScheduledReport,
) -> str:
    """Generate report content based on report type.

    Args:
        db: Database session.
        report: The scheduled report configuration.

    Returns:
        Report content as string (HTML for email body).
    """
    analytics_service = AnalyticsService(db)

    if report.report_type == ReportType.DASHBOARD_SUMMARY:
        summary = await analytics_service.get_dashboard_summary(report.organization_id)
        return f"""
        <h2>Dashboard Summary Report</h2>
        <p>Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}</p>

        <h3>Key Metrics</h3>
        <ul>
            <li><strong>Total Papers:</strong> {summary.total_papers}</li>
            <li><strong>Papers This Week:</strong> {summary.papers_this_week}</li>
            <li><strong>Papers This Month:</strong> {summary.papers_this_month}</li>
            <li><strong>Scored Papers:</strong> {summary.scored_papers}</li>
            <li><strong>Average Score:</strong> {summary.average_score:.1f if summary.average_score else 'N/A'}</li>
            <li><strong>Total Projects:</strong> {summary.total_projects}</li>
            <li><strong>Active Users:</strong> {summary.active_users}</li>
        </ul>
        """

    elif report.report_type == ReportType.PAPER_TRENDS:
        analytics = await analytics_service.get_paper_analytics(report.organization_id, days=30)
        source_breakdown = "".join(
            f"<li>{s.source}: {s.count} ({s.percentage:.1f}%)</li>"
            for s in analytics.import_trends.by_source
        )
        return f"""
        <h2>Paper Trends Report</h2>
        <p>Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}</p>

        <h3>Import Statistics (Last 30 Days)</h3>
        <ul>
            <li><strong>Total Scored:</strong> {analytics.scoring_stats.total_scored}</li>
            <li><strong>Total Unscored:</strong> {analytics.scoring_stats.total_unscored}</li>
            <li><strong>Average Overall Score:</strong> {analytics.scoring_stats.average_overall_score:.1f if analytics.scoring_stats.average_overall_score else 'N/A'}</li>
            <li><strong>Embedding Coverage:</strong> {analytics.embedding_coverage_percent:.1f}%</li>
        </ul>

        <h3>Papers by Source</h3>
        <ul>{source_breakdown}</ul>
        """

    elif report.report_type == ReportType.TEAM_ACTIVITY:
        team = await analytics_service.get_team_overview(report.organization_id)
        user_activity = "".join(
            f"<li>{u.email}: {u.notes_created} notes</li>"
            for u in team.user_activity[:10]
        )
        return f"""
        <h2>Team Activity Report</h2>
        <p>Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}</p>

        <h3>Team Overview</h3>
        <ul>
            <li><strong>Total Users:</strong> {team.total_users}</li>
            <li><strong>Active (Last 7 Days):</strong> {team.active_users_last_7_days}</li>
            <li><strong>Active (Last 30 Days):</strong> {team.active_users_last_30_days}</li>
            <li><strong>Total Papers:</strong> {team.total_papers}</li>
            <li><strong>Total Scores:</strong> {team.total_scores}</li>
            <li><strong>Total Projects:</strong> {team.total_projects}</li>
        </ul>

        <h3>User Activity</h3>
        <ul>{user_activity}</ul>
        """

    return "<p>Report content not available.</p>"


async def send_report_email(
    report: ScheduledReport,
    content: str,
) -> None:
    """Send report email to recipients.

    Args:
        report: The scheduled report configuration.
        content: Report HTML content.
    """
    subject = f"[Paper Scraper] {report.name} - {report.report_type.value.replace('_', ' ').title()}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px; }}
            h2 {{ color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
            h3 {{ color: #4b5563; margin-top: 20px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        {content}
        <hr style="margin-top: 30px; border: none; border-top: 1px solid #e5e7eb;">
        <p style="color: #9ca3af; font-size: 12px;">
            This is an automated report from Paper Scraper.<br>
            To manage your report settings, visit your analytics dashboard.
        </p>
    </body>
    </html>
    """

    for recipient in report.recipients:
        try:
            await email_service.send_email(
                to=recipient,
                subject=subject,
                html_content=html_content,
            )
            logger.info(f"Sent report '{report.name}' to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send report '{report.name}' to {recipient}: {e}")


async def process_scheduled_reports_task(
    ctx: dict[str, Any],
    schedule: str,
) -> dict[str, Any]:
    """Process all scheduled reports for a given schedule type.

    Args:
        ctx: Worker context.
        schedule: Schedule type ('daily', 'weekly', 'monthly').

    Returns:
        Dict with processing results.
    """
    logger.info(f"Processing {schedule} scheduled reports")

    try:
        report_schedule = ReportSchedule(schedule)
    except ValueError:
        return {"error": f"Invalid schedule: {schedule}", "processed": 0}

    async with get_db_session() as db:
        # Get all active reports for this schedule
        query = select(ScheduledReport).where(
            ScheduledReport.schedule == report_schedule,
            ScheduledReport.is_active.is_(True),
        )
        result = await db.execute(query)
        reports = result.scalars().all()

        processed = 0
        errors = 0

        for report in reports:
            try:
                content = await generate_report_content(db, report)
                await send_report_email(report, content)

                # Update last_sent_at
                report.last_sent_at = datetime.now(UTC)
                await db.commit()

                processed += 1
                logger.info(f"Processed report '{report.name}'")
            except Exception as e:
                errors += 1
                logger.error(f"Error processing report '{report.name}': {e}")

        return {
            "schedule": schedule,
            "total_reports": len(reports),
            "processed": processed,
            "errors": errors,
        }


async def process_daily_reports_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process daily scheduled reports."""
    return await process_scheduled_reports_task(ctx, "daily")


async def process_weekly_reports_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process weekly scheduled reports."""
    return await process_scheduled_reports_task(ctx, "weekly")


async def process_monthly_reports_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Process monthly scheduled reports."""
    return await process_scheduled_reports_task(ctx, "monthly")


async def run_single_report_task(
    ctx: dict[str, Any],
    report_id: str,
) -> dict[str, Any]:
    """Run a single report on demand.

    Args:
        ctx: Worker context.
        report_id: UUID of the report to run.

    Returns:
        Dict with run result.
    """
    logger.info(f"Running single report: {report_id}")

    async with get_db_session() as db:
        query = select(ScheduledReport).where(
            ScheduledReport.id == UUID(report_id)
        )
        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            return {"error": f"Report not found: {report_id}", "success": False}

        try:
            content = await generate_report_content(db, report)
            await send_report_email(report, content)

            report.last_sent_at = datetime.now(UTC)
            await db.commit()

            return {
                "success": True,
                "report_id": report_id,
                "report_name": report.name,
                "recipients": report.recipients,
            }
        except Exception as e:
            logger.error(f"Error running report '{report.name}': {e}")
            return {"error": str(e), "success": False, "report_id": report_id}
