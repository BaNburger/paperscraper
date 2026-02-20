"""USPTO PatentsView API client for US patent data."""

import logging
from typing import Any

import httpx

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)


class USPTOClient:
    """Client for USPTO PatentsView API.

    Provides US patent search and retrieval.
    Free API, no strict rate limit (be polite: ~10 req/s).

    Docs: https://patentsview.org/apis/api-endpoints
    """

    def __init__(self) -> None:
        """Initialize USPTO PatentsView client."""
        self.base_url = settings.USPTO_BASE_URL
        self.api_key = settings.USPTO_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    async def search_patents(
        self,
        query: str,
        max_results: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search US patents via PatentsView API.

        Args:
            query: Search query string (searches title and abstract).
            max_results: Maximum results per page (max 10000).
            offset: Pagination offset.

        Returns:
            Raw API response dict with 'patents' and 'total_patent_count'.
        """
        body: dict[str, Any] = {
            "q": {
                "_or": [
                    {"_text_any": {"patent_title": query}},
                    {"_text_any": {"patent_abstract": query}},
                ],
            },
            "f": [
                "patent_number",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "patent_type",
                "patent_num_cited_by_us_patents",
                "app_date",
            ],
            "o": {
                "page": (offset // max_results) + 1,
                "per_page": min(max_results, 1000),
            },
            "s": [{"patent_date": "desc"}],
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/patents/query",
                json=body,
                headers=self._headers(),
            )
            if response.status_code == 404:
                return {"patents": [], "total_patent_count": 0}
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("USPTO PatentsView search failed: %s", e)
            return {"patents": [], "total_patent_count": 0}

    async def get_patent(self, patent_number: str) -> dict[str, Any] | None:
        """Get a specific patent by number.

        Args:
            patent_number: US patent number.

        Returns:
            Normalized patent dict or None.
        """
        body: dict[str, Any] = {
            "q": {"patent_number": patent_number},
            "f": [
                "patent_number",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "patent_type",
                "patent_num_cited_by_us_patents",
                "app_date",
                "assignees",
                "inventors",
                "cpcs",
            ],
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/patents/query",
                json=body,
                headers=self._headers(),
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            patents = data.get("patents", [])
            return self.normalize(patents[0]) if patents else None
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("USPTO get_patent failed for %s: %s", patent_number, e)
            return None

    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize a USPTO PatentsView record to standard format.

        Args:
            record: Raw PatentsView patent record.

        Returns:
            Normalized paper dict compatible with ingestion pipeline.
        """
        patent_number = record.get("patent_number", "")
        title = record.get("patent_title", "Untitled")
        abstract = record.get("patent_abstract")

        # Extract assignees as "authors"
        authors = []
        for assignee in record.get("assignees", []) or []:
            org_name = assignee.get("assignee_organization") or ""
            first = assignee.get("assignee_first_name") or ""
            last = assignee.get("assignee_last_name") or ""
            name = org_name or f"{first} {last}".strip()
            if name:
                authors.append({"name": name, "orcid": None, "affiliations": []})

        # Extract inventors if no assignees
        if not authors:
            for inventor in record.get("inventors", []) or []:
                first = inventor.get("inventor_first_name") or ""
                last = inventor.get("inventor_last_name") or ""
                name = f"{first} {last}".strip()
                if name:
                    authors.append({"name": name, "orcid": None, "affiliations": []})

        # CPC codes as keywords
        cpc_codes = []
        for cpc in record.get("cpcs", []) or []:
            code = cpc.get("cpc_group_id") or cpc.get("cpc_subgroup_id")
            if code:
                cpc_codes.append(code)

        return {
            "source": "uspto",
            "source_id": f"US{patent_number}",
            "doi": None,
            "title": title or "Untitled",
            "abstract": abstract[:2000] if abstract else None,
            "publication_date": record.get("patent_date"),
            "journal": None,
            "keywords": cpc_codes[:10],
            "authors": authors,
            "citations_count": record.get("patent_num_cited_by_us_patents"),
            "raw_metadata": {
                "patent_number": f"US{patent_number}",
                "filing_date": record.get("app_date"),
                "patent_type": record.get("patent_type"),
                "cpc_codes": cpc_codes,
                "paper_type": "patent",
            },
        }
