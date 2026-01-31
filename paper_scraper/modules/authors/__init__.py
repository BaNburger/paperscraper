"""Authors module for author profiles and contact tracking."""

from paper_scraper.modules.authors.models import AuthorContact
from paper_scraper.modules.authors.router import router
from paper_scraper.modules.authors.service import AuthorService

__all__ = [
    "AuthorContact",
    "AuthorService",
    "router",
]
