"""Source connector implementations for ingestion pipeline."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from paper_scraper.modules.ingestion.interfaces import ConnectorBatch, SourceConnector
from paper_scraper.modules.papers.clients.arxiv import ArxivClient
from paper_scraper.modules.papers.clients.crossref import CrossrefClient
from paper_scraper.modules.papers.clients.epo_ops import EPOOPSClient
from paper_scraper.modules.papers.clients.lens import LensClient
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.clients.pubmed import PubMedClient
from paper_scraper.modules.papers.clients.semantic_scholar import SemanticScholarClient
from paper_scraper.modules.papers.clients.uspto import USPTOClient


def _require_query(filters: dict[str, Any] | None) -> str:
    query = (filters or {}).get("query")
    if not query:
        raise ValueError("filters.query is required for connector fetch")
    return str(query)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class OpenAlexSourceConnector(SourceConnector):
    """OpenAlex connector with cursor-based pagination."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        batch_cursor = (cursor or {}).get("cursor") or "*"
        per_page = min(max(limit, 1), 200)

        params: dict[str, Any] = {
            "search": query,
            "per_page": per_page,
            "cursor": batch_cursor,
        }

        source_filters = (filters or {}).get("filters")
        if isinstance(source_filters, dict) and source_filters:
            params["filter"] = ",".join(f"{k}:{v}" for k, v in source_filters.items())

        async with OpenAlexClient() as client:
            params["mailto"] = client.email
            response = await client.client.get(f"{client.base_url}/works", params=params)
            response.raise_for_status()
            payload = response.json()
            raw_records = payload.get("results", [])
            records = [client.normalize(item) for item in raw_records]
            next_cursor = (payload.get("meta") or {}).get("next_cursor")

        cursor_after = {"cursor": next_cursor or batch_cursor}
        return ConnectorBatch(
            records=records,
            cursor_before={"cursor": batch_cursor},
            cursor_after=cursor_after,
            has_more=bool(next_cursor and records),
        )


class CrossrefSourceConnector(SourceConnector):
    """Crossref connector with offset pagination."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        offset = _as_int((cursor or {}).get("offset"), 0)
        rows = min(max(limit, 1), 1000)

        params: dict[str, Any] = {
            "query": query,
            "rows": rows,
            "offset": offset,
        }

        source_filters = (filters or {}).get("filters")
        if isinstance(source_filters, dict) and source_filters:
            params["filter"] = ",".join(f"{k}:{v}" for k, v in source_filters.items())

        async with CrossrefClient() as client:
            params["mailto"] = client.email
            response = await client.client.get(f"{client.base_url}/works", params=params)
            response.raise_for_status()
            payload = response.json().get("message", {})
            raw_items = payload.get("items", [])
            records = [client.normalize(item) for item in raw_items]
            total_results = _as_int(payload.get("total-results"), 0)

        next_offset = offset + len(records)
        has_more = bool(records and next_offset < total_results)
        return ConnectorBatch(
            records=records,
            cursor_before={"offset": offset},
            cursor_after={"offset": next_offset},
            has_more=has_more,
        )


class ArxivSourceConnector(SourceConnector):
    """arXiv connector with start-based pagination."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        start = _as_int((cursor or {}).get("start"), 0)
        max_results = min(max(limit, 1), 2000)
        category = (filters or {}).get("category")

        search_query = query
        if category:
            search_query = f"cat:{category} AND all:{query}"

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        async with ArxivClient() as client:
            await client._rate_limit()  # noqa: SLF001
            response = await client.client.get(f"{client.base_url}/query", params=params)
            response.raise_for_status()
            records = client._parse_arxiv_xml(response.text)  # noqa: SLF001
            root = ET.fromstring(response.text)

        total_results = _as_int(
            root.findtext("{http://a9.com/-/spec/opensearch/1.1/}totalResults"),
            0,
        )
        next_start = start + len(records)
        has_more = bool(records and next_start < total_results)
        return ConnectorBatch(
            records=records,
            cursor_before={"start": start},
            cursor_after={"start": next_start},
            has_more=has_more,
        )


class PubMedSourceConnector(SourceConnector):
    """PubMed connector with retstart pagination."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        retstart = _as_int((cursor or {}).get("retstart"), 0)
        retmax = min(max(limit, 1), 1000)

        async with PubMedClient() as client:
            search_params: dict[str, Any] = {
                "db": "pubmed",
                "term": query,
                "retstart": retstart,
                "retmax": retmax,
                "retmode": "json",
            }
            if client.api_key:
                search_params["api_key"] = client.api_key

            search_response = await client.client.get(
                f"{client.base_url}/esearch.fcgi",
                params=search_params,
            )
            search_response.raise_for_status()
            search_payload = search_response.json().get("esearchresult", {})
            pmids = search_payload.get("idlist", [])
            total_results = _as_int(search_payload.get("count"), 0)

            records: list[dict[str, Any]] = []
            if pmids:
                fetch_params: dict[str, Any] = {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "rettype": "xml",
                    "retmode": "xml",
                }
                if client.api_key:
                    fetch_params["api_key"] = client.api_key

                fetch_response = await client.client.get(
                    f"{client.base_url}/efetch.fcgi",
                    params=fetch_params,
                )
                fetch_response.raise_for_status()
                records = client._parse_pubmed_xml(fetch_response.text)  # noqa: SLF001

        next_retstart = retstart + len(pmids)
        has_more = bool(pmids and next_retstart < total_results)
        return ConnectorBatch(
            records=records,
            cursor_before={"retstart": retstart},
            cursor_after={"retstart": next_retstart},
            has_more=has_more,
        )


class SemanticScholarSourceConnector(SourceConnector):
    """Semantic Scholar connector with offset pagination."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        offset = _as_int((cursor or {}).get("offset"), 0)
        request_limit = min(max(limit, 1), 100)

        params: dict[str, Any] = {
            "query": query,
            "offset": offset,
            "limit": request_limit,
            "fields": (
                "paperId,externalIds,title,abstract,year,venue,publicationDate,journal,"
                "referenceCount,citationCount,fieldsOfStudy,authors"
            ),
        }

        year = (filters or {}).get("year")
        if year:
            params["year"] = year

        fields_of_study = (filters or {}).get("fields_of_study")
        if isinstance(fields_of_study, list) and fields_of_study:
            params["fieldsOfStudy"] = ",".join(str(item) for item in fields_of_study)

        async with SemanticScholarClient() as client:
            response = await client.client.get(
                f"{client.base_url}/paper/search",
                params=params,
                headers=client._headers(),  # noqa: SLF001
            )
            response.raise_for_status()
            payload = response.json()
            raw_records = payload.get("data", [])
            records = [client.normalize(item) for item in raw_records if item]
            total_results = _as_int(payload.get("total"), 0)

        next_offset = offset + len(records)
        has_more = bool(records and next_offset < total_results)
        return ConnectorBatch(
            records=records,
            cursor_before={"offset": offset},
            cursor_after={"offset": next_offset},
            has_more=has_more,
        )


class LensSourceConnector(SourceConnector):
    """Lens.org connector with offset pagination for patent data."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        offset = _as_int((cursor or {}).get("offset"), 0)
        per_page = min(max(limit, 1), 1000)

        async with LensClient() as client:
            response = await client.search_patents(
                query=query,
                max_results=per_page,
                offset=offset,
            )
            raw_records = response.get("data", [])
            records = [client.normalize_patent(r) for r in raw_records]
            total_results = _as_int(response.get("total"), 0)

        next_offset = offset + len(records)
        has_more = bool(records and next_offset < total_results)
        return ConnectorBatch(
            records=records,
            cursor_before={"offset": offset},
            cursor_after={"offset": next_offset},
            has_more=has_more,
        )


class EPOSourceConnector(SourceConnector):
    """EPO OPS connector with range-based pagination for patent data."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        start = _as_int((cursor or {}).get("start"), 1)
        per_page = min(max(limit, 1), 100)

        async with EPOOPSClient() as client:
            patents = await client.search_patents(
                query=query,
                max_results=per_page,
            )

        # EPO client returns pre-parsed patent dicts; normalize to pipeline format
        records = [
            {
                "source": "epo",
                "source_id": p.get("patent_number"),
                "doi": None,
                "title": p.get("title", "Untitled"),
                "abstract": p.get("abstract"),
                "publication_date": p.get("publication_date"),
                "journal": None,
                "keywords": [],
                "authors": (
                    [{"name": p["applicant"], "orcid": None, "affiliations": []}]
                    if p.get("applicant")
                    else []
                ),
                "citations_count": None,
                "raw_metadata": {
                    "patent_number": p.get("patent_number"),
                    "filing_date": p.get("filing_date"),
                    "espacenet_url": p.get("espacenet_url"),
                    "paper_type": "patent",
                },
            }
            for p in patents
        ]

        next_start = start + len(records)
        has_more = len(records) >= per_page
        return ConnectorBatch(
            records=records,
            cursor_before={"start": start},
            cursor_after={"start": next_start},
            has_more=has_more,
        )


class USPTOSourceConnector(SourceConnector):
    """USPTO PatentsView connector with offset pagination."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch:
        query = _require_query(filters)
        offset = _as_int((cursor or {}).get("offset"), 0)
        per_page = min(max(limit, 1), 1000)

        async with USPTOClient() as client:
            response = await client.search_patents(
                query=query,
                max_results=per_page,
                offset=offset,
            )
            raw_records = response.get("patents", []) or []
            records = [client.normalize(r) for r in raw_records]
            total_results = _as_int(response.get("total_patent_count"), 0)

        next_offset = offset + len(records)
        has_more = bool(records and next_offset < total_results)
        return ConnectorBatch(
            records=records,
            cursor_before={"offset": offset},
            cursor_after={"offset": next_offset},
            has_more=has_more,
        )


def get_source_connector(source: str) -> SourceConnector:
    """Return a source connector for a known source key."""
    registry: dict[str, SourceConnector] = {
        "openalex": OpenAlexSourceConnector(),
        "crossref": CrossrefSourceConnector(),
        "arxiv": ArxivSourceConnector(),
        "pubmed": PubMedSourceConnector(),
        "semantic_scholar": SemanticScholarSourceConnector(),
        "lens": LensSourceConnector(),
        "epo": EPOSourceConnector(),
        "uspto": USPTOSourceConnector(),
    }
    connector = registry.get(source)
    if connector is None:
        raise ValueError(f"Unsupported source connector: {source}")
    return connector
