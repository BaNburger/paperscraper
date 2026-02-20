"""Typesense full-text search engine client.

Replaces PostgreSQL trigram/ILIKE search with Typesense for:
- BM25 relevance ranking
- Typo tolerance
- Faceted filtering (source, paper_type, keywords)
- Instant search (<10ms p99)

Collection: papers — indexed with title, abstract, keywords, and metadata.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import typesense

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)

# Singleton client
_client: typesense.Client | None = None

# Schema version — bump when schema changes require reindex
SCHEMA_VERSION = 1

PAPERS_SCHEMA: dict[str, Any] = {
    "fields": [
        {"name": "paper_id", "type": "string"},
        {"name": "organization_id", "type": "string", "optional": True, "facet": True},
        {"name": "title", "type": "string"},
        {"name": "abstract", "type": "string", "optional": True},
        {"name": "doi", "type": "string", "optional": True},
        {"name": "source", "type": "string", "facet": True},
        {"name": "journal", "type": "string", "optional": True, "facet": True},
        {"name": "paper_type", "type": "string", "optional": True, "facet": True},
        {"name": "keywords", "type": "string[]", "optional": True, "facet": True},
        {"name": "overall_score", "type": "float", "optional": True},
        {"name": "citations_count", "type": "int32", "optional": True},
        {"name": "has_embedding", "type": "bool", "optional": True},
        {"name": "is_global", "type": "bool", "optional": True, "facet": True},
        {"name": "publication_date", "type": "int64", "optional": True},
        {"name": "created_at", "type": "int64"},
    ],
    "default_sorting_field": "created_at",
    "enable_nested_fields": False,
}


def get_typesense_client() -> typesense.Client:
    """Get or create the Typesense client singleton."""
    global _client
    if _client is None:
        # Parse URL to extract host, port, protocol
        url = settings.TYPESENSE_URL
        protocol = "https" if url.startswith("https") else "http"
        # Strip protocol prefix
        host_port = url.replace("https://", "").replace("http://", "")
        # Split host and port
        parts = host_port.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else (443 if protocol == "https" else 80)

        _client = typesense.Client(
            {
                "api_key": settings.TYPESENSE_API_KEY.get_secret_value(),
                "nodes": [
                    {
                        "host": host,
                        "port": str(port),
                        "protocol": protocol,
                    }
                ],
                "connection_timeout_seconds": 10,
            }
        )
    return _client


def _collection_name(name: str) -> str:
    """Get the full collection name with optional prefix."""
    return f"{settings.TYPESENSE_COLLECTION_PREFIX}{name}"


def _datetime_to_epoch(dt: datetime | None) -> int | None:
    """Convert datetime to epoch seconds for Typesense int64 fields."""
    if dt is None:
        return None
    return int(dt.timestamp())


class SearchEngineService:
    """High-level full-text search operations backed by Typesense.

    Provides tenant-isolated search with BM25 ranking, typo tolerance,
    and faceted filtering.
    """

    def __init__(self, client: typesense.Client | None = None) -> None:
        self._client = client or get_typesense_client()

    # =========================================================================
    # Collection Management
    # =========================================================================

    async def ensure_collections(self) -> None:
        """Create collections if they don't exist.

        Note: Typesense client is synchronous. This method wraps sync calls
        for consistency with the async interface.
        """
        self._ensure_collection_sync("papers", PAPERS_SCHEMA)

    def _ensure_collection_sync(self, name: str, schema: dict[str, Any]) -> None:
        """Synchronously ensure a collection exists."""
        full_name = _collection_name(name)
        try:
            self._client.collections[full_name].retrieve()
            logger.debug("Typesense collection %s already exists", full_name)
        except typesense.exceptions.ObjectNotFound:
            create_schema = {
                "name": full_name,
                **schema,
            }
            self._client.collections.create(create_schema)
            logger.info("Created Typesense collection: %s", full_name)

    async def delete_collections(self) -> None:
        """Delete all managed collections. Used in testing."""
        for name in ["papers"]:
            full_name = _collection_name(name)
            try:
                self._client.collections[full_name].delete()
            except Exception:
                pass

    # =========================================================================
    # Indexing
    # =========================================================================

    def index_paper(self, paper_data: dict[str, Any]) -> None:
        """Index or update a single paper document.

        Args:
            paper_data: Paper document with fields matching PAPERS_SCHEMA
        """
        full_name = _collection_name("papers")
        self._client.collections[full_name].documents.upsert(paper_data)

    def index_papers_batch(
        self,
        papers: list[dict[str, Any]],
        action: str = "upsert",
    ) -> list[dict[str, Any]]:
        """Batch index papers.

        Args:
            papers: List of paper documents
            action: Import action (create, upsert, update)

        Returns:
            List of import results (one per document)
        """
        if not papers:
            return []

        full_name = _collection_name("papers")
        results = self._client.collections[full_name].documents.import_(papers, {"action": action})
        return results

    def delete_paper(self, paper_id: str) -> None:
        """Delete a paper from the search index."""
        full_name = _collection_name("papers")
        try:
            self._client.collections[full_name].documents[paper_id].delete()
        except typesense.exceptions.ObjectNotFound:
            pass

    def delete_papers_by_org(self, organization_id: UUID) -> int:
        """Delete all papers for an organization from the search index.

        Returns:
            Number of documents deleted
        """
        full_name = _collection_name("papers")
        result = self._client.collections[full_name].documents.delete(
            {"filter_by": f"organization_id:={organization_id}"}
        )
        return result.get("num_deleted", 0)

    # =========================================================================
    # Search
    # =========================================================================

    def search_papers(
        self,
        query: str,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        filter_by: str | None = None,
        sort_by: str | None = None,
        facet_by: str | None = None,
        scope: str = "library",
    ) -> dict[str, Any]:
        """Full-text search for papers.

        Args:
            query: Search query text
            organization_id: Tenant isolation filter (used when scope='library')
            page: Page number (1-indexed)
            page_size: Results per page
            filter_by: Additional Typesense filter expression
            sort_by: Sort expression (e.g., "created_at:desc")
            facet_by: Facet fields (e.g., "source,paper_type")
            scope: 'library' for org-scoped search, 'catalog' for global

        Returns:
            Typesense search result with hits, found count, facets, etc.
        """
        full_name = _collection_name("papers")

        # Build filter based on scope
        if scope == "catalog":
            filters = ["is_global:=true"]
        else:
            filters = [f"organization_id:={organization_id}"]
        if filter_by:
            filters.append(filter_by)
        filter_str = " && ".join(filters)

        search_params: dict[str, Any] = {
            "q": query,
            "query_by": "title,abstract,keywords",
            "query_by_weights": "3,1,2",
            "filter_by": filter_str,
            "per_page": page_size,
            "page": page,
            "highlight_full_fields": "title,abstract",
            "highlight_start_tag": "<mark>",
            "highlight_end_tag": "</mark>",
            "num_typos": 2,
            "typo_tokens_threshold": 3,
        }

        if sort_by:
            search_params["sort_by"] = sort_by
        if facet_by:
            search_params["facet_by"] = facet_by

        return self._client.collections[full_name].documents.search(search_params)

    def multi_search(
        self,
        searches: list[dict[str, Any]],
        organization_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Execute multiple searches in a single request.

        Args:
            searches: List of search parameter dicts
            organization_id: If provided, enforces tenant isolation on all
                sub-searches by injecting an organization_id filter.

        Returns:
            Combined results
        """
        if organization_id is not None:
            org_filter = f"organization_id:={organization_id}"
            for s in searches:
                existing = s.get("filter_by", "")
                if org_filter not in existing:
                    s["filter_by"] = (
                        f"{existing} && {org_filter}" if existing else org_filter
                    )

        return self._client.multi_search.perform(
            {"searches": searches},
            {},
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def paper_to_document(
        paper_id: UUID,
        organization_id: UUID | None,
        title: str,
        abstract: str | None = None,
        doi: str | None = None,
        source: str | None = None,
        journal: str | None = None,
        paper_type: str | None = None,
        keywords: list[str] | None = None,
        overall_score: float | None = None,
        citations_count: int | None = None,
        has_embedding: bool = False,
        is_global: bool = False,
        publication_date: datetime | None = None,
        created_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Convert paper fields to a Typesense document.

        Uses paper_id as the document ID for direct lookup.
        """
        doc: dict[str, Any] = {
            "id": str(paper_id),
            "paper_id": str(paper_id),
            "title": title,
            "created_at": _datetime_to_epoch(created_at) or 0,
        }

        if organization_id is not None:
            doc["organization_id"] = str(organization_id)
        if abstract is not None:
            doc["abstract"] = abstract
        if doi is not None:
            doc["doi"] = doi
        if source is not None:
            doc["source"] = source
        if journal is not None:
            doc["journal"] = journal
        if paper_type is not None:
            doc["paper_type"] = paper_type
        if keywords:
            doc["keywords"] = keywords
        if overall_score is not None:
            doc["overall_score"] = overall_score
        if citations_count is not None:
            doc["citations_count"] = citations_count
        if has_embedding:
            doc["has_embedding"] = has_embedding
        if is_global:
            doc["is_global"] = is_global
        if publication_date is not None:
            doc["publication_date"] = _datetime_to_epoch(publication_date)

        return doc
