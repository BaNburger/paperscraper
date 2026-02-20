"""Service layer for trends module."""

import logging
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.core.sync import SyncService
from paper_scraper.core.vector import VectorService
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.scoring.embeddings import EmbeddingClient
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.trends.analyzer import TrendAnalyzer
from paper_scraper.modules.trends.models import TrendPaper, TrendSnapshot, TrendTopic
from paper_scraper.modules.trends.schemas import (
    TrendDashboardResponse,
    TrendPaperListResponse,
    TrendPaperResponse,
    TrendSnapshotResponse,
    TrendTopicCreate,
    TrendTopicListResponse,
    TrendTopicResponse,
    TrendTopicUpdate,
)

logger = logging.getLogger(__name__)


class TrendsService:
    """Service for trend radar operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def create_topic(
        self,
        data: TrendTopicCreate,
        organization_id: UUID,
        user_id: UUID,
    ) -> TrendTopicResponse:
        """Create a new trend topic and embed its description."""
        topic = TrendTopic(
            organization_id=organization_id,
            created_by_id=user_id,
            name=data.name,
            description=data.description,
            color=data.color,
        )
        self.db.add(topic)
        await self.db.flush()
        await self.db.refresh(topic)

        # Generate embedding and sync to Qdrant
        embedding = await self._embed_description(data.description)
        if embedding is not None:
            sync = SyncService()
            await sync.sync_trend(
                trend_id=topic.id,
                organization_id=organization_id,
                embedding=embedding,
            )

        return self._build_topic_response(topic, snapshot=None)

    async def list_topics(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> TrendTopicListResponse:
        """List all trend topics for an organization with summary metrics."""
        query = select(TrendTopic).where(TrendTopic.organization_id == organization_id)
        if not include_inactive:
            query = query.where(TrendTopic.is_active.is_(True))
        query = query.order_by(desc(TrendTopic.created_at))

        result = await self.db.execute(query)
        topics = result.scalars().all()

        # Batch-fetch latest snapshots for all topics
        topic_ids = [t.id for t in topics]
        snapshots_map = await self._get_latest_snapshots(topic_ids)

        items = [self._build_topic_response(topic, snapshots_map.get(topic.id)) for topic in topics]
        return TrendTopicListResponse(items=items, total=len(items))

    async def get_topic(
        self,
        topic_id: UUID,
        organization_id: UUID,
    ) -> TrendTopicResponse:
        """Get a single trend topic by ID."""
        topic = await self._get_topic(topic_id, organization_id)
        snapshot = await self._get_latest_snapshot(topic_id)
        return self._build_topic_response(topic, snapshot)

    async def update_topic(
        self,
        topic_id: UUID,
        data: TrendTopicUpdate,
        organization_id: UUID,
    ) -> TrendTopicResponse:
        """Update a trend topic. Re-embeds if description changes."""
        topic = await self._get_topic(topic_id, organization_id)

        if data.name is not None:
            topic.name = data.name
        if data.description is not None:
            topic.description = data.description
            embedding = await self._embed_description(data.description)
            if embedding is not None:
                sync = SyncService()
                await sync.sync_trend(
                    trend_id=topic.id,
                    organization_id=topic.organization_id,
                    embedding=embedding,
                )
        if data.color is not None:
            topic.color = data.color
        if data.is_active is not None:
            topic.is_active = data.is_active

        await self.db.flush()
        await self.db.refresh(topic)

        snapshot = await self._get_latest_snapshot(topic_id)
        return self._build_topic_response(topic, snapshot)

    async def delete_topic(
        self,
        topic_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a trend topic and all associated data."""
        topic = await self._get_topic(topic_id, organization_id)

        # Clean up Qdrant vector
        vector = VectorService()
        await vector.delete("trends", str(topic.id))

        await self.db.delete(topic)
        await self.db.flush()

    # =========================================================================
    # Analysis
    # =========================================================================

    async def analyze_topic(
        self,
        topic_id: UUID,
        organization_id: UUID,
        min_similarity: float = 0.65,
        max_papers: int = 100,
    ) -> TrendSnapshotResponse:
        """Run analysis pipeline for a trend topic."""
        topic = await self._get_topic(topic_id, organization_id)

        # Ensure embedding exists in Qdrant
        vector = VectorService()
        has_vector = await vector.has_vector("trends", topic.id)
        if not has_vector:
            embedding = await self._embed_description(topic.description)
            if embedding is not None:
                sync = SyncService()
                await sync.sync_trend(
                    trend_id=topic.id,
                    organization_id=organization_id,
                    embedding=embedding,
                )

        analyzer = TrendAnalyzer(self.db)
        snapshot = await analyzer.analyze(
            topic=topic,
            min_similarity=min_similarity,
            max_papers=max_papers,
        )
        return TrendSnapshotResponse.model_validate(snapshot)

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard(
        self,
        topic_id: UUID,
        organization_id: UUID,
    ) -> TrendDashboardResponse:
        """Get complete dashboard data for a trend topic."""
        topic = await self._get_topic(topic_id, organization_id)
        snapshot = await self._get_latest_snapshot(topic_id)

        # Get top 10 papers by relevance
        top_papers_result = await self.get_matched_papers(
            topic_id=topic_id,
            organization_id=organization_id,
            page=1,
            page_size=10,
        )

        return TrendDashboardResponse(
            topic=self._build_topic_response(topic, snapshot),
            snapshot=TrendSnapshotResponse.model_validate(snapshot) if snapshot else None,
            top_papers=top_papers_result.items,
        )

    async def get_matched_papers(
        self,
        topic_id: UUID,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> TrendPaperListResponse:
        """Get paginated list of matched papers for a trend."""
        # Count total
        count_query = (
            select(func.count())
            .select_from(TrendPaper)
            .where(
                TrendPaper.trend_topic_id == topic_id,
                TrendPaper.organization_id == organization_id,
            )
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated papers with scores
        query = (
            select(TrendPaper, Paper, PaperScore)
            .join(Paper, TrendPaper.paper_id == Paper.id)
            .outerjoin(
                PaperScore,
                and_(
                    PaperScore.paper_id == Paper.id,
                    PaperScore.organization_id == organization_id,
                ),
            )
            .where(
                TrendPaper.trend_topic_id == topic_id,
                TrendPaper.organization_id == organization_id,
            )
            .order_by(desc(TrendPaper.relevance_score))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        rows = result.unique().all()

        items = []
        for trend_paper, paper, score in rows:
            items.append(
                TrendPaperResponse(
                    id=paper.id,
                    title=paper.title,
                    abstract=paper.abstract,
                    doi=paper.doi,
                    journal=paper.journal,
                    publication_date=paper.publication_date,
                    relevance_score=trend_paper.relevance_score,
                    overall_score=score.overall_score if score else None,
                    novelty=score.novelty if score else None,
                    ip_potential=score.ip_potential if score else None,
                )
            )

        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return TrendPaperListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_topic(self, topic_id: UUID, organization_id: UUID) -> TrendTopic:
        """Get topic with tenant isolation. Raises NotFoundError."""
        result = await self.db.execute(
            select(TrendTopic).where(
                TrendTopic.id == topic_id,
                TrendTopic.organization_id == organization_id,
            )
        )
        topic = result.scalar_one_or_none()
        if not topic:
            raise NotFoundError("TrendTopic", str(topic_id))
        return topic

    async def _get_latest_snapshot(self, topic_id: UUID) -> TrendSnapshot | None:
        """Get the most recent snapshot for a topic."""
        result = await self.db.execute(
            select(TrendSnapshot)
            .where(TrendSnapshot.trend_topic_id == topic_id)
            .order_by(desc(TrendSnapshot.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_latest_snapshots(self, topic_ids: list[UUID]) -> dict[UUID, TrendSnapshot]:
        """Batch-fetch latest snapshot for each topic."""
        if not topic_ids:
            return {}

        # Use DISTINCT ON to get the latest per topic
        query = (
            select(TrendSnapshot)
            .where(TrendSnapshot.trend_topic_id.in_(topic_ids))
            .distinct(TrendSnapshot.trend_topic_id)
            .order_by(TrendSnapshot.trend_topic_id, desc(TrendSnapshot.created_at))
        )
        result = await self.db.execute(query)
        snapshots = result.scalars().all()

        return {s.trend_topic_id: s for s in snapshots}

    @staticmethod
    def _build_topic_response(
        topic: TrendTopic,
        snapshot: TrendSnapshot | None,
    ) -> TrendTopicResponse:
        """Build topic response with snapshot summary data."""
        return TrendTopicResponse(
            id=topic.id,
            organization_id=topic.organization_id,
            created_by_id=topic.created_by_id,
            name=topic.name,
            description=topic.description,
            color=topic.color,
            is_active=topic.is_active,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
            matched_papers_count=snapshot.matched_papers_count if snapshot else 0,
            avg_overall_score=snapshot.avg_overall_score if snapshot else None,
            patent_count=snapshot.patent_count if snapshot else 0,
            last_analyzed_at=snapshot.created_at if snapshot else None,
        )

    @staticmethod
    async def _embed_description(description: str) -> list[float] | None:
        """Embed a trend description using the embedding client.

        Returns None if embedding fails (e.g. no API key configured).
        The embedding will be generated during analysis instead.
        """
        try:
            client = EmbeddingClient()
            return await client.embed_text(description)
        except Exception as exc:
            logger.warning("Failed to embed trend description: %s", exc)
            return None
