"""Scheduled reports module for automated report generation."""

from paper_scraper.modules.reports.models import ScheduledReport
from paper_scraper.modules.reports.router import router as reports_router
from paper_scraper.modules.reports.service import ReportsService

__all__ = ["ScheduledReport", "reports_router", "ReportsService"]
