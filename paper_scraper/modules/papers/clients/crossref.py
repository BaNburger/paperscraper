"""Crossref API client - DOI resolution fallback."""

import logging

import httpx

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient

logger = logging.getLogger(__name__)


class CrossrefClient(BaseAPIClient):
    """Client for Crossref API.

    Crossref is a DOI registration agency with comprehensive metadata.

    Features:
        - Free, email for polite pool
        - 50 req/s in polite pool

    Docs: https://api.crossref.org/
    """

    def __init__(self):
        """Initialize Crossref client."""
        super().__init__()
        self.base_url = settings.CROSSREF_BASE_URL
        self.email = settings.CROSSREF_EMAIL

    async def search(self, query: str, max_results: int = 100) -> list[dict]:
        """Search Crossref for papers.

        Args:
            query: Search query string.
            max_results: Maximum results to return.

        Returns:
            List of normalized paper dicts.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/works",
                params={
                    "query": query,
                    "rows": min(max_results, 1000),
                    "mailto": self.email,
                },
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("Crossref search failed: %s", e)
            return []
        except ValueError as e:
            logger.warning("Crossref returned invalid JSON: %s", e)
            return []

        return [self.normalize(item) for item in data.get("message", {}).get("items", [])]

    async def get_by_id(self, doi: str) -> dict | None:
        """Get paper by DOI from Crossref.

        Args:
            doi: Digital Object Identifier.

        Returns:
            Normalized paper dict or None if not found.
        """
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        try:
            response = await self.client.get(
                f"{self.base_url}/works/{doi}",
                params={"mailto": self.email},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self.normalize(response.json().get("message", {}))
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("Crossref get_by_id failed for %s: %s", doi, e)
            return None
        except ValueError as e:
            logger.warning("Crossref get_by_id returned invalid JSON: %s", e)
            return None

    def normalize(self, item: dict) -> dict:
        """Normalize Crossref item to standard format.

        Args:
            item: Raw Crossref work data.

        Returns:
            Normalized paper dictionary.
        """
        # Extract authors
        authors = []
        for author in item.get("author", []):
            name = f"{author.get('given', '')} {author.get('family', '')}".strip()
            authors.append(
                {
                    "name": name or "Unknown",
                    "orcid": author.get("ORCID"),
                    "affiliations": [
                        aff.get("name") for aff in author.get("affiliation", []) if aff.get("name")
                    ],
                }
            )

        # Extract publication date
        pub_date = self._extract_date(item)

        # Extract title
        title = item.get("title", ["Untitled"])
        if isinstance(title, list):
            title = title[0] if title else "Untitled"

        # Extract journal
        journal = item.get("container-title", [""])
        if isinstance(journal, list):
            journal = journal[0] if journal else None

        return {
            "source": "crossref",
            "source_id": item.get("DOI"),
            "doi": item.get("DOI"),
            "title": title,
            "abstract": item.get("abstract"),
            "publication_date": pub_date,
            "journal": journal,
            "volume": item.get("volume"),
            "issue": item.get("issue"),
            "pages": item.get("page"),
            "keywords": item.get("subject", []),
            "references_count": item.get("references-count"),
            "citations_count": item.get("is-referenced-by-count"),
            "authors": authors,
            "raw_metadata": item,
        }

    def _extract_date(self, item: dict) -> str | None:
        """Extract publication date from Crossref item.

        Args:
            item: Crossref work data.

        Returns:
            ISO date string or None.
        """
        for date_field in ["published-print", "published-online", "created"]:
            date_parts = item.get(date_field, {}).get("date-parts", [[]])[0]
            if date_parts:
                year = date_parts[0] if len(date_parts) > 0 else 2000
                month = date_parts[1] if len(date_parts) > 1 else 1
                day = date_parts[2] if len(date_parts) > 2 else 1
                return f"{year}-{month:02d}-{day:02d}"
        return None
