"""Notifications module for server-side notification persistence."""

from paper_scraper.modules.notifications.models import Notification
from paper_scraper.modules.notifications.router import router
from paper_scraper.modules.notifications.service import NotificationService

__all__ = ["Notification", "NotificationService", "router"]
