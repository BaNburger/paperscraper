"""PubMed E-utilities API client."""

import logging
import xml.etree.ElementTree as ET

import httpx

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient

logger = logging.getLogger(__name__)


class PubMedClient(BaseAPIClient):
    """
    Client for PubMed E-utilities API.

    - Free, API key optional (higher rate limits with key)
    - Rate limit: 3 req/s without key, 10 req/s with key

    Docs: https://www.ncbi.nlm.nih.gov/books/NBK25497/
    """

    def __init__(self):
        super().__init__()
        self.base_url = settings.PUBMED_BASE_URL
        self.api_key = settings.PUBMED_API_KEY

    async def search(
        self,
        query: str,
        max_results: int = 100,
    ) -> list[dict]:
        """
        Search PubMed for papers.

        Args:
            query: PubMed search query
            max_results: Maximum results to return

        Returns:
            List of normalized paper dicts
        """
        # Step 1: Search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "usehistory": "y",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key

        try:
            search_response = await self.client.get(
                f"{self.base_url}/esearch.fcgi",
                params=search_params,
            )
            search_response.raise_for_status()
            search_data = search_response.json()
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("PubMed search failed: %s", e)
            return []
        except ValueError as e:
            logger.warning("PubMed search returned invalid JSON: %s", e)
            return []

        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []

        # Step 2: Fetch details for PMIDs
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "xml",
            "retmode": "xml",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        try:
            fetch_response = await self.client.get(
                f"{self.base_url}/efetch.fcgi",
                params=fetch_params,
            )
            fetch_response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("PubMed fetch failed: %s", e)
            return []

        # Parse XML response
        return self._parse_pubmed_xml(fetch_response.text)

    async def get_by_id(self, pmid: str) -> dict | None:
        """Get paper by PubMed ID."""
        params = {
            "db": "pubmed",
            "id": pmid,
            "rettype": "xml",
            "retmode": "xml",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self.client.get(
                f"{self.base_url}/efetch.fcgi",
                params=params,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("PubMed get_by_id failed for %s: %s", pmid, e)
            return None

        papers = self._parse_pubmed_xml(response.text)
        return papers[0] if papers else None

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        """Parse PubMed XML response."""
        root = ET.fromstring(xml_text)
        papers = []

        for article in root.findall(".//PubmedArticle"):
            papers.append(self.normalize(article))

        return papers

    def normalize(self, article: ET.Element) -> dict:
        """Normalize PubMed article to standard format."""
        medline = article.find(".//MedlineCitation")
        article_data = medline.find(".//Article")

        # Extract PMID
        pmid = medline.findtext("PMID", "")

        # Extract title
        title = article_data.findtext(".//ArticleTitle", "Untitled")

        # Extract abstract
        abstract_parts = []
        for abstract_text in article_data.findall(".//AbstractText"):
            label = abstract_text.get("Label", "")
            text = abstract_text.text or ""
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts) if abstract_parts else None

        # Extract authors
        authors = []
        for author in article_data.findall(".//Author"):
            last_name = author.findtext("LastName", "")
            first_name = author.findtext("ForeName", "")
            name = f"{first_name} {last_name}".strip()

            affiliations = [aff.text for aff in author.findall(".//Affiliation") if aff.text]

            authors.append(
                {
                    "name": name or "Unknown",
                    "affiliations": affiliations,
                }
            )

        # Extract publication date
        pub_date = article_data.find(".//PubDate")
        publication_date = None
        if pub_date is not None:
            year = pub_date.findtext("Year", "2000")
            month = pub_date.findtext("Month", "01")
            day = pub_date.findtext("Day", "01")
            # Convert month name to number if needed
            try:
                month = int(month)
            except ValueError:
                month_map = {
                    "Jan": 1,
                    "Feb": 2,
                    "Mar": 3,
                    "Apr": 4,
                    "May": 5,
                    "Jun": 6,
                    "Jul": 7,
                    "Aug": 8,
                    "Sep": 9,
                    "Oct": 10,
                    "Nov": 11,
                    "Dec": 12,
                }
                month = month_map.get(month[:3], 1)
            publication_date = f"{year}-{month:02d}-{int(day):02d}"

        # Extract journal
        journal = article_data.findtext(".//Journal/Title", None)

        # Extract DOI
        doi = None
        for article_id in article.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text
                break

        # Extract MeSH terms
        mesh_terms = [
            mesh.findtext("DescriptorName", "") for mesh in medline.findall(".//MeshHeading")
        ]

        return {
            "source": "pubmed",
            "source_id": pmid,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "publication_date": publication_date,
            "journal": journal,
            "authors": authors,
            "mesh_terms": [m for m in mesh_terms if m],
            "keywords": [],
            "raw_metadata": {"pmid": pmid},
        }
