"""Compliance module for enterprise governance, audit, and data retention."""

from paper_scraper.modules.compliance.models import RetentionAction, RetentionPolicy

__all__ = [
    "RetentionPolicy",
    "RetentionAction",
]


def get_router():
    """Lazy import of router to avoid circular imports."""
    from paper_scraper.modules.compliance.router import router
    return router


def get_service():
    """Lazy import of service to avoid circular imports."""
    from paper_scraper.modules.compliance.service import ComplianceService
    return ComplianceService
