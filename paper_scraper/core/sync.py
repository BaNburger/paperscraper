"""Sync service for dual-write orchestration to Qdrant and Typesense.

PostgreSQL remains the source of truth. Qdrant and Typesense are
eventually consistent read-optimized layers.

Usage:
    sync = SyncService()
    await sync.sync_paper(paper, embedding=embedding_vector)
    await sync.sync_author(author, embedding=embedding_vector)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from paper_scraper.core.search_engine import SearchEngineService
from paper_scraper.core.vector import VectorService

logger = logging.getLogger(__name__)


class SyncService:
    """Orchestrates sync of entities from PostgreSQL to Qdrant + Typesense.

    Failures in external services are logged but do not raise — PostgreSQL
    writes always succeed independently.
    """

    def __init__(
        self,
        vector_service: VectorService | None = None,
        search_service: SearchEngineService | None = None,
    ) -> None:
        self.vector = vector_service or VectorService()
        self.search = search_service or SearchEngineService()

    # =========================================================================
    # Paper Sync
    # =========================================================================

    async def sync_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
        title: str,
        abstract: str | None = None,
        doi: str | None = None,
        source: str | None = None,
        journal: str | None = None,
        paper_type: str | None = None,
        keywords: list[str] | None = None,
        overall_score: float | None = None,
        citations_count: int | None = None,
        publication_date: datetime | None = None,
        created_at: datetime | None = None,
        embedding: list[float] | None = None,
    ) -> None:
        """Sync a paper to both Qdrant (vector) and Typesense (search).

        Args:
            paper_id: Paper UUID
            organization_id: Tenant ID
            title: Paper title
            abstract: Paper abstract
            embedding: 1536d embedding vector (if available)
            **kwargs: Additional paper metadata
        """
        # Sync to Qdrant (vector search) — only if embedding exists
        if embedding is not None:
            await self._sync_paper_vector(
                paper_id=paper_id,
                organization_id=organization_id,
                embedding=embedding,
                doi=doi,
                source=source,
                created_at=created_at,
            )

        # Sync to Typesense (full-text search)
        self._sync_paper_search(
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
            has_embedding=embedding is not None,
            publication_date=publication_date,
            created_at=created_at,
        )

    async def _sync_paper_vector(
        self,
        paper_id: UUID,
        organization_id: UUID,
        embedding: list[float],
        doi: str | None = None,
        source: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Sync paper embedding to Qdrant."""
        try:
            payload: dict[str, Any] = {
                "organization_id": str(organization_id),
                "paper_id": str(paper_id),
            }
            if doi:
                payload["doi"] = doi
            if source:
                payload["source"] = source
            if created_at:
                payload["created_at"] = int(created_at.timestamp())

            await self.vector.upsert(
                collection="papers",
                point_id=paper_id,
                vector=embedding,
                payload=payload,
            )
        except Exception:
            logger.exception("Failed to sync paper %s to Qdrant", paper_id)

    def _sync_paper_search(
        self,
        paper_id: UUID,
        organization_id: UUID,
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
        publication_date: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Sync paper to Typesense search index."""
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
                publication_date=publication_date,
                created_at=created_at,
            )
            self.search.index_paper(doc)
        except Exception:
            logger.exception("Failed to sync paper %s to Typesense", paper_id)

    # =========================================================================
    # Author Sync
    # =========================================================================

    async def sync_author(
        self,
        author_id: UUID,
        organization_id: UUID,
        embedding: list[float],
        name: str | None = None,
        orcid: str | None = None,
    ) -> None:
        """Sync author embedding to Qdrant."""
        try:
            payload: dict[str, Any] = {
                "organization_id": str(organization_id),
                "author_id": str(author_id),
            }
            if name:
                payload["name"] = name
            if orcid:
                payload["orcid"] = orcid

            await self.vector.upsert(
                collection="authors",
                point_id=author_id,
                vector=embedding,
                payload=payload,
            )
        except Exception:
            logger.exception("Failed to sync author %s to Qdrant", author_id)

    # =========================================================================
    # Cluster Sync
    # =========================================================================

    async def sync_cluster(
        self,
        cluster_id: UUID,
        organization_id: UUID,
        project_id: UUID,
        centroid: list[float],
    ) -> None:
        """Sync project cluster centroid to Qdrant."""
        try:
            await self.vector.upsert(
                collection="clusters",
                point_id=cluster_id,
                vector=centroid,
                payload={
                    "organization_id": str(organization_id),
                    "project_id": str(project_id),
                    "cluster_id": str(cluster_id),
                },
            )
        except Exception:
            logger.exception("Failed to sync cluster %s to Qdrant", cluster_id)

    # =========================================================================
    # Trend Sync
    # =========================================================================

    async def sync_trend(
        self,
        trend_id: UUID,
        organization_id: UUID,
        embedding: list[float],
        name: str | None = None,
    ) -> None:
        """Sync trend topic embedding to Qdrant."""
        try:
            payload: dict[str, Any] = {
                "organization_id": str(organization_id),
                "trend_id": str(trend_id),
            }
            if name:
                payload["name"] = name

            await self.vector.upsert(
                collection="trends",
                point_id=trend_id,
                vector=embedding,
                payload=payload,
            )
        except Exception:
            logger.exception("Failed to sync trend %s to Qdrant", trend_id)

    # =========================================================================
    # Saved Search Sync
    # =========================================================================

    async def sync_saved_search(
        self,
        search_id: UUID,
        organization_id: UUID,
        embedding: list[float],
    ) -> None:
        """Sync saved search embedding to Qdrant."""
        try:
            await self.vector.upsert(
                collection="searches",
                point_id=search_id,
                vector=embedding,
                payload={
                    "organization_id": str(organization_id),
                    "search_id": str(search_id),
                },
            )
        except Exception:
            logger.exception("Failed to sync saved search %s to Qdrant", search_id)

    # =========================================================================
    # Delete Operations
    # =========================================================================

    async def delete_paper(self, paper_id: UUID) -> None:
        """Remove paper from both Qdrant and Typesense."""
        try:
            await self.vector.delete("papers", paper_id)
        except Exception:
            logger.exception("Failed to delete paper %s from Qdrant", paper_id)

        try:
            self.search.delete_paper(str(paper_id))
        except Exception:
            logger.exception("Failed to delete paper %s from Typesense", paper_id)

    async def delete_author(self, author_id: UUID) -> None:
        """Remove author from Qdrant."""
        try:
            await self.vector.delete("authors", author_id)
        except Exception:
            logger.exception("Failed to delete author %s from Qdrant", author_id)

    async def delete_org_data(self, organization_id: UUID) -> None:
        """Remove all data for an organization from external services."""
        for collection in ["papers", "authors", "clusters", "searches", "trends"]:
            try:
                await self.vector.delete_by_org(collection, organization_id)
            except Exception:
                logger.exception(
                    "Failed to delete org %s data from Qdrant %s",
                    organization_id,
                    collection,
                )

        try:
            self.search.delete_papers_by_org(organization_id)
        except Exception:
            logger.exception(
                "Failed to delete org %s papers from Typesense",
                organization_id,
            )

    # =========================================================================
    # Bulk Sync (Reindex)
    # =========================================================================

    async def bulk_sync_papers(
        self,
        papers: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> dict[str, int]:
        """Bulk sync papers to both Qdrant and Typesense.

        Args:
            papers: List of dicts with paper data including optional 'embedding'
            batch_size: Items per batch

        Returns:
            Dict with counts: vectors_synced, documents_synced, errors
        """
        vectors_synced = 0
        documents_synced = 0
        errors = 0

        # Prepare Qdrant points (only papers with embeddings)
        vector_points = []
        # Prepare Typesense documents
        search_docs = []

        for p in papers:
            paper_id = p["paper_id"]
            org_id = p["organization_id"]

            # Typesense document
            doc = SearchEngineService.paper_to_document(
                paper_id=paper_id,
                organization_id=org_id,
                title=p["title"],
                abstract=p.get("abstract"),
                doi=p.get("doi"),
                source=p.get("source"),
                journal=p.get("journal"),
                paper_type=p.get("paper_type"),
                keywords=p.get("keywords"),
                overall_score=p.get("overall_score"),
                citations_count=p.get("citations_count"),
                has_embedding=p.get("embedding") is not None,
                publication_date=p.get("publication_date"),
                created_at=p.get("created_at"),
            )
            search_docs.append(doc)

            # Qdrant point (only if embedding exists)
            if p.get("embedding"):
                vector_points.append(
                    {
                        "id": paper_id,
                        "vector": p["embedding"],
                        "payload": {
                            "organization_id": str(org_id),
                            "paper_id": str(paper_id),
                            "doi": p.get("doi"),
                            "source": p.get("source"),
                        },
                    }
                )

        # Batch upsert to Qdrant
        if vector_points:
            try:
                vectors_synced = await self.vector.upsert_batch(
                    "papers", vector_points, batch_size=batch_size
                )
            except Exception:
                logger.exception("Failed to bulk sync papers to Qdrant")
                errors += len(vector_points)

        # Batch import to Typesense
        if search_docs:
            try:
                results = self.search.index_papers_batch(search_docs)
                documents_synced = sum(
                    1 for r in results if isinstance(r, dict) and r.get("success", True)
                )
                errors += len(search_docs) - documents_synced
            except Exception:
                logger.exception("Failed to bulk sync papers to Typesense")
                errors += len(search_docs)

        return {
            "vectors_synced": vectors_synced,
            "documents_synced": documents_synced,
            "errors": errors,
        }
