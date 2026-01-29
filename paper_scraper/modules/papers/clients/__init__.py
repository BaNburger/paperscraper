"""External API clients for paper data sources."""

from paper_scraper.modules.papers.clients.crossref import CrossrefClient
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient

__all__ = ["OpenAlexClient", "CrossrefClient"]
