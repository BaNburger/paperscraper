"""Core utilities and configuration for Paper Scraper."""

from paper_scraper.core.config import settings
from paper_scraper.core.database import Base, get_db
from paper_scraper.core.exceptions import (
    PaperScraperException,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ValidationError,
)

__all__ = [
    "settings",
    "Base",
    "get_db",
    "PaperScraperException",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "ValidationError",
]
