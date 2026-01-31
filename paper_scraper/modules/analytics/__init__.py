"""Analytics module for team and paper metrics."""

from paper_scraper.modules.analytics.router import router
from paper_scraper.modules.analytics.service import AnalyticsService

__all__ = ["router", "AnalyticsService"]
