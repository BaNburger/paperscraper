"""Trend analysis pipeline.

Handles the heavy lifting: semantic paper matching, score aggregation,
patent search, keyword extraction, timeline building, and AI summary.
"""

import logging
from collections import Counter
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.papers.clients.epo_ops import EPOOPSClient
from paper_scraper.modules.papers.models import Paper
from paper_scraper.modules.scoring.models import PaperScore
from paper_scraper.modules.trends.models import TrendPaper, TrendSnapshot, TrendTopic

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes trend topics and generates snapshots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        topic: TrendTopic,
        min_similarity: float = 0.65,
        max_papers: int = 100,
    ) -> TrendSnapshot:
        """Run full analysis pipeline for a trend topic.

        Steps:
            1. Find semantically matching papers
            2. Store paper matches
            3. Aggregate scoring dimensions
            4. Search for related patents
            5. Extract top keywords
            6. Build publication timeline
            7. Generate AI summary
        """
        logger.info("Analyzing trend topic: %s (id=%s)", topic.name, topic.id)

        # Step 1: Find matching papers via embedding similarity
        matched = await self._find_matching_papers(topic, min_similarity, max_papers)
        logger.info("Found %d matching papers for trend %s", len(matched), topic.name)

        # Step 2: Store paper matches
        await self._store_matched_papers(topic.id, topic.organization_id, matched)

        # Step 3: Aggregate scores across matched papers
        score_stats = await self._aggregate_scores(topic.id, topic.organization_id)

        # Step 4: Search EPO for related patents
        patent_results = await self._search_patents(topic.name)

        # Step 5: Extract keywords from matched papers
        top_keywords = await self._extract_keywords(topic.id)

        # Step 6: Build publication timeline
        timeline_data = await self._build_timeline(topic.id)

        # Step 7: Generate AI summary
        summary, insights = await self._generate_summary(
            topic=topic,
            paper_count=len(matched),
            score_stats=score_stats,
            patent_count=len(patent_results),
            top_keywords=top_keywords[:5],
        )

        # Create snapshot
        snapshot = TrendSnapshot(
            trend_topic_id=topic.id,
            organization_id=topic.organization_id,
            matched_papers_count=len(matched),
            avg_novelty=score_stats.get("avg_novelty"),
            avg_ip_potential=score_stats.get("avg_ip_potential"),
            avg_marketability=score_stats.get("avg_marketability"),
            avg_feasibility=score_stats.get("avg_feasibility"),
            avg_commercialization=score_stats.get("avg_commercialization"),
            avg_team_readiness=score_stats.get("avg_team_readiness"),
            avg_overall_score=score_stats.get("avg_overall_score"),
            patent_count=len(patent_results),
            patent_results=patent_results[:10],
            summary=summary,
            key_insights=insights,
            top_keywords=top_keywords,
            timeline_data=timeline_data,
        )

        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)

        logger.info(
            "Created snapshot %s for trend %s (%d papers, %d patents)",
            snapshot.id,
            topic.name,
            len(matched),
            len(patent_results),
        )
        return snapshot

    async def _find_matching_papers(
        self,
        topic: TrendTopic,
        min_similarity: float,
        max_papers: int,
    ) -> list[tuple[UUID, float]]:
        """Find papers semantically similar to trend description."""
        if topic.embedding is None:
            return []

        # cosine_distance returns 0..2 where 0 = identical
        # similarity = 1 - distance, so distance <= 1 - min_similarity
        max_distance = 1 - min_similarity

        query = (
            select(
                Paper.id,
                (1 - Paper.embedding.cosine_distance(topic.embedding)).label("similarity"),
            )
            .where(
                Paper.organization_id == topic.organization_id,
                Paper.embedding.is_not(None),
                Paper.embedding.cosine_distance(topic.embedding) <= max_distance,
            )
            .order_by(Paper.embedding.cosine_distance(topic.embedding))
            .limit(max_papers)
        )

        result = await self.db.execute(query)
        return [(row[0], float(row[1])) for row in result.all()]

    async def _store_matched_papers(
        self,
        topic_id: UUID,
        organization_id: UUID,
        matched: list[tuple[UUID, float]],
    ) -> None:
        """Replace existing paper matches with new ones."""
        # Delete existing matches
        await self.db.execute(delete(TrendPaper).where(TrendPaper.trend_topic_id == topic_id))

        # Insert new matches
        for paper_id, similarity in matched:
            self.db.add(
                TrendPaper(
                    trend_topic_id=topic_id,
                    paper_id=paper_id,
                    organization_id=organization_id,
                    relevance_score=similarity,
                )
            )

        await self.db.flush()

    async def _aggregate_scores(
        self,
        topic_id: UUID,
        organization_id: UUID,
    ) -> dict[str, float | None]:
        """Aggregate scoring dimensions across matched papers."""
        # Join trend_papers → paper_scores, take latest score per paper
        latest_score = (
            select(
                PaperScore.paper_id,
                func.max(PaperScore.created_at).label("latest"),
            )
            .where(PaperScore.organization_id == organization_id)
            .group_by(PaperScore.paper_id)
            .subquery()
        )

        query = (
            select(
                func.avg(PaperScore.novelty).label("avg_novelty"),
                func.avg(PaperScore.ip_potential).label("avg_ip_potential"),
                func.avg(PaperScore.marketability).label("avg_marketability"),
                func.avg(PaperScore.feasibility).label("avg_feasibility"),
                func.avg(PaperScore.commercialization).label("avg_commercialization"),
                func.avg(PaperScore.team_readiness).label("avg_team_readiness"),
                func.avg(PaperScore.overall_score).label("avg_overall_score"),
            )
            .select_from(TrendPaper)
            .join(latest_score, TrendPaper.paper_id == latest_score.c.paper_id)
            .join(
                PaperScore,
                and_(
                    PaperScore.paper_id == latest_score.c.paper_id,
                    PaperScore.created_at == latest_score.c.latest,
                ),
            )
            .where(TrendPaper.trend_topic_id == topic_id)
        )

        result = await self.db.execute(query)
        row = result.one_or_none()

        if not row or row[0] is None:
            return {}

        return {
            "avg_novelty": round(float(row[0]), 2) if row[0] is not None else None,
            "avg_ip_potential": round(float(row[1]), 2) if row[1] is not None else None,
            "avg_marketability": round(float(row[2]), 2) if row[2] is not None else None,
            "avg_feasibility": round(float(row[3]), 2) if row[3] is not None else None,
            "avg_commercialization": round(float(row[4]), 2) if row[4] is not None else None,
            "avg_team_readiness": round(float(row[5]), 2) if row[5] is not None else None,
            "avg_overall_score": round(float(row[6]), 2) if row[6] is not None else None,
        }

    async def _search_patents(self, topic_name: str) -> list[dict]:
        """Search EPO for related patents."""
        try:
            async with EPOOPSClient() as epo:
                return await epo.search_patents(query=topic_name, max_results=20)
        except Exception as e:
            logger.warning("EPO patent search failed: %s", e)
            return []

    async def _extract_keywords(
        self,
        topic_id: UUID,
        max_keywords: int = 20,
    ) -> list[dict]:
        """Extract top keywords from matched papers."""
        query = (
            select(Paper.keywords)
            .select_from(TrendPaper)
            .join(Paper, TrendPaper.paper_id == Paper.id)
            .where(TrendPaper.trend_topic_id == topic_id)
        )

        result = await self.db.execute(query)
        all_keywords: list[str] = []
        for (keywords,) in result:
            if keywords:
                all_keywords.extend(keywords)

        counter = Counter(all_keywords)
        return [{"keyword": kw, "count": count} for kw, count in counter.most_common(max_keywords)]

    async def _build_timeline(self, topic_id: UUID) -> list[dict]:
        """Build publication timeline (papers per month)."""
        query = (
            select(
                func.to_char(Paper.publication_date, "YYYY-MM").label("month"),
                func.count().label("count"),
            )
            .select_from(TrendPaper)
            .join(Paper, TrendPaper.paper_id == Paper.id)
            .where(
                TrendPaper.trend_topic_id == topic_id,
                Paper.publication_date.is_not(None),
            )
            .group_by(func.to_char(Paper.publication_date, "YYYY-MM"))
            .order_by(func.to_char(Paper.publication_date, "YYYY-MM"))
        )

        result = await self.db.execute(query)
        return [{"date": row[0], "count": row[1]} for row in result.all()]

    async def _generate_summary(
        self,
        topic: TrendTopic,
        paper_count: int,
        score_stats: dict,
        patent_count: int,
        top_keywords: list[dict],
    ) -> tuple[str, list[str]]:
        """Generate AI summary and key insights using LLM."""
        try:
            from paper_scraper.modules.scoring.llm_client import get_llm_client

            llm = get_llm_client()
        except Exception as e:
            logger.warning("Could not initialize LLM client: %s", e)
            return "", []

        keywords_str = ", ".join(kw["keyword"] for kw in top_keywords) if top_keywords else "N/A"

        prompt = f"""Analyze this research trend topic and provide a concise summary.

Topic: {topic.name}
Description: {topic.description}

Data from our paper library:
- Matching papers found: {paper_count}
- Related patents found: {patent_count}
- Top keywords: {keywords_str}
- Average scores (0-10 scale):
  - Novelty: {score_stats.get('avg_novelty', 'N/A')}
  - IP Potential: {score_stats.get('avg_ip_potential', 'N/A')}
  - Marketability: {score_stats.get('avg_marketability', 'N/A')}
  - Feasibility: {score_stats.get('avg_feasibility', 'N/A')}
  - Commercialization: {score_stats.get('avg_commercialization', 'N/A')}
  - Team Readiness: {score_stats.get('avg_team_readiness', 'N/A')}

Generate:
1. A 2-3 sentence executive summary of this research trend
2. 3-5 actionable key insights

Respond strictly in JSON format:
{{
  "summary": "...",
  "insights": ["...", "...", "..."]
}}"""

        try:
            response = await llm.complete_json(
                prompt=prompt,
                system="You are a technology transfer and research trends analyst. Provide concise, data-driven insights.",
                temperature=0.4,
                max_tokens=800,
            )
            return response.get("summary", ""), response.get("insights", [])
        except Exception as e:
            logger.warning("AI summary generation failed: %s", e)
            return "", []
