"""Saved searches module for persisting and sharing search queries."""

from paper_scraper.modules.saved_searches.models import SavedSearch
from paper_scraper.modules.saved_searches.router import router
from paper_scraper.modules.saved_searches.service import SavedSearchService

__all__ = ["SavedSearch", "SavedSearchService", "router"]
