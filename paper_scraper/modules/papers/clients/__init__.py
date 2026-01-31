"""External API clients for paper data sources."""

from paper_scraper.modules.papers.clients.arxiv import ArxivClient
from paper_scraper.modules.papers.clients.crossref import CrossrefClient
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.clients.pubmed import PubMedClient

__all__ = ["OpenAlexClient", "CrossrefClient", "PubMedClient", "ArxivClient"]
