"""Sync service for writing paper data to Typesense search index.

PostgreSQL is the source of truth for all data, including vector embeddings
(stored via pgvector). Typesense provides fast full-text search.

Usage:
    sync = SyncService()
    sync.sync_paper(paper_id, organization_id, title, ...)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from paper_scraper.core.search_engine import SearchEngineService

logger = logging.getLogger(__name__)

# Transient errors that may resolve on retry
_TRANSIENT_ERRORS = (ConnectionError, TimeoutError, OSError)


def _classify_sync_error(exc: Exception, service: str, entity: str, entity_id: Any) -> None:
    """Log sync errors with severity classification."""
    if isinstance(exc, _TRANSIENT_ERRORS):
        logger.warning(
            "Transient %s sync failure for %s %s: %s",
            service,
            entity,
            entity_id,
            exc,
        )
    else:
        logger.error(
            "%s sync failed for %s %s: %s",
            service,
            entity,
            entity_id,
            exc,
            exc_info=True,
        )


class SyncService:
    """Orchestrates sync of entities from PostgreSQL to Typesense.

    Failures in Typesense are logged but do not raise — PostgreSQL
    writes (including pgvector embeddings) always succeed independently.
    """

    def __init__(
        self,
        search_service: SearchEngineService | None = None,
    ) -> None:
        self.search = search_service or SearchEngineService()

    # =========================================================================
    # Paper Sync (Typesense only — embeddings handled via pgvector directly)
    # =========================================================================

    def sync_paper(
        self,
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
    ) -> None:
        """Sync a paper to the Typesense search index.

        Args:
            paper_id: Paper UUID
            organization_id: Tenant ID (None for global papers)
            title: Paper title
            is_global: Whether this is a global catalog paper
            **kwargs: Additional paper metadata
        """
        try:
            doc = SearchEngineService.paper_to_document(
                paper_id=paper_id,
                organization_id=organization_id,
                title=title,
                abstract=abstract,
                doi=doi,
                source=source,
                journal=journal,
                paper_type=paper_type,
                keywords=keywords,
                overall_score=overall_score,
                citations_count=citations_count,
                has_embedding=has_embedding,
                is_global=is_global,
                publication_date=publication_date,
                created_at=created_at,
            )
            self.search.index_paper(doc)
        except Exception as exc:
            _classify_sync_error(exc, "Typesense", "paper", paper_id)

    # =========================================================================
    # Delete Operations
    # =========================================================================

    def delete_paper(self, paper_id: UUID) -> None:
        """Remove paper from Typesense."""
        try:
            self.search.delete_paper(str(paper_id))
        except Exception as exc:
            _classify_sync_error(exc, "Typesense", "paper_delete", paper_id)

    def delete_org_data(self, organization_id: UUID) -> None:
        """Remove all data for an organization from Typesense."""
        try:
            self.search.delete_papers_by_org(organization_id)
        except Exception as exc:
            _classify_sync_error(exc, "Typesense", "org_delete", organization_id)

    # =========================================================================
    # Bulk Sync (Reindex)
    # =========================================================================

    def bulk_sync_papers(
        self,
        papers: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Bulk sync papers to Typesense.

        Embeddings are NOT synced here — they live in pgvector on the
        papers table and are updated directly via VectorService.

        Args:
            papers: List of dicts with paper data

        Returns:
            Dict with counts: documents_synced, errors
        """
        documents_synced = 0
        errors = 0

        search_docs = []
        for p in papers:
            doc = SearchEngineService.paper_to_document(
                paper_id=p["paper_id"],
                organization_id=p.get("organization_id"),
                title=p["title"],
                abstract=p.get("abstract"),
                doi=p.get("doi"),
                source=p.get("source"),
                journal=p.get("journal"),
                paper_type=p.get("paper_type"),
                keywords=p.get("keywords"),
                overall_score=p.get("overall_score"),
                citations_count=p.get("citations_count"),
                has_embedding=p.get("has_embedding", False),
                is_global=p.get("is_global", False),
                publication_date=p.get("publication_date"),
                created_at=p.get("created_at"),
            )
            search_docs.append(doc)

        if search_docs:
            try:
                results = self.search.index_papers_batch(search_docs)
                documents_synced = sum(
                    1 for r in results if isinstance(r, dict) and r.get("success", True)
                )
                errors += len(search_docs) - documents_synced
            except Exception as exc:
                _classify_sync_error(exc, "Typesense", "bulk_papers", f"{len(search_docs)} docs")
                errors += len(search_docs)

        return {
            "documents_synced": documents_synced,
            "errors": errors,
        }
