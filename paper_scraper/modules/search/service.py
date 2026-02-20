"""Service layer for search module.

Uses pgvector (PostgreSQL HNSW) for semantic search and Typesense for
full-text search. PostgreSQL is used for paper hydration and score lookups.
"""

import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.search_engine import SearchEngineService
from paper_scraper.core.vector import VectorService
from paper_scraper.modules.embeddings.service import EmbeddingService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.scoring.embeddings import EmbeddingClient
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.search.models import SearchActivity
from paper_scraper.modules.search.schemas import (
    EmbeddingBackfillResult,
    EmbeddingStats,
    ScoreSummary,
    SearchFilters,
    SearchHighlight,
    SearchMode,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchScope,
    SimilarPaperItem,
    SimilarPapersResponse,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for paper search operations.

    Uses pgvector (PostgreSQL HNSW) for semantic search and Typesense for
    full-text search. Paper metadata is hydrated from PostgreSQL after
    search backends return matching IDs.
    """

    # RRF constant (typically 60 is used)
    RRF_K = 60

    def __init__(
        self,
        db: AsyncSession,
        vector: VectorService | None = None,
        search_engine: SearchEngineService | None = None,
    ) -> None:
        self.db = db
        self.embedding_client = EmbeddingClient()
        self.embedding_service = EmbeddingService(db)
        self.vector = vector or VectorService()
        self.search_engine = search_engine or SearchEngineService()

    # =========================================================================
    # Main Search Methods
    # =========================================================================

    async def search(
        self,
        request: SearchRequest,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> SearchResponse:
        """Execute a search query based on the specified mode.

        Args:
            request: Search request with query, mode, filters.
            organization_id: Organization ID for tenant isolation.
            user_id: Optional user ID for activity tracking.

        Returns:
            SearchResponse with paginated results.
        """
        start_time = time.time()
        scope = request.scope if hasattr(request, "scope") else SearchScope.LIBRARY

        if request.mode == SearchMode.FULLTEXT:
            results, total = await self._fulltext_search(
                query=request.query,
                organization_id=organization_id,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
                include_highlights=request.include_highlights,
                scope=scope,
            )
        elif request.mode == SearchMode.SEMANTIC:
            results, total = await self._semantic_search(
                query=request.query,
                organization_id=organization_id,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
                scope=scope,
            )
        else:  # HYBRID
            results, total = await self._hybrid_search(
                query=request.query,
                organization_id=organization_id,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
                semantic_weight=request.semantic_weight,
                include_highlights=request.include_highlights,
                scope=scope,
            )

        search_time_ms = (time.time() - start_time) * 1000

        # Log search activity for gamification tracking
        if user_id is not None:
            activity = SearchActivity(
                user_id=user_id,
                organization_id=organization_id,
                query=request.query[:1000],
                mode=request.mode.value,
                results_count=total,
                search_time_ms=round(search_time_ms, 2),
            )
            self.db.add(activity)
            await self.db.flush()

        return SearchResponse(
            items=results,
            total=total,
            page=request.page,
            page_size=request.page_size,
            pages=(total + request.page_size - 1) // request.page_size if total > 0 else 0,
            query=request.query,
            mode=request.mode,
            search_time_ms=round(search_time_ms, 2),
        )

    async def find_similar_papers(
        self,
        paper_id: UUID,
        organization_id: UUID,
        limit: int = 10,
        min_similarity: float = 0.0,
        filters: SearchFilters | None = None,
    ) -> SimilarPapersResponse:
        """Find papers similar to a given paper using pgvector cosine similarity.

        Args:
            paper_id: ID of the reference paper.
            organization_id: Organization ID.
            limit: Maximum results.
            min_similarity: Minimum similarity threshold (0-1).
            filters: Optional filters.

        Returns:
            SimilarPapersResponse with similar papers.
        """
        # Verify the paper exists in PostgreSQL
        paper = await self._get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Check if the paper has an embedding
        has_vec = await self.vector.has_vector(db=self.db, paper_id=paper_id)
        if not has_vec:
            return SimilarPapersResponse(
                paper_id=paper_id,
                similar_papers=[],
                total_found=0,
            )

        # Search for similar papers via pgvector
        vector_results = await self.vector.search_by_paper_id(
            db=self.db,
            paper_id=paper_id,
            organization_id=organization_id,
            limit=limit,
            min_score=min_similarity if min_similarity > 0 else None,
        )

        if not vector_results:
            return SimilarPapersResponse(
                paper_id=paper_id,
                similar_papers=[],
                total_found=0,
            )

        # Build a map of ID -> similarity score
        score_map: dict[UUID, float] = {}
        result_ids: list[UUID] = []
        for result in vector_results:
            rid = UUID(result["id"])
            result_ids.append(rid)
            score_map[rid] = result["score"]

        # Hydrate paper metadata from PostgreSQL
        hydrated_papers = await self._hydrate_papers(result_ids, organization_id)

        # Apply PostgreSQL-side filters (score filters that need joins)
        if filters:
            filtered_ids = await self._apply_pg_score_filter(
                list(hydrated_papers.keys()), filters, organization_id
            )
            hydrated_papers = {pid: p for pid, p in hydrated_papers.items() if pid in filtered_ids}

        # Build similar paper items, preserving ranking order
        similar_papers: list[SimilarPaperItem] = []
        for rid in result_ids:
            if rid not in hydrated_papers:
                continue
            p = hydrated_papers[rid]
            similar_papers.append(
                SimilarPaperItem(
                    id=p.id,
                    title=p.title,
                    abstract=p.abstract,
                    doi=p.doi,
                    source=p.source,
                    journal=p.journal,
                    publication_date=p.publication_date,
                    keywords=p.keywords or [],
                    similarity_score=round(score_map[rid], 4),
                )
            )

        return SimilarPapersResponse(
            paper_id=paper_id,
            similar_papers=similar_papers,
            total_found=len(similar_papers),
        )

    async def semantic_search_by_text(
        self,
        query: str,
        organization_id: UUID,
        limit: int = 20,
        filters: SearchFilters | None = None,
    ) -> list[SearchResultItem]:
        """Perform semantic search by embedding the query text.

        Args:
            query: Query text to embed.
            organization_id: Organization ID.
            limit: Maximum results.
            filters: Optional filters.

        Returns:
            List of search results sorted by semantic similarity.
        """
        query_embedding = await self.embedding_client.embed_text(query)

        results, _ = await self._semantic_search(
            query=query,
            organization_id=organization_id,
            filters=filters,
            page=1,
            page_size=limit,
            query_embedding=query_embedding,
        )

        return results

    # =========================================================================
    # Embedding Backfill
    # =========================================================================

    async def count_papers_without_embeddings(
        self,
        organization_id: UUID,
    ) -> int:
        """Count papers that need embeddings generated."""
        return await self.embedding_service.count_without_embeddings(organization_id)

    async def get_embedding_stats(self, organization_id: UUID) -> EmbeddingStats:
        """Get embedding statistics for an organization."""
        stats = await self.embedding_service.get_stats(organization_id)
        return EmbeddingStats(
            total_papers=stats.total_papers,
            with_embedding=stats.with_embedding,
            without_embedding=stats.without_embedding,
            embedding_coverage=stats.embedding_coverage,
        )

    async def backfill_embeddings(
        self,
        organization_id: UUID,
        batch_size: int = 100,
        max_papers: int | None = None,
    ) -> EmbeddingBackfillResult:
        """Generate embeddings for papers that don't have them.

        Args:
            organization_id: Organization ID.
            batch_size: Papers to process per batch.
            max_papers: Maximum papers to process (None = all).

        Returns:
            EmbeddingBackfillResult with statistics.
        """
        summary = await self.embedding_service.backfill_for_organization(
            organization_id=organization_id,
            batch_size=batch_size,
            max_papers=max_papers,
        )
        return EmbeddingBackfillResult(
            papers_processed=summary.papers_processed,
            papers_succeeded=summary.papers_succeeded,
            papers_failed=summary.papers_failed,
            errors=summary.errors[:10],
        )

    # =========================================================================
    # Private Search Methods
    # =========================================================================

    async def _fulltext_search(
        self,
        query: str,
        organization_id: UUID,
        filters: SearchFilters | None,
        page: int,
        page_size: int,
        include_highlights: bool = True,
        scope: SearchScope = SearchScope.LIBRARY,
    ) -> tuple[list[SearchResultItem], int]:
        """Perform full-text search using Typesense.

        Uses Typesense BM25 ranking with typo tolerance.
        """
        # Build Typesense filter string from SearchFilters
        ts_filter = self._build_typesense_filter(filters, organization_id)

        # Execute Typesense search
        ts_result = self.search_engine.search_papers(
            query=query,
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            filter_by=ts_filter,
            scope=scope.value,
        )

        total: int = ts_result.get("found", 0)
        hits: list[dict[str, Any]] = ts_result.get("hits", [])

        if not hits:
            return [], total

        # Extract paper IDs and Typesense metadata (scores, highlights)
        ts_paper_ids: list[UUID] = []
        ts_meta: dict[UUID, dict[str, Any]] = {}
        for hit in hits:
            doc = hit.get("document", {})
            paper_id_str = doc.get("paper_id") or doc.get("id")
            if not paper_id_str:
                continue
            try:
                pid = UUID(paper_id_str)
            except (ValueError, AttributeError):
                continue
            ts_paper_ids.append(pid)
            ts_meta[pid] = {
                "text_score": hit.get("text_match_info", {}).get("score", 0),
                "highlights": hit.get("highlights", []),
                "has_embedding": doc.get("has_embedding", False),
            }

        # Hydrate paper metadata from PostgreSQL
        hydrated_papers = await self._hydrate_papers(ts_paper_ids, organization_id, scope=scope)

        # Apply PostgreSQL-side score filters
        if filters and self._needs_pg_score_filter(filters):
            filtered_ids = await self._apply_pg_score_filter(
                list(hydrated_papers.keys()), filters, organization_id
            )
            hydrated_papers = {pid: p for pid, p in hydrated_papers.items() if pid in filtered_ids}

        # Fetch scores for matched papers (scores are always org-scoped)
        scores_map = await self._get_latest_scores(list(hydrated_papers.keys()), organization_id)

        # Build result items preserving Typesense ranking order
        items: list[SearchResultItem] = []
        for pid in ts_paper_ids:
            if pid not in hydrated_papers:
                continue
            paper = hydrated_papers[pid]
            meta = ts_meta.get(pid, {})
            text_score = meta.get("text_score", 0)

            # Normalize Typesense text_match score to 0-1 range
            # Typesense scores are large integers; normalize by dividing
            normalized_score = self._normalize_typesense_score(text_score)

            highlights: list[SearchHighlight] = []
            if include_highlights:
                highlights = self._extract_typesense_highlights(meta.get("highlights", []))

            items.append(
                SearchResultItem(
                    id=paper.id,
                    title=paper.title,
                    abstract=paper.abstract,
                    doi=paper.doi,
                    source=paper.source,
                    journal=paper.journal,
                    publication_date=paper.publication_date,
                    keywords=paper.keywords or [],
                    citations_count=paper.citations_count,
                    has_embedding=meta.get("has_embedding", False),
                    created_at=paper.created_at,
                    relevance_score=round(normalized_score, 4),
                    text_score=round(normalized_score, 4),
                    semantic_score=None,
                    highlights=highlights,
                    score=scores_map.get(paper.id),
                )
            )

        return items, total

    async def _semantic_search(
        self,
        query: str,
        organization_id: UUID,
        filters: SearchFilters | None,
        page: int,
        page_size: int,
        query_embedding: list[float] | None = None,
        scope: SearchScope = SearchScope.LIBRARY,
    ) -> tuple[list[SearchResultItem], int]:
        """Perform semantic search using pgvector HNSW embeddings.

        Uses pgvector cosine similarity for ranking.
        """
        # Generate query embedding if not provided
        if query_embedding is None:
            query_embedding = await self.embedding_client.embed_text(query)

        # pgvector supports ORDER BY + LIMIT natively, so fetch page*page_size
        fetch_limit = min(page * page_size, 10_000)

        # Execute pgvector search — pass None org_id for catalog scope
        vector_org_id = organization_id if scope == SearchScope.LIBRARY else None
        vector_results = await self.vector.search_similar(
            db=self.db,
            query_vector=query_embedding,
            organization_id=vector_org_id,
            limit=fetch_limit,
        )

        total = len(vector_results)

        # Apply pagination by slicing
        start = (page - 1) * page_size
        paginated_results = vector_results[start : start + page_size]

        if not paginated_results:
            return [], total

        # Build ID -> score map
        result_ids: list[UUID] = []
        score_map: dict[UUID, float] = {}
        for result in paginated_results:
            rid = UUID(result["id"])
            result_ids.append(rid)
            score_map[rid] = result["score"]

        # Hydrate paper metadata from PostgreSQL
        hydrated_papers = await self._hydrate_papers(result_ids, organization_id, scope=scope)

        # Apply PostgreSQL-side score filters
        if filters and self._needs_pg_score_filter(filters):
            filtered_ids = await self._apply_pg_score_filter(
                list(hydrated_papers.keys()), filters, organization_id
            )
            hydrated_papers = {pid: p for pid, p in hydrated_papers.items() if pid in filtered_ids}

        # Fetch scores (scores are always org-scoped)
        scores_map = await self._get_latest_scores(list(hydrated_papers.keys()), organization_id)

        # Build results preserving ranking order
        items: list[SearchResultItem] = []
        for rid in result_ids:
            if rid not in hydrated_papers:
                continue
            paper = hydrated_papers[rid]
            similarity = score_map.get(rid, 0.0)

            items.append(
                SearchResultItem(
                    id=paper.id,
                    title=paper.title,
                    abstract=paper.abstract,
                    doi=paper.doi,
                    source=paper.source,
                    journal=paper.journal,
                    publication_date=paper.publication_date,
                    keywords=paper.keywords or [],
                    citations_count=paper.citations_count,
                    has_embedding=True,
                    created_at=paper.created_at,
                    relevance_score=round(similarity, 4),
                    text_score=None,
                    semantic_score=round(similarity, 4),
                    highlights=[],
                    score=scores_map.get(paper.id),
                )
            )

        return items, total

    async def _hybrid_search(
        self,
        query: str,
        organization_id: UUID,
        filters: SearchFilters | None,
        page: int,
        page_size: int,
        semantic_weight: float = 0.5,
        include_highlights: bool = True,
        scope: SearchScope = SearchScope.LIBRARY,
    ) -> tuple[list[SearchResultItem], int]:
        """Perform hybrid search combining Typesense and pgvector results.

        Uses Reciprocal Rank Fusion (RRF) to combine rankings:
        RRF_score = text_weight/(k + rank_text) + semantic_weight/(k + rank_semantic)
        """
        # Generate query embedding
        query_embedding = await self.embedding_client.embed_text(query)

        # Fetch more results than needed for RRF merging
        fetch_limit = page_size * 5

        # Get full-text results from Typesense
        text_results, text_total = await self._fulltext_search(
            query=query,
            organization_id=organization_id,
            filters=filters,
            page=1,
            page_size=fetch_limit,
            include_highlights=include_highlights,
            scope=scope,
        )

        # Get semantic results from pgvector
        semantic_results, semantic_total = await self._semantic_search(
            query=query,
            organization_id=organization_id,
            filters=filters,
            page=1,
            page_size=fetch_limit,
            query_embedding=query_embedding,
            scope=scope,
        )

        # Create rank mappings
        text_ranks: dict[UUID, int] = {item.id: rank + 1 for rank, item in enumerate(text_results)}
        semantic_ranks: dict[UUID, int] = {
            item.id: rank + 1 for rank, item in enumerate(semantic_results)
        }

        # Combine all unique paper IDs
        all_paper_ids = set(text_ranks.keys()) | set(semantic_ranks.keys())

        # Calculate RRF scores
        rrf_scores: dict[UUID, float] = {}
        text_weight = 1 - semantic_weight

        for paper_id in all_paper_ids:
            # Default rank for missing items is large (beyond list length)
            text_rank = text_ranks.get(paper_id, fetch_limit + 100)
            semantic_rank = semantic_ranks.get(paper_id, fetch_limit + 100)

            # RRF formula with weights
            text_rrf = text_weight * (1 / (self.RRF_K + text_rank))
            semantic_rrf = semantic_weight * (1 / (self.RRF_K + semantic_rank))
            rrf_scores[paper_id] = text_rrf + semantic_rrf

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build result items from text or semantic results
        text_items_map = {item.id: item for item in text_results}
        semantic_items_map = {item.id: item for item in semantic_results}

        # Paginate
        total = len(sorted_ids)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_ids = sorted_ids[start:end]

        items: list[SearchResultItem] = []
        for paper_id in paginated_ids:
            # Prefer text result (has highlights), fall back to semantic
            if paper_id in text_items_map:
                item = text_items_map[paper_id]
                # Add semantic score if available
                if paper_id in semantic_items_map:
                    item.semantic_score = semantic_items_map[paper_id].semantic_score
            else:
                item = semantic_items_map[paper_id]

            # Update relevance score to RRF score
            item.relevance_score = round(rrf_scores[paper_id], 4)
            items.append(item)

        return items, total

    # =========================================================================
    # Typesense Filter Builder
    # =========================================================================

    @staticmethod
    def _sanitize_typesense_value(value: str) -> str:
        """Sanitize a string value for use in Typesense filter_by expressions.

        Strips backticks and filter operators to prevent injection into
        backtick-delimited Typesense filter values.
        """
        # Remove backticks (used as delimiters) and characters that could
        # alter filter semantics
        return value.replace("`", "").replace("&&", "").replace("||", "")

    @staticmethod
    def _build_typesense_filter(
        filters: SearchFilters | None,
        organization_id: UUID,
    ) -> str | None:
        """Convert SearchFilters to a Typesense filter_by string.

        The organization_id filter is applied separately by SearchEngineService,
        so this method only builds additional filter conditions.

        Args:
            filters: Search filter criteria.
            organization_id: Tenant ID (not used here, handled by SearchEngineService).

        Returns:
            Typesense filter_by string or None if no filters.
        """
        if not filters:
            return None

        parts: list[str] = []

        # Source filter
        if filters.sources:
            source_values = ",".join(s.value for s in filters.sources)
            parts.append(f"source:[{source_values}]")

        # Date filters (Typesense stores dates as epoch int64)
        if filters.date_from:
            epoch = int(filters.date_from.timestamp())
            parts.append(f"publication_date:>={epoch}")
        if filters.date_to:
            epoch = int(filters.date_to.timestamp())
            parts.append(f"publication_date:<={epoch}")

        # Ingested date filters
        if filters.ingested_from:
            epoch = int(filters.ingested_from.timestamp())
            parts.append(f"created_at:>={epoch}")
        if filters.ingested_to:
            epoch = int(filters.ingested_to.timestamp())
            parts.append(f"created_at:<={epoch}")

        # Score filters (overall_score is indexed in Typesense)
        if filters.min_score is not None:
            parts.append(f"overall_score:>={filters.min_score}")
        if filters.max_score is not None:
            parts.append(f"overall_score:<={filters.max_score}")

        # Embedding filter
        if filters.has_embedding is True:
            parts.append("has_embedding:true")
        elif filters.has_embedding is False:
            parts.append("has_embedding:false")

        # Journal filter (sanitize to prevent filter injection)
        if filters.journals:
            escaped = ",".join(
                f"`{SearchService._sanitize_typesense_value(j)}`" for j in filters.journals
            )
            parts.append(f"journal:[{escaped}]")

        # Keyword filter (sanitize to prevent filter injection)
        if filters.keywords:
            escaped = ",".join(
                f"`{SearchService._sanitize_typesense_value(kw)}`" for kw in filters.keywords
            )
            parts.append(f"keywords:[{escaped}]")

        if not parts:
            return None

        return " && ".join(parts)

    # =========================================================================
    # PostgreSQL Filter Helpers (for score filters that need joins)
    # =========================================================================

    @staticmethod
    def _needs_pg_score_filter(filters: SearchFilters) -> bool:
        """Check if filters require PostgreSQL-side score filtering.

        has_score requires checking the PaperScore table existence which
        is not indexed in Typesense. min_score/max_score are also checked
        here for precise latest-score filtering when needed.
        """
        return filters.has_score is not None

    async def _apply_pg_score_filter(
        self,
        paper_ids: list[UUID],
        filters: SearchFilters,
        organization_id: UUID,
    ) -> set[UUID]:
        """Apply score existence filters via PostgreSQL and return matching IDs.

        Args:
            paper_ids: Paper IDs to check.
            filters: Filters containing has_score criteria.
            organization_id: Tenant ID.

        Returns:
            Set of paper IDs that pass the filter.
        """
        if not paper_ids:
            return set()

        if filters.has_score is None:
            return set(paper_ids)

        score_alias = aliased(PaperScore)

        if filters.has_score is True:
            # Return papers that HAVE at least one score
            query = select(Paper.id).where(
                Paper.id.in_(paper_ids),
                Paper.organization_id == organization_id,
                exists(
                    select(score_alias.id).where(
                        score_alias.paper_id == Paper.id,
                        score_alias.organization_id == organization_id,
                    )
                ),
            )
        else:
            # Return papers that DO NOT have any score
            query = select(Paper.id).where(
                Paper.id.in_(paper_ids),
                Paper.organization_id == organization_id,
                ~exists(
                    select(score_alias.id).where(
                        score_alias.paper_id == Paper.id,
                        score_alias.organization_id == organization_id,
                    )
                ),
            )

        result = await self.db.execute(query)
        return {row[0] for row in result.all()}

    def _apply_filters(
        self,
        query: Any,
        filters: SearchFilters | None,
        organization_id: UUID,
    ) -> Any:
        """Apply search filters to a SQLAlchemy query.

        Kept for PostgreSQL-side hydration queries that still
        need basic + score filtering (e.g., backfill operations).
        """
        if not filters:
            return query

        query = self._apply_basic_filters(query, filters)
        query = self._apply_score_filters(query, filters, organization_id)

        return query

    def _apply_basic_filters(self, query: Any, filters: SearchFilters) -> Any:
        """Apply basic paper field filters to a SQLAlchemy query."""
        if filters.sources:
            query = query.where(Paper.source.in_(filters.sources))

        if filters.date_from:
            query = query.where(Paper.publication_date >= filters.date_from)
        if filters.date_to:
            query = query.where(Paper.publication_date <= filters.date_to)
        if filters.ingested_from:
            query = query.where(Paper.created_at >= filters.ingested_from)
        if filters.ingested_to:
            query = query.where(Paper.created_at <= filters.ingested_to)

        if filters.journals:
            query = query.where(Paper.journal.in_(filters.journals))

        from sqlalchemy import or_

        if filters.keywords:
            keyword_conditions = [Paper.keywords.contains([kw]) for kw in filters.keywords]
            query = query.where(or_(*keyword_conditions))

        return query

    def _apply_score_filters(
        self,
        query: Any,
        filters: SearchFilters,
        organization_id: UUID,
    ) -> Any:
        """Apply score-related filters requiring PaperScore join."""
        needs_score_filter = (
            filters.min_score is not None
            or filters.max_score is not None
            or filters.has_score is not None
        )
        if not needs_score_filter:
            return query

        score_alias = aliased(PaperScore)

        if filters.has_score is True:
            query = query.where(
                exists(
                    select(score_alias.id).where(
                        score_alias.paper_id == Paper.id,
                        score_alias.organization_id == organization_id,
                    )
                )
            )
        elif filters.has_score is False:
            query = query.where(
                ~exists(
                    select(score_alias.id).where(
                        score_alias.paper_id == Paper.id,
                        score_alias.organization_id == organization_id,
                    )
                )
            )

        if filters.min_score is not None or filters.max_score is not None:
            latest_score_subquery = (
                select(
                    PaperScore.paper_id,
                    func.max(PaperScore.created_at).label("latest"),
                )
                .where(PaperScore.organization_id == organization_id)
                .group_by(PaperScore.paper_id)
                .subquery()
            )

            query = query.join(
                latest_score_subquery,
                Paper.id == latest_score_subquery.c.paper_id,
            ).join(
                score_alias,
                and_(
                    score_alias.paper_id == latest_score_subquery.c.paper_id,
                    score_alias.created_at == latest_score_subquery.c.latest,
                ),
            )

            if filters.min_score is not None:
                query = query.where(score_alias.overall_score >= filters.min_score)
            if filters.max_score is not None:
                query = query.where(score_alias.overall_score <= filters.max_score)

        return query

    # =========================================================================
    # Typesense Highlight Extraction
    # =========================================================================

    @staticmethod
    def _sanitize_highlight(snippet: str) -> str:
        """Strip all HTML tags except <mark> from a highlight snippet.

        Typesense wraps matched tokens with <mark>...</mark>. Any other
        HTML in the indexed content must be stripped to prevent XSS.
        """
        import html
        import re

        # Temporarily replace <mark> and </mark> with placeholders
        snippet = snippet.replace("<mark>", "\x00MARK_OPEN\x00")
        snippet = snippet.replace("</mark>", "\x00MARK_CLOSE\x00")
        # Strip all remaining HTML tags
        snippet = re.sub(r"<[^>]+>", "", snippet)
        # Escape remaining special characters for safety (html.escape
        # handles &amp; correctly without double-escaping)
        snippet = html.escape(snippet, quote=False)
        # Restore mark tags
        snippet = snippet.replace("\x00MARK_OPEN\x00", "<mark>")
        snippet = snippet.replace("\x00MARK_CLOSE\x00", "</mark>")
        return snippet

    @staticmethod
    def _extract_typesense_highlights(
        highlights: list[dict[str, Any]],
    ) -> list[SearchHighlight]:
        """Convert Typesense highlight objects to SearchHighlight schema.

        Typesense highlights have the structure:
        [{"field": "title", "snippet": "<mark>neural</mark> network...", ...}]

        Args:
            highlights: List of Typesense highlight dicts.

        Returns:
            List of SearchHighlight objects.
        """
        result: list[SearchHighlight] = []
        for hl in highlights:
            field = hl.get("field", "")
            snippet = hl.get("snippet", "")
            if not snippet:
                # Fall back to matched_tokens joined
                matched = hl.get("matched_tokens", [])
                if matched:
                    snippet = " ".join(str(t) for t in matched)
            if field and snippet:
                snippet = SearchService._sanitize_highlight(snippet)
                result.append(SearchHighlight(field=field, snippet=snippet))
        return result

    @staticmethod
    def _normalize_typesense_score(raw_score: int | float) -> float:
        """Normalize Typesense text_match score to a 0-1 range.

        Typesense text_match scores are large integers based on a bucketed
        scoring system. We apply a simple sigmoid-like normalization.

        Args:
            raw_score: Raw Typesense text_match score.

        Returns:
            Normalized score between 0 and 1.
        """
        if raw_score <= 0:
            return 0.0
        # Typesense text_match_info scores are typically in the range
        # of millions. We use log-based normalization to compress to 0-1.
        import math

        # log10(1_000_000) = 6, log10(100_000_000_000) ~ 11
        # Normalize so score of 1M -> ~0.4, 100B -> ~0.9
        log_score = math.log10(max(raw_score, 1))
        # Scale to 0-1 with max around log10(1e12) = 12
        normalized = min(log_score / 12.0, 1.0)
        return normalized

    # =========================================================================
    # Paper Hydration from PostgreSQL
    # =========================================================================

    async def _hydrate_papers(
        self,
        paper_ids: list[UUID],
        organization_id: UUID,
        scope: SearchScope = SearchScope.LIBRARY,
    ) -> dict[UUID, Paper]:
        """Load paper metadata from PostgreSQL for a list of IDs.

        Args:
            paper_ids: Paper IDs to hydrate.
            organization_id: Tenant isolation (used when scope='library').
            scope: Search scope — 'library' filters by org, 'catalog' by is_global.

        Returns:
            Dict mapping paper ID to Paper ORM object.
        """
        if not paper_ids:
            return {}

        query = select(Paper).where(Paper.id.in_(paper_ids))

        if scope == SearchScope.CATALOG:
            query = query.where(Paper.is_global.is_(True))
        else:
            query = query.where(Paper.organization_id == organization_id)

        result = await self.db.execute(query)
        papers = result.scalars().all()
        return {p.id: p for p in papers}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_latest_scores(
        self,
        paper_ids: list[UUID],
        organization_id: UUID,
    ) -> dict[UUID, ScoreSummary]:
        """Fetch latest scores for a list of papers."""
        if not paper_ids:
            return {}

        # Subquery to get latest score per paper
        latest_subquery = (
            select(
                PaperScore.paper_id,
                func.max(PaperScore.created_at).label("latest"),
            )
            .where(
                PaperScore.paper_id.in_(paper_ids),
                PaperScore.organization_id == organization_id,
            )
            .group_by(PaperScore.paper_id)
            .subquery()
        )

        query = select(PaperScore).join(
            latest_subquery,
            and_(
                PaperScore.paper_id == latest_subquery.c.paper_id,
                PaperScore.created_at == latest_subquery.c.latest,
            ),
        )

        result = await self.db.execute(query)
        scores = result.scalars().all()

        return {
            score.paper_id: ScoreSummary(
                overall_score=score.overall_score,
                novelty=score.novelty,
                ip_potential=score.ip_potential,
                marketability=score.marketability,
                feasibility=score.feasibility,
                commercialization=score.commercialization,
            )
            for score in scores
        }

    async def _get_paper(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> Paper | None:
        """Get paper with tenant isolation."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()
