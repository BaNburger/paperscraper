"""Lens.org API client for scholarly + patent data."""

import logging
from typing import Any

import httpx

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)


class LensClient:
    """Client for Lens.org API.

    Provides patent and scholarly work search.
    Free tier: 50 req/min, 1000 results per request.

    Docs: https://docs.api.lens.org/
    """

    def __init__(self) -> None:
        """Initialize Lens.org client."""
        self.base_url = settings.LENS_BASE_URL
        self.api_key = settings.LENS_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def _headers(self) -> dict[str, str]:
        """Build request headers with auth."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def search_patents(
        self,
        query: str,
        max_results: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search patents via Lens.org API.

        Args:
            query: Search query string.
            max_results: Maximum results per page (max 1000).
            offset: Pagination offset.

        Returns:
            Raw API response dict with 'data' and 'total' keys.
        """
        if not self.api_key:
            logger.warning("LENS_API_KEY not configured, returning empty results")
            return {"data": [], "total": 0}

        body: dict[str, Any] = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"title": query}},
                    ],
                },
            },
            "size": min(max_results, 1000),
            "from": offset,
            "include": [
                "lens_id",
                "doc_number",
                "jurisdiction",
                "kind",
                "date_published",
                "filing_date",
                "title",
                "abstract",
                "applicant",
                "inventor",
                "classification_ipc",
                "family_id",
                "cited_by.patent_count",
                "reference.cited_by.scholarly",
            ],
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/patent/search",
                json=body,
                headers=self._headers(),
            )
            if response.status_code == 404:
                return {"data": [], "total": 0}
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("Lens.org patent search failed: %s", e)
            return {"data": [], "total": 0}

    async def search_scholarly(
        self,
        query: str,
        max_results: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search scholarly works via Lens.org API.

        Args:
            query: Search query string.
            max_results: Maximum results per page (max 1000).
            offset: Pagination offset.

        Returns:
            Raw API response dict with 'data' and 'total' keys.
        """
        if not self.api_key:
            logger.warning("LENS_API_KEY not configured, returning empty results")
            return {"data": [], "total": 0}

        body: dict[str, Any] = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"title": query}},
                    ],
                },
            },
            "size": min(max_results, 1000),
            "from": offset,
            "include": [
                "lens_id",
                "doi",
                "title",
                "abstract",
                "date_published",
                "year_published",
                "source",
                "authors",
                "fields_of_study",
                "references_count",
                "scholarly_citations_count",
                "external_ids",
            ],
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/scholarly/search",
                json=body,
                headers=self._headers(),
            )
            if response.status_code == 404:
                return {"data": [], "total": 0}
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("Lens.org scholarly search failed: %s", e)
            return {"data": [], "total": 0}

    def normalize_patent(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Lens.org patent record to standard format.

        Args:
            record: Raw Lens.org patent API record.

        Returns:
            Normalized paper dict compatible with ingestion pipeline.
        """
        title_data = record.get("title") or {}
        title = title_data if isinstance(title_data, str) else title_data.get("text", "Untitled")

        abstract_data = record.get("abstract") or {}
        abstract = abstract_data if isinstance(abstract_data, str) else abstract_data.get("text")

        # Extract applicant names
        applicants = record.get("applicant", [])
        authors = []
        for app in applicants[:20]:
            name = app.get("extracted_name", {}).get("value", "") if isinstance(app, dict) else str(app)
            if name:
                authors.append({"name": name, "orcid": None, "affiliations": []})

        # IPC codes
        ipc_codes = []
        for ipc in record.get("classification_ipc", []) or []:
            code = ipc.get("symbol") if isinstance(ipc, dict) else str(ipc)
            if code:
                ipc_codes.append(code)

        patent_number = record.get("doc_number", "")
        jurisdiction = record.get("jurisdiction", "")

        return {
            "source": "lens",
            "source_id": record.get("lens_id"),
            "doi": None,
            "title": title or "Untitled",
            "abstract": abstract[:2000] if abstract else None,
            "publication_date": record.get("date_published"),
            "journal": None,
            "keywords": ipc_codes[:10],
            "authors": authors,
            "citations_count": record.get("cited_by", {}).get("patent_count"),
            "raw_metadata": {
                "patent_number": f"{jurisdiction}{patent_number}",
                "jurisdiction": jurisdiction,
                "kind": record.get("kind"),
                "filing_date": record.get("filing_date"),
                "family_id": record.get("family_id"),
                "ipc_codes": ipc_codes,
                "paper_type": "patent",
            },
        }
