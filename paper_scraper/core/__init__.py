"""Core utilities and configuration for Paper Scraper."""

from paper_scraper.core.config import settings
from paper_scraper.core.database import Base, DbSession, get_db
from paper_scraper.core.exceptions import (
    DuplicateError,
    ExternalAPIError,
    ForbiddenError,
    NotFoundError,
    PaperScraperException,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    # Config
    "settings",
    # Database
    "Base",
    "DbSession",
    "get_db",
    # Exceptions
    "DuplicateError",
    "ExternalAPIError",
    "ForbiddenError",
    "NotFoundError",
    "PaperScraperException",
    "UnauthorizedError",
    "ValidationError",
]
