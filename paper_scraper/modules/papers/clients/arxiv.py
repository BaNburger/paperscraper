"""arXiv API client."""

import asyncio
import time
import xml.etree.ElementTree as ET

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient


class ArxivClient(BaseAPIClient):
    """
    Client for arXiv API.

    - Free, no API key required
    - Rate limit: 1 request per 3 seconds

    Docs: https://info.arxiv.org/help/api/
    """

    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(self):
        super().__init__()
        self.base_url = settings.ARXIV_BASE_URL
        self._last_request = 0.0

    async def _rate_limit(self) -> None:
        """Ensure we don't exceed rate limit (1 req/3s)."""
        now = time.time()
        wait_time = 3 - (now - self._last_request)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self._last_request = time.time()

    async def search(
        self,
        query: str,
        max_results: int = 100,
        category: str | None = None,
    ) -> list[dict]:
        """
        Search arXiv for papers.

        Args:
            query: Search query
            max_results: Maximum results
            category: Optional category filter (e.g., "cs.AI", "physics.med-ph")

        Returns:
            List of normalized paper dicts
        """
        await self._rate_limit()

        search_query = query
        if category:
            search_query = f"cat:{category} AND all:{query}"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        response = await self.client.get(
            f"{self.base_url}/query",
            params=params,
        )
        response.raise_for_status()

        return self._parse_arxiv_xml(response.text)

    async def get_by_id(self, arxiv_id: str) -> dict | None:
        """
        Get paper by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2301.07041" or "arxiv:2301.07041")
        """
        await self._rate_limit()

        # Clean arXiv ID
        arxiv_id = arxiv_id.replace("arxiv:", "").replace("arXiv:", "")

        params = {"id_list": arxiv_id}

        response = await self.client.get(
            f"{self.base_url}/query",
            params=params,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()

        papers = self._parse_arxiv_xml(response.text)
        return papers[0] if papers else None

    def _parse_arxiv_xml(self, xml_text: str) -> list[dict]:
        """Parse arXiv Atom XML response."""
        root = ET.fromstring(xml_text)
        papers = []

        for entry in root.findall("atom:entry", self.NAMESPACES):
            papers.append(self.normalize(entry))

        return papers

    def normalize(self, entry: ET.Element) -> dict:
        """Normalize arXiv entry to standard format."""
        ns = self.NAMESPACES

        # Extract arXiv ID from URL
        id_url = entry.findtext("atom:id", "", ns)
        arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else id_url

        # Extract title (remove newlines)
        title = entry.findtext("atom:title", "Untitled", ns)
        title = " ".join(title.split())

        # Extract abstract (remove newlines)
        abstract = entry.findtext("atom:summary", "", ns)
        abstract = " ".join(abstract.split()) if abstract else None

        # Extract authors
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", "Unknown", ns)
            affiliation = author.findtext("arxiv:affiliation", None, ns)
            authors.append(
                {
                    "name": name,
                    "affiliations": [affiliation] if affiliation else [],
                }
            )

        # Extract publication date
        published = entry.findtext("atom:published", None, ns)
        publication_date = None
        if published:
            publication_date = published[:10]  # YYYY-MM-DD

        # Extract DOI
        doi = entry.findtext("arxiv:doi", None, ns)

        # Extract categories as keywords
        categories = [cat.get("term", "") for cat in entry.findall("atom:category", ns)]

        # Extract PDF link
        pdf_url = None
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break

        return {
            "source": "arxiv",
            "source_id": arxiv_id,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "publication_date": publication_date,
            "journal": "arXiv",
            "authors": authors,
            "keywords": [c for c in categories if c],
            "mesh_terms": [],
            "raw_metadata": {"arxiv_id": arxiv_id, "pdf_url": pdf_url},
        }
