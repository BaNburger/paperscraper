"""Alerts module for search notifications and email alerts."""

from paper_scraper.modules.alerts.models import Alert, AlertResult
from paper_scraper.modules.alerts.router import router
from paper_scraper.modules.alerts.service import AlertService

__all__ = ["Alert", "AlertResult", "AlertService", "router"]
