"""EPO Open Patent Services (OPS) client for patent data."""

import base64
import logging
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree

import httpx

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)

# EPO OPS XML namespaces
NS = {
    "ops": "http://ops.epo.org",
    "exchange": "http://www.epo.org/exchange",
    "ft": "http://www.epo.org/fulltext",
}


class EPOOPSClient:
    """Client for EPO Open Patent Services API.

    Provides patent search and retrieval from the European Patent Office.
    Free tier: 4GB/week, ~3.5 req/sec.

    Docs: https://www.epo.org/searching-for-patents/data/web-services/ops.html
    """

    def __init__(self) -> None:
        """Initialize EPO OPS client."""
        self.base_url = settings.EPO_OPS_BASE_URL
        self.key = settings.EPO_OPS_KEY
        self.secret = settings.EPO_OPS_SECRET
        self._access_token: str | None = None
        self._token_expires: datetime | None = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def _authenticate(self) -> str:
        """Get OAuth2 access token from EPO OPS.

        Returns:
            Access token string.
        """
        if self._access_token and self._token_expires and datetime.now(UTC) < self._token_expires:
            return self._access_token

        if not self.key or not self.secret:
            raise ValueError("EPO_OPS_KEY and EPO_OPS_SECRET must be configured")

        secret_value = self.secret.get_secret_value() if hasattr(self.secret, "get_secret_value") else str(self.secret)
        credentials = base64.b64encode(f"{self.key}:{secret_value}".encode()).decode()

        response = await self.client.post(
            "https://ops.epo.org/3.2/auth/accesstoken",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 1200))
        self._token_expires = datetime.now(UTC) + timedelta(seconds=expires_in - 60)
        return self._access_token

    async def search_patents(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """Search patents related to a query.

        Args:
            query: Search query (title/abstract terms).
            max_results: Maximum number of results.

        Returns:
            List of patent dicts with title, number, abstract, applicant, etc.
        """
        if not self.key or not self.secret:
            logger.warning("EPO OPS credentials not configured, returning empty results")
            return []

        try:
            token = await self._authenticate()
        except Exception as e:
            logger.warning("EPO OPS authentication failed: %s", e)
            return []

        # CQL query: search in title and abstract
        escaped_query = query.replace('"', '\\"')
        cql_query = f'ta="{escaped_query}"'
        params = {
            "q": cql_query,
            "Range": f"1-{min(max_results, 100)}",
        }

        try:
            response = await self.client.get(
                f"{self.base_url}/rest-services/published-data/search",
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/xml",
                },
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning("EPO OPS search failed: %s", e)
            return []

        return self._parse_search_results(response.text)

    async def get_patent(self, patent_number: str) -> dict | None:
        """Get patent details by publication number.

        Args:
            patent_number: Patent publication number (e.g., 'EP1234567').

        Returns:
            Patent dict or None if not found.
        """
        if not self.key or not self.secret:
            return None

        try:
            token = await self._authenticate()
            response = await self.client.get(
                f"{self.base_url}/rest-services/published-data/publication/epodoc/{patent_number}/biblio",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/xml",
                },
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
        except (httpx.HTTPStatusError, ValueError) as e:
            logger.warning("EPO OPS get_patent failed: %s", e)
            return None

        patents = self._parse_biblio_response(response.text)
        return patents[0] if patents else None

    def _parse_search_results(self, xml_text: str) -> list[dict]:
        """Parse EPO OPS search XML response.

        Args:
            xml_text: Raw XML response text.

        Returns:
            List of patent dicts.
        """
        patents: list[dict] = []
        try:
            root = ElementTree.fromstring(xml_text)
            for doc in root.iter(f"{{{NS['exchange']}}}exchange-document"):
                patent = self._extract_patent_from_element(doc)
                if patent:
                    patents.append(patent)
        except ElementTree.ParseError as e:
            logger.warning("Failed to parse EPO OPS XML: %s", e)
        return patents

    def _parse_biblio_response(self, xml_text: str) -> list[dict]:
        """Parse EPO OPS bibliographic XML response.

        Args:
            xml_text: Raw XML response text.

        Returns:
            List of patent dicts.
        """
        patents: list[dict] = []
        try:
            root = ElementTree.fromstring(xml_text)
            for doc in root.iter(f"{{{NS['exchange']}}}exchange-document"):
                patent = self._extract_patent_from_element(doc)
                if patent:
                    patents.append(patent)
        except ElementTree.ParseError as e:
            logger.warning("Failed to parse EPO OPS biblio XML: %s", e)
        return patents

    def _extract_patent_from_element(self, doc: ElementTree.Element) -> dict | None:
        """Extract patent data from an exchange-document XML element.

        Args:
            doc: XML element for an exchange-document.

        Returns:
            Patent dict or None.
        """
        country = doc.get("country", "")
        doc_number = doc.get("doc-number", "")
        kind = doc.get("kind", "")
        patent_number = f"{country}{doc_number}{kind}".strip()

        if not patent_number:
            return None

        # Extract title (prefer English)
        title = ""
        for title_el in doc.iter(f"{{{NS['exchange']}}}invention-title"):
            lang = title_el.get("lang", "")
            text = title_el.text or ""
            if lang == "en" or not title:
                title = text

        # Extract abstract (prefer English)
        abstract = ""
        for abs_el in doc.iter(f"{{{NS['exchange']}}}abstract"):
            lang = abs_el.get("lang", "")
            text = "".join(abs_el.itertext()).strip()
            if lang == "en" or not abstract:
                abstract = text

        # Extract applicant
        applicant = ""
        for app_el in doc.iter(f"{{{NS['exchange']}}}applicant"):
            name_el = app_el.find(f"{{{NS['exchange']}}}applicant-name/{{{NS['exchange']}}}name")
            if name_el is not None and name_el.text:
                applicant = name_el.text
                break

        # Extract dates
        filing_date = ""
        for date_el in doc.iter(f"{{{NS['exchange']}}}application-reference"):
            date_node = date_el.find(f"{{{NS['exchange']}}}document-id/{{{NS['exchange']}}}date")
            if date_node is not None and date_node.text:
                filing_date = date_node.text
                break

        pub_date = ""
        for date_el in doc.iter(f"{{{NS['exchange']}}}publication-reference"):
            date_node = date_el.find(f"{{{NS['exchange']}}}document-id/{{{NS['exchange']}}}date")
            if date_node is not None and date_node.text:
                pub_date = date_node.text
                break

        espacenet_url = f"https://worldwide.espacenet.com/patent/search?q=pn%3D{patent_number}"

        return {
            "patent_number": patent_number,
            "title": title,
            "abstract": abstract[:500] if abstract else None,
            "applicant": applicant or None,
            "filing_date": self._format_date(filing_date),
            "publication_date": self._format_date(pub_date),
            "espacenet_url": espacenet_url,
        }

    @staticmethod
    def _format_date(date_str: str) -> str | None:
        """Format EPO date string (YYYYMMDD) to ISO format.

        Args:
            date_str: Date in YYYYMMDD format.

        Returns:
            ISO date string or None.
        """
        if date_str and len(date_str) >= 8:
            try:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except (IndexError, ValueError):
                pass
        return None
