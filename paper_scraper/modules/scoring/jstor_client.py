"""JSTOR content search via Crossref API (DOI prefix 10.2307).

JSTOR does not provide a free public API. This module searches JSTOR
content through the Crossref REST API by filtering on the JSTOR DOI
prefix ``10.2307``, which covers ~3.4M scholarly works.

The results are used as additional context in the scoring pipeline to
produce more nuanced assessments that account for the broader JSTOR
scholarly library.
"""

import logging
import re
from dataclasses import dataclass, field

import httpx

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)

JSTOR_DOI_PREFIX = "10.2307"
MAX_JSTOR_RESULTS = 10
REQUEST_TIMEOUT = 15.0


@dataclass
class JstorPaper:
    """Minimal paper representation from JSTOR (via Crossref)."""

    title: str
    authors: str = ""
    year: int | None = None
    doi: str | None = None
    journal: str | None = None
    abstract: str | None = None
    citation_count: int | None = None
    jstor_url: str | None = None

    def to_context_line(self) -> str:
        """Format as a single context line for LLM prompts."""
        safe_title = self.title[:300].replace("\n", " ").strip()
        parts = [f"- {safe_title}"]
        if self.year:
            parts.append(f"({self.year})")
        if self.journal:
            safe_journal = self.journal[:100].replace("\n", " ").strip()
            parts.append(f"[{safe_journal}]")
        if self.doi:
            parts.append(f"[DOI: {self.doi[:100]}]")
        if self.citation_count is not None:
            parts.append(f"[{self.citation_count} citations]")
        return " ".join(parts)


@dataclass
class JstorSearchResult:
    """Container for JSTOR search results."""

    papers: list[JstorPaper] = field(default_factory=list)
    total_results: int = 0
    query_used: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.papers


async def search_jstor(
    query: str,
    max_results: int = MAX_JSTOR_RESULTS,
) -> JstorSearchResult:
    """Search JSTOR content via Crossref prefix API.

    Uses ``GET /prefixes/10.2307/works`` to find JSTOR-published works
    matching the query. Gracefully returns an empty result on any failure.

    Args:
        query: Free-text search query (paper title + keywords).
        max_results: Maximum number of results to return.

    Returns:
        JstorSearchResult with matching papers.
    """
    if not query or not query.strip():
        return JstorSearchResult(query_used=query)

    clean_query = query.strip()[:500]
    url = f"{settings.CROSSREF_BASE_URL}/prefixes/{JSTOR_DOI_PREFIX}/works"
    params = {
        "query": clean_query,
        "rows": min(max_results, 50),
        "mailto": settings.CROSSREF_EMAIL,
        "select": "DOI,title,author,container-title,published-print,published-online,is-referenced-by-count,abstract",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
        logger.warning("JSTOR/Crossref search failed: %s", e)
        return JstorSearchResult(query_used=clean_query, errors=[str(e)])
    except ValueError as e:
        logger.warning("JSTOR/Crossref returned invalid JSON: %s", e)
        return JstorSearchResult(query_used=clean_query, errors=[str(e)])

    message = data.get("message", {})
    total = message.get("total-results", 0)
    items = message.get("items", [])

    papers = [_crossref_item_to_jstor_paper(item) for item in items]

    return JstorSearchResult(
        papers=papers,
        total_results=total,
        query_used=clean_query,
    )


def build_jstor_query(title: str, keywords: list[str] | None = None) -> str:
    """Build a search query from paper title and keywords.

    Args:
        title: Paper title (truncated to first 100 chars).
        keywords: Optional list of keywords (top 3 used).

    Returns:
        Combined search query string.
    """
    parts = [title[:100]]
    if keywords:
        parts.extend(kw[:50] for kw in keywords[:3])
    return " ".join(parts)


def _crossref_item_to_jstor_paper(item: dict) -> JstorPaper:
    """Convert a Crossref work dict to JstorPaper."""
    # Title
    title = item.get("title", ["Untitled"])
    if isinstance(title, list):
        title = title[0] if title else "Untitled"

    # Authors
    authors_list = item.get("author", [])
    author_names = []
    for author in authors_list[:5]:
        name = f"{author.get('given', '')} {author.get('family', '')}".strip()
        if name:
            author_names.append(name)
    authors = ", ".join(author_names)

    # Publication year
    year = _extract_year(item)

    # DOI
    doi = item.get("DOI")

    # Journal
    journal = item.get("container-title", [""])
    if isinstance(journal, list):
        journal = journal[0] if journal else None

    # Abstract (often sparse for JSTOR content)
    abstract = item.get("abstract")
    if abstract:
        # Strip all JATS XML / HTML tags from Crossref abstracts
        abstract = re.sub(r"<[^>]+>", "", abstract)
        abstract = abstract[:500]

    # Citation count
    citation_count = item.get("is-referenced-by-count")

    # JSTOR URL
    jstor_url = None
    if doi and doi.startswith(JSTOR_DOI_PREFIX):
        jstor_id = doi.replace(f"{JSTOR_DOI_PREFIX}/", "")
        jstor_url = f"https://www.jstor.org/stable/{jstor_id}"

    return JstorPaper(
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        journal=journal,
        abstract=abstract,
        citation_count=citation_count,
        jstor_url=jstor_url,
    )


def _extract_year(item: dict) -> int | None:
    """Extract publication year from Crossref item."""
    for date_field in ("published-print", "published-online", "created"):
        date_parts = item.get(date_field, {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            try:
                return int(date_parts[0][0])
            except (ValueError, IndexError):
                continue
    return None
