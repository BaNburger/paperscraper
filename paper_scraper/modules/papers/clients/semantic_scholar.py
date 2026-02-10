"""Semantic Scholar API client for paper search and citation data."""

import logging

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient

logger = logging.getLogger(__name__)

# Fields to request from Semantic Scholar API
_PAPER_FIELDS = ",".join([
    "paperId",
    "externalIds",
    "title",
    "abstract",
    "year",
    "venue",
    "publicationDate",
    "journal",
    "referenceCount",
    "citationCount",
    "fieldsOfStudy",
    "authors",
])

_CITATION_FIELDS = "paperId,title,year,citationCount"


class SemanticScholarClient(BaseAPIClient):
    """Client for Semantic Scholar API.

    Provides paper search, metadata, and citation graph data.
    Free tier: 100 requests/5 min without API key, 1 request/sec with key.

    Docs: https://api.semanticscholar.org/api-docs/
    """

    def __init__(self) -> None:
        """Initialize Semantic Scholar client."""
        super().__init__(timeout=30.0)
        self.base_url = settings.SEMANTIC_SCHOLAR_BASE_URL
        self.api_key = settings.SEMANTIC_SCHOLAR_API_KEY

    def _headers(self) -> dict[str, str]:
        """Get request headers, including API key if available."""
        headers: dict[str, str] = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def search(
        self,
        query: str,
        max_results: int = 100,
        year: str | None = None,
        fields_of_study: list[str] | None = None,
    ) -> list[dict]:
        """Search for papers on Semantic Scholar.

        Args:
            query: Search query string.
            max_results: Maximum number of results (max 100 per request).
            year: Year filter (e.g., "2020-2024" or "2023").
            fields_of_study: Filter by fields (e.g., ["Computer Science"]).

        Returns:
            List of normalized paper dictionaries.
        """
        papers = []
        offset = 0

        while len(papers) < max_results:
            remaining = max_results - len(papers)
            params: dict = {
                "query": query,
                "offset": offset,
                "limit": min(remaining, 100),
                "fields": _PAPER_FIELDS,
            }
            if year:
                params["year"] = year
            if fields_of_study:
                params["fieldsOfStudy"] = ",".join(fields_of_study)

            try:
                response = await self.client.get(
                    f"{self.base_url}/paper/search",
                    params=params,
                    headers=self._headers(),
                )
                response.raise_for_status()
            except Exception as e:
                logger.warning("Semantic Scholar search failed: %s", e)
                return papers

            data = response.json()
            batch = data.get("data", [])
            if not batch:
                break

            for paper in batch:
                normalized = self.normalize(paper)
                if normalized:
                    papers.append(normalized)
                    if len(papers) >= max_results:
                        break

            offset += len(batch)
            if len(batch) < params["limit"]:
                break

        return papers

    async def get_by_id(self, identifier: str) -> dict | None:
        """Get paper by Semantic Scholar ID or DOI.

        Args:
            identifier: Semantic Scholar paper ID or DOI (prefixed with DOI:).

        Returns:
            Normalized paper dict or None if not found.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/paper/{identifier}",
                params={"fields": _PAPER_FIELDS},
                headers=self._headers(),
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
        except Exception as e:
            logger.warning("Semantic Scholar get_by_id failed: %s", e)
            return None

        return self.normalize(response.json())

    async def get_citations(
        self,
        paper_id: str,
        max_results: int = 20,
    ) -> list[dict]:
        """Get papers that cite the given paper.

        Args:
            paper_id: Semantic Scholar paper ID.
            max_results: Maximum number of citing papers.

        Returns:
            List of citing paper dicts with id, title, year, citation_count.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/paper/{paper_id}/citations",
                params={
                    "fields": _CITATION_FIELDS,
                    "limit": min(max_results, 100),
                },
                headers=self._headers(),
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
        except Exception as e:
            logger.warning("Semantic Scholar get_citations failed: %s", e)
            return []

        data = response.json()
        citations = []
        for item in data.get("data", []):
            citing_paper = item.get("citingPaper", {})
            if citing_paper.get("paperId"):
                citations.append({
                    "paper_id": citing_paper["paperId"],
                    "title": citing_paper.get("title", "Unknown"),
                    "year": citing_paper.get("year"),
                    "citation_count": citing_paper.get("citationCount"),
                })
        return citations

    async def get_references(
        self,
        paper_id: str,
        max_results: int = 20,
    ) -> list[dict]:
        """Get papers referenced by the given paper.

        Args:
            paper_id: Semantic Scholar paper ID.
            max_results: Maximum number of referenced papers.

        Returns:
            List of referenced paper dicts.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/paper/{paper_id}/references",
                params={
                    "fields": _CITATION_FIELDS,
                    "limit": min(max_results, 100),
                },
                headers=self._headers(),
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
        except Exception as e:
            logger.warning("Semantic Scholar get_references failed: %s", e)
            return []

        data = response.json()
        refs = []
        for item in data.get("data", []):
            cited_paper = item.get("citedPaper", {})
            if cited_paper.get("paperId"):
                refs.append({
                    "paper_id": cited_paper["paperId"],
                    "title": cited_paper.get("title", "Unknown"),
                    "year": cited_paper.get("year"),
                    "citation_count": cited_paper.get("citationCount"),
                })
        return refs

    def normalize(self, paper: dict) -> dict:
        """Normalize Semantic Scholar paper to standard format.

        Args:
            paper: Raw Semantic Scholar paper data.

        Returns:
            Normalized paper dictionary.
        """
        if not paper:
            return {}

        # Extract DOI from external IDs
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")

        # Extract authors
        authors = []
        for author_data in paper.get("authors", []):
            authors.append({
                "name": author_data.get("name", "Unknown"),
                "semantic_scholar_id": author_data.get("authorId"),
                "orcid": None,
                "openalex_id": None,
                "affiliations": [],
                "is_corresponding": False,
            })

        # Journal info
        journal_info = paper.get("journal") or {}
        journal_name = journal_info.get("name") or paper.get("venue")
        volume = journal_info.get("volume")
        pages = journal_info.get("pages")

        return {
            "source": "semantic_scholar",
            "source_id": paper.get("paperId"),
            "doi": doi,
            "title": paper.get("title") or "Untitled",
            "abstract": paper.get("abstract"),
            "publication_date": paper.get("publicationDate"),
            "journal": journal_name,
            "volume": volume,
            "issue": None,
            "pages": pages,
            "keywords": paper.get("fieldsOfStudy") or [],
            "references_count": paper.get("referenceCount"),
            "citations_count": paper.get("citationCount"),
            "authors": authors,
            "raw_metadata": paper,
        }
