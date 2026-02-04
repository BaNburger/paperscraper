"""Papers module - Paper management and ingestion."""

from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource
from paper_scraper.modules.papers.service import PaperService

# Note: router is not exported here to avoid circular imports.
# Import it directly: from paper_scraper.modules.papers.router import router

__all__ = ["Paper", "Author", "PaperAuthor", "PaperSource", "PaperService"]
