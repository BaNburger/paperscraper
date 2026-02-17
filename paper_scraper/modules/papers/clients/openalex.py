"""OpenAlex API client - Primary data source."""

import logging

import httpx

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient

logger = logging.getLogger(__name__)


class OpenAlexClient(BaseAPIClient):
    """Client for OpenAlex API.

    OpenAlex is a free, comprehensive catalog of scholarly papers.

    Features:
        - Free, no API key required
        - Email for polite pool (higher rate limits)
        - 100k requests/day limit

    Docs: https://docs.openalex.org/
    """

    def __init__(self):
        """Initialize OpenAlex client."""
        super().__init__()
        self.base_url = settings.OPENALEX_BASE_URL
        self.email = settings.OPENALEX_EMAIL

    async def search(
        self,
        query: str,
        max_results: int = 100,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search OpenAlex for papers.

        Args:
            query: Search query string.
            max_results: Maximum results (max 200 per page).
            filters: OpenAlex filters, e.g. {"publication_year": ">2020"}.

        Returns:
            List of normalized paper dicts.
        """
        papers = []
        per_page = min(max_results, 200)

        params: dict[str, str | int] = {
            "search": query,
            "per_page": per_page,
            "mailto": self.email,
            "cursor": "*",
        }

        if filters:
            filter_parts = [f"{k}:{v}" for k, v in filters.items()]
            params["filter"] = ",".join(filter_parts)

        while len(papers) < max_results:
            try:
                response = await self.client.get(
                    f"{self.base_url}/works",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning("OpenAlex search failed: %s", e)
                return papers
            except ValueError as e:
                logger.warning("OpenAlex returned invalid JSON: %s", e)
                return papers

            results = data.get("results", [])
            if not results:
                break

            for work in results:
                papers.append(self.normalize(work))
                if len(papers) >= max_results:
                    break

            next_cursor = (data.get("meta") or {}).get("next_cursor")
            if not next_cursor:
                break
            params["cursor"] = next_cursor

        return papers

    async def get_by_id(self, openalex_id: str) -> dict | None:
        """Get paper by OpenAlex ID (e.g., 'W2741809807').

        Args:
            openalex_id: OpenAlex work identifier.

        Returns:
            Normalized paper dict or None if not found.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/works/{openalex_id}",
                params={"mailto": self.email},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self.normalize(response.json())
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("OpenAlex get_by_id failed for %s: %s", openalex_id, e)
            return None
        except ValueError as e:
            logger.warning("OpenAlex get_by_id returned invalid JSON: %s", e)
            return None

    async def get_by_doi(self, doi: str) -> dict | None:
        """Get paper by DOI.

        Args:
            doi: Digital Object Identifier.

        Returns:
            Normalized paper dict or None if not found.
        """
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        try:
            response = await self.client.get(
                f"{self.base_url}/works/doi:{doi}",
                params={"mailto": self.email},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self.normalize(response.json())
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("OpenAlex get_by_doi failed for %s: %s", doi, e)
            return None
        except ValueError as e:
            logger.warning("OpenAlex get_by_doi returned invalid JSON: %s", e)
            return None

    async def _search_entity(
        self,
        endpoint: str,
        query: str,
        max_results: int,
    ) -> list[dict]:
        """Search an OpenAlex entity endpoint (institutions, authors, etc.).

        Args:
            endpoint: API endpoint path (e.g., "institutions", "authors").
            query: Search query string.
            max_results: Maximum results to return (max 25).

        Returns:
            List of raw result dicts from OpenAlex, or empty list on error.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/{endpoint}",
                params={
                    "search": query,
                    "per_page": min(max_results, 25),
                    "mailto": self.email,
                },
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("OpenAlex %s search failed: %s", endpoint, e)
            return []
        except ValueError as e:
            logger.warning("OpenAlex %s search returned invalid JSON: %s", endpoint, e)
            return []

    async def search_institutions(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """Search OpenAlex for institutions.

        Args:
            query: Search query string (e.g., "MIT", "Stanford").
            max_results: Maximum results to return (max 25).

        Returns:
            List of institution dicts with id, display_name, etc.
        """
        results = await self._search_entity("institutions", query, max_results)
        return [
            {
                "openalex_id": inst.get("id", ""),
                "display_name": inst.get("display_name", "Unknown"),
                "country_code": inst.get("country_code"),
                "type": inst.get("type"),
                "works_count": inst.get("works_count", 0),
                "cited_by_count": inst.get("cited_by_count", 0),
            }
            for inst in results
        ]

    async def search_authors(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """Search OpenAlex for authors.

        Args:
            query: Search query string (e.g., "John Smith").
            max_results: Maximum results to return (max 25).

        Returns:
            List of author dicts with id, display_name, etc.
        """
        results = await self._search_entity("authors", query, max_results)
        return [self._normalize_author_result(author) for author in results]

    def _normalize_author_result(self, author: dict) -> dict:
        """Normalize a raw OpenAlex author result."""
        institutions = author.get("last_known_institutions") or []
        return {
            "openalex_id": author.get("id", ""),
            "display_name": author.get("display_name", "Unknown"),
            "works_count": author.get("works_count", 0),
            "cited_by_count": author.get("cited_by_count", 0),
            "last_known_institution": institutions[0].get("display_name") if institutions else None,
        }

    def normalize(self, work: dict) -> dict:
        """Normalize OpenAlex work to standard format.

        Args:
            work: Raw OpenAlex work data.

        Returns:
            Normalized paper dictionary.
        """
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            authors.append(
                {
                    "name": author.get("display_name", "Unknown"),
                    "orcid": author.get("orcid"),
                    "openalex_id": author.get("id"),
                    "affiliations": [
                        inst.get("display_name")
                        for inst in authorship.get("institutions", [])
                        if inst.get("display_name")
                    ],
                    "is_corresponding": authorship.get("is_corresponding", False),
                }
            )

        # Extract venue/journal
        venue = work.get("primary_location", {}) or {}
        source = venue.get("source", {}) or {}

        # Clean DOI
        doi = work.get("doi")
        if doi:
            doi = doi.replace("https://doi.org/", "")

        return {
            "source": "openalex",
            "source_id": work.get("id"),
            "doi": doi,
            "title": work.get("title") or "Untitled",
            "abstract": work.get("abstract"),
            "publication_date": work.get("publication_date"),
            "journal": source.get("display_name"),
            "volume": work.get("biblio", {}).get("volume"),
            "issue": work.get("biblio", {}).get("issue"),
            "pages": self._format_pages(work.get("biblio", {})),
            "keywords": [
                kw.get("display_name")
                for kw in work.get("keywords", [])
                if kw.get("display_name")
            ],
            "references_count": work.get("referenced_works_count"),
            "citations_count": work.get("cited_by_count"),
            "authors": authors,
            "raw_metadata": work,
        }

    def _format_pages(self, biblio: dict) -> str | None:
        """Format page range from biblio dict.

        Args:
            biblio: Bibliography data with first_page and last_page.

        Returns:
            Formatted page range string or None.
        """
        first = biblio.get("first_page")
        last = biblio.get("last_page")
        if first and last:
            return f"{first}-{last}"
        return first or last
