"""OpenAlex API client - Primary data source."""

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient


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
            response = await self.client.get(
                f"{self.base_url}/works",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

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
        response = await self.client.get(
            f"{self.base_url}/works/{openalex_id}",
            params={"mailto": self.email},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self.normalize(response.json())

    async def get_by_doi(self, doi: str) -> dict | None:
        """Get paper by DOI.

        Args:
            doi: Digital Object Identifier.

        Returns:
            Normalized paper dict or None if not found.
        """
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        response = await self.client.get(
            f"{self.base_url}/works/doi:{doi}",
            params={"mailto": self.email},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self.normalize(response.json())

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
