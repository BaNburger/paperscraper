"""Citation graph data fetching from OpenAlex for scoring context."""

import logging
import re
from dataclasses import dataclass, field

import httpx

from paper_scraper.core.config import settings

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")
OPENALEX_ID_PATTERN = re.compile(r"^W\d+$")

logger = logging.getLogger(__name__)

MAX_REFERENCES = 10
MAX_CITING_PAPERS = 10
REQUEST_TIMEOUT = 15.0


@dataclass
class CitationPaper:
    """Minimal paper representation from citation graph."""

    title: str
    doi: str | None = None
    publication_year: int | None = None
    cited_by_count: int | None = None

    def to_context_line(self) -> str:
        """Format as a single context line with sanitization."""
        safe_title = self.title[:300].replace("\n", " ").strip()
        parts = [f"- {safe_title}"]
        if self.publication_year:
            parts.append(f"({self.publication_year})")
        if self.doi:
            parts.append(f"[DOI: {self.doi[:100]}]")
        if self.cited_by_count is not None:
            parts.append(f"[{self.cited_by_count} citations]")
        return " ".join(parts)


@dataclass
class CitationGraph:
    """Citation graph data for a paper."""

    references: list[CitationPaper] = field(default_factory=list)
    citing_papers: list[CitationPaper] = field(default_factory=list)
    total_references: int = 0
    total_citing: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.references and not self.citing_papers


async def fetch_citation_graph(
    paper_doi: str | None = None,
    paper_openalex_id: str | None = None,
    raw_metadata: dict | None = None,
) -> CitationGraph:
    """Fetch citation graph data from OpenAlex.

    Retrieves both referenced works (what this paper cites) and
    citing papers (what cites this paper).

    Args:
        paper_doi: Paper DOI for API lookups.
        paper_openalex_id: OpenAlex work ID (e.g., full URL).
        raw_metadata: Stored raw_metadata from OpenAlex ingestion.

    Returns:
        CitationGraph with references and citing papers.
        Gracefully returns empty CitationGraph on any failure.
    """
    graph = CitationGraph()

    if not paper_doi and not paper_openalex_id:
        return graph

    openalex_id = paper_openalex_id
    if not openalex_id and paper_doi:
        openalex_id = await _resolve_openalex_id(paper_doi)

    # Phase 1: Get referenced works from stored raw_metadata
    referenced_work_ids = _extract_reference_ids(raw_metadata)
    if referenced_work_ids:
        graph.total_references = len(referenced_work_ids)
        graph.references = await _fetch_works_batch(
            referenced_work_ids[:MAX_REFERENCES]
        )

    # Phase 2: Get citing papers via live API
    if openalex_id:
        citing_papers, total_citing = await _fetch_citing_papers(openalex_id)
        graph.citing_papers = citing_papers
        graph.total_citing = total_citing

    return graph


def _extract_reference_ids(raw_metadata: dict | None) -> list[str]:
    """Extract referenced work OpenAlex IDs from stored raw_metadata."""
    if not raw_metadata:
        return []
    referenced = raw_metadata.get("referenced_works", [])
    if not isinstance(referenced, list):
        return []
    return [str(r) for r in referenced if r and isinstance(r, str)]


async def _resolve_openalex_id(doi: str) -> str | None:
    """Resolve a DOI to an OpenAlex work ID."""
    clean_doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    clean_doi = clean_doi.split("?")[0].split("#")[0]  # Strip query/fragment
    if not DOI_PATTERN.match(clean_doi):
        logger.warning("Invalid DOI format, skipping resolution: %s", doi[:100])
        return None
    url = f"{settings.OPENALEX_BASE_URL}/works/doi:{clean_doi}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, params={"mailto": settings.OPENALEX_EMAIL})
            if response.status_code == 200:
                return response.json().get("id")
    except Exception as e:
        logger.warning("Failed to resolve OpenAlex ID for DOI %s: %s", doi, e)
    return None


async def _fetch_works_batch(work_ids: list[str]) -> list[CitationPaper]:
    """Fetch minimal data for a batch of OpenAlex work IDs.

    Uses the OpenAlex filter API to batch up to 50 IDs in a single request.
    """
    if not work_ids:
        return []

    bare_ids = []
    for wid in work_ids:
        bid = wid.split("/")[-1] if "/" in wid else wid
        if OPENALEX_ID_PATTERN.match(bid):
            bare_ids.append(bid)
    if not bare_ids:
        return []

    filter_value = "|".join(f"https://openalex.org/{wid}" for wid in bare_ids)
    url = f"{settings.OPENALEX_BASE_URL}/works"
    params = {
        "filter": f"openalex:{filter_value}",
        "select": "title,doi,publication_year,cited_by_count",
        "per_page": len(bare_ids),
        "mailto": settings.OPENALEX_EMAIL,
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            return [_work_to_citation_paper(w) for w in results]
    except Exception as e:
        logger.warning("Failed to fetch reference works batch: %s", e)
        return []


async def _fetch_citing_papers(
    openalex_id: str,
    limit: int = MAX_CITING_PAPERS,
) -> tuple[list[CitationPaper], int]:
    """Fetch papers that cite the given work, sorted by citation count."""
    if not openalex_id.startswith("https://"):
        openalex_id = f"https://openalex.org/{openalex_id}"

    url = f"{settings.OPENALEX_BASE_URL}/works"
    params = {
        "filter": f"cites:{openalex_id}",
        "select": "title,doi,publication_year,cited_by_count",
        "sort": "cited_by_count:desc",
        "per_page": limit,
        "mailto": settings.OPENALEX_EMAIL,
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            total = (data.get("meta") or {}).get("count", 0)
            results = data.get("results", [])
            return [_work_to_citation_paper(w) for w in results], total
    except Exception as e:
        logger.warning("Failed to fetch citing papers for %s: %s", openalex_id, e)
        return [], 0


def _work_to_citation_paper(work: dict) -> CitationPaper:
    """Convert an OpenAlex work dict to CitationPaper."""
    doi = work.get("doi")
    if doi:
        doi = doi.replace("https://doi.org/", "")
    return CitationPaper(
        title=work.get("title") or "Untitled",
        doi=doi,
        publication_year=work.get("publication_year"),
        cited_by_count=work.get("cited_by_count"),
    )
