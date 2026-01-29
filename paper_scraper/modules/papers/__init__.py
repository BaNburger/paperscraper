"""Papers module - Paper management and ingestion."""

from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource
from paper_scraper.modules.papers.router import router
from paper_scraper.modules.papers.service import PaperService

__all__ = ["Paper", "Author", "PaperAuthor", "PaperSource", "PaperService", "router"]
