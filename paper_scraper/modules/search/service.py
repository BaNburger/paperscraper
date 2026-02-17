"""Service layer for search module."""

import time
from uuid import UUID

from sqlalchemy import and_, exists, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from paper_scraper.core.exceptions import NotFoundError
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
    SimilarPaperItem,
    SimilarPapersResponse,
)


class SearchService:
    """Service for paper search operations."""

    # RRF constant (typically 60 is used)
    RRF_K = 60

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_client = EmbeddingClient()

    # =========================================================================
    # Main Search Methods
    # =========================================================================

    async def search(
        self,
        request: SearchRequest,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> SearchResponse:
        """
        Execute a search query based on the specified mode.

        Args:
            request: Search request with query, mode, filters
            organization_id: Organization ID for tenant isolation

        Returns:
            SearchResponse with paginated results
        """
        start_time = time.time()

        if request.mode == SearchMode.FULLTEXT:
            results, total = await self._fulltext_search(
                query=request.query,
                organization_id=organization_id,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
                include_highlights=request.include_highlights,
            )
        elif request.mode == SearchMode.SEMANTIC:
            results, total = await self._semantic_search(
                query=request.query,
                organization_id=organization_id,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
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
        """
        Find papers similar to a given paper using embedding similarity.

        Args:
            paper_id: ID of the reference paper
            organization_id: Organization ID
            limit: Maximum results
            min_similarity: Minimum similarity threshold (0-1)
            filters: Optional filters

        Returns:
            SimilarPapersResponse with similar papers
        """
        # Get the reference paper
        paper = await self._get_paper(paper_id, organization_id)
        if not paper:
            raise NotFoundError("Paper", paper_id)

        if not paper.embedding:
            return SimilarPapersResponse(
                paper_id=paper_id,
                similar_papers=[],
                total_found=0,
            )

        # Build base query for similar papers
        query = (
            select(
                Paper,
                (1 - Paper.embedding.cosine_distance(paper.embedding)).label(
                    "similarity"
                ),
            )
            .where(
                Paper.organization_id == organization_id,
                Paper.id != paper_id,
                Paper.embedding.is_not(None),
            )
        )

        # Apply filters
        query = self._apply_filters(query, filters, organization_id)

        # Filter by minimum similarity (cosine distance < 1 - min_similarity)
        if min_similarity > 0:
            max_distance = 1 - min_similarity
            query = query.where(
                Paper.embedding.cosine_distance(paper.embedding) <= max_distance
            )

        # Order by similarity (lowest distance = highest similarity)
        query = query.order_by(Paper.embedding.cosine_distance(paper.embedding))
        query = query.limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        similar_papers = []
        for row in rows:
            p = row[0]
            similarity = row[1]
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
                    similarity_score=round(similarity, 4),
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
        """
        Perform semantic search by embedding the query text.

        Args:
            query: Query text to embed
            organization_id: Organization ID
            limit: Maximum results
            filters: Optional filters

        Returns:
            List of search results sorted by semantic similarity
        """
        # Generate query embedding
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
        result = await self.db.execute(
            select(func.count())
            .select_from(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.embedding.is_(None),
            )
        )
        return result.scalar() or 0

    async def get_embedding_stats(self, organization_id: UUID) -> EmbeddingStats:
        """Get embedding statistics for an organization."""
        with_embedding_result = await self.db.execute(
            select(func.count())
            .select_from(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.embedding.is_not(None),
            )
        )
        without_embedding_result = await self.db.execute(
            select(func.count())
            .select_from(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.embedding.is_(None),
            )
        )

        with_count = with_embedding_result.scalar() or 0
        without_count = without_embedding_result.scalar() or 0
        total = with_count + without_count

        coverage = round(with_count / total * 100, 2) if total > 0 else 0.0

        return EmbeddingStats(
            total_papers=total,
            with_embedding=with_count,
            without_embedding=without_count,
            embedding_coverage=coverage,
        )

    async def backfill_embeddings(
        self,
        organization_id: UUID,
        batch_size: int = 100,
        max_papers: int | None = None,
    ) -> EmbeddingBackfillResult:
        """
        Generate embeddings for papers that don't have them.

        Args:
            organization_id: Organization ID
            batch_size: Papers to process per batch
            max_papers: Maximum papers to process (None = all)

        Returns:
            EmbeddingBackfillResult with statistics
        """
        from paper_scraper.modules.scoring.embeddings import generate_paper_embedding

        # Find papers without embeddings
        query = (
            select(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.embedding.is_(None),
            )
            .order_by(Paper.created_at.desc())
        )

        if max_papers:
            query = query.limit(max_papers)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())

        succeeded = 0
        failed = 0
        errors: list[str] = []

        for paper in papers:
            try:
                embedding = await generate_paper_embedding(
                    title=paper.title,
                    abstract=paper.abstract,
                    keywords=paper.keywords,
                )
                paper.embedding = embedding
                succeeded += 1

                # Commit in batches
                if succeeded % batch_size == 0:
                    await self.db.commit()

            except Exception as e:
                failed += 1
                errors.append(f"Paper {paper.id}: {str(e)[:100]}")
                # No rollback needed: if generate_paper_embedding raises,
                # paper.embedding was never assigned so session has no dirty state.

        # Final commit for remaining papers
        if succeeded % batch_size != 0:
            await self.db.commit()

        return EmbeddingBackfillResult(
            papers_processed=len(papers),
            papers_succeeded=succeeded,
            papers_failed=failed,
            errors=errors[:10],  # Limit errors in response
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
    ) -> tuple[list[SearchResultItem], int]:
        """
        Perform full-text search using PostgreSQL trigram similarity.

        Uses pg_trgm for fuzzy matching on title and abstract.
        """
        # Calculate trigram similarity for title and abstract
        # Higher weight for title matches
        title_similarity = func.similarity(Paper.title, query).label("title_sim")
        abstract_similarity = func.coalesce(
            func.similarity(Paper.abstract, query), literal(0.0)
        ).label("abstract_sim")

        # Combined score with title weighted higher
        text_score = (title_similarity * 0.7 + abstract_similarity * 0.3).label(
            "text_score"
        )

        # Build base query
        base_query = (
            select(Paper, text_score)
            .where(
                Paper.organization_id == organization_id,
                # Match either title or abstract with minimum similarity
                or_(
                    func.similarity(Paper.title, query) > 0.1,
                    func.similarity(Paper.abstract, query) > 0.1,
                ),
            )
        )

        # Apply filters
        base_query = self._apply_filters(base_query, filters, organization_id)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Order by score and paginate
        paginated_query = (
            base_query.order_by(text_score.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(paginated_query)
        rows = result.all()

        # Fetch scores for matched papers
        paper_ids = [row[0].id for row in rows]
        scores_map = await self._get_latest_scores(paper_ids, organization_id)

        # Build results
        items = []
        for row in rows:
            paper = row[0]
            score = row[1]

            highlights = []
            if include_highlights:
                highlights = self._generate_highlights(paper, query)

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
                    has_embedding=paper.has_embedding,
                    created_at=paper.created_at,
                    relevance_score=round(score, 4),
                    text_score=round(score, 4),
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
    ) -> tuple[list[SearchResultItem], int]:
        """
        Perform semantic search using vector embeddings.

        Uses pgvector cosine distance for similarity.
        """
        # Generate query embedding if not provided
        if query_embedding is None:
            query_embedding = await self.embedding_client.embed_text(query)

        # Calculate cosine similarity (1 - distance)
        cosine_similarity = (
            1 - Paper.embedding.cosine_distance(query_embedding)
        ).label("semantic_score")

        # Build base query - only papers with embeddings
        base_query = (
            select(Paper, cosine_similarity)
            .where(
                Paper.organization_id == organization_id,
                Paper.embedding.is_not(None),
            )
        )

        # Apply filters
        base_query = self._apply_filters(base_query, filters, organization_id)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Order by similarity (highest first) and paginate
        query_stmt = (
            base_query.order_by(
                Paper.embedding.cosine_distance(query_embedding)
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query_stmt)
        rows = result.all()

        # Fetch scores
        paper_ids = [row[0].id for row in rows]
        scores_map = await self._get_latest_scores(paper_ids, organization_id)

        # Build results
        items = []
        for row in rows:
            paper = row[0]
            similarity = row[1]

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
                    has_embedding=paper.has_embedding,
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
    ) -> tuple[list[SearchResultItem], int]:
        """
        Perform hybrid search combining full-text and semantic results.

        Uses Reciprocal Rank Fusion (RRF) to combine rankings:
        RRF_score = 1/(k + rank_text) + 1/(k + rank_semantic)
        """
        # Generate query embedding
        query_embedding = await self.embedding_client.embed_text(query)

        # Fetch more results than needed for RRF merging
        fetch_limit = page_size * 5

        # Get full-text results with ranks
        text_results, text_total = await self._fulltext_search(
            query=query,
            organization_id=organization_id,
            filters=filters,
            page=1,
            page_size=fetch_limit,
            include_highlights=include_highlights,
        )

        # Get semantic results with ranks
        semantic_results, semantic_total = await self._semantic_search(
            query=query,
            organization_id=organization_id,
            filters=filters,
            page=1,
            page_size=fetch_limit,
            query_embedding=query_embedding,
        )

        # Create rank mappings
        text_ranks: dict[UUID, int] = {
            item.id: rank + 1 for rank, item in enumerate(text_results)
        }
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

        items = []
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
    # Helper Methods
    # =========================================================================

    def _apply_filters(
        self,
        query,
        filters: SearchFilters | None,
        organization_id: UUID,
    ):
        """Apply search filters to a query."""
        if not filters:
            return query

        query = self._apply_basic_filters(query, filters)
        query = self._apply_score_filters(query, filters, organization_id)

        return query

    def _apply_basic_filters(self, query, filters: SearchFilters):
        """Apply basic paper field filters."""
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

        if filters.has_embedding is True:
            query = query.where(Paper.embedding.is_not(None))
        elif filters.has_embedding is False:
            query = query.where(Paper.embedding.is_(None))

        if filters.journals:
            query = query.where(Paper.journal.in_(filters.journals))

        if filters.keywords:
            keyword_conditions = [
                Paper.keywords.contains([kw]) for kw in filters.keywords
            ]
            query = query.where(or_(*keyword_conditions))

        return query

    def _apply_score_filters(
        self,
        query,
        filters: SearchFilters,
        organization_id: UUID,
    ):
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

        query = (
            select(PaperScore)
            .join(
                latest_subquery,
                and_(
                    PaperScore.paper_id == latest_subquery.c.paper_id,
                    PaperScore.created_at == latest_subquery.c.latest,
                ),
            )
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

    def _generate_highlights(
        self,
        paper: Paper,
        query: str,
    ) -> list[SearchHighlight]:
        """Generate text highlights showing where query matches."""
        query_words = query.lower().split()
        highlights: list[SearchHighlight] = []

        # Title uses smaller context window (30 chars), abstract uses larger (50 chars)
        title_highlight = self._find_highlight(paper.title, query_words, "title", 30)
        if title_highlight:
            highlights.append(title_highlight)

        abstract_highlight = self._find_highlight(
            paper.abstract, query_words, "abstract", 50
        )
        if abstract_highlight:
            highlights.append(abstract_highlight)

        return highlights

    def _find_highlight(
        self,
        text: str | None,
        query_words: list[str],
        field: str,
        context_size: int,
    ) -> SearchHighlight | None:
        """Find a highlight snippet in text for query words."""
        if not text:
            return None

        text_lower = text.lower()
        for word in query_words:
            if word not in text_lower:
                continue

            idx = text_lower.find(word)
            start = max(0, idx - context_size)
            end = min(len(text), idx + len(word) + context_size)

            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

            return SearchHighlight(field=field, snippet=snippet)

        return None
