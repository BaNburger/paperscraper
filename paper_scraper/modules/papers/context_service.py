"""Service for paper context snapshot generation and retrieval."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.integrations.connectors.market_feed import MarketFeedConnector
from paper_scraper.modules.integrations.models import (
    ConnectorStatus,
    ConnectorType,
    IntegrationConnector,
)
from paper_scraper.modules.papers.clients.epo_ops import EPOOPSClient
from paper_scraper.modules.papers.context_models import PaperContextSnapshot
from paper_scraper.modules.papers.models import Paper


class PaperContextService:
    """Build and serve enrichment context snapshots for papers."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.market_connector = MarketFeedConnector()

    async def get_snapshot(
        self,
        paper_id: UUID,
        organization_id: UUID,
        enrichment_version: str = "v1",
    ) -> PaperContextSnapshot | None:
        """Get latest context snapshot for a paper/version."""
        result = await self.db.execute(
            select(PaperContextSnapshot).where(
                PaperContextSnapshot.paper_id == paper_id,
                PaperContextSnapshot.organization_id == organization_id,
                PaperContextSnapshot.enrichment_version == enrichment_version,
            )
        )
        return result.scalar_one_or_none()

    async def refresh_snapshot(
        self,
        paper_id: UUID,
        organization_id: UUID,
        enrichment_version: str = "v1",
    ) -> PaperContextSnapshot:
        """Refresh a paper's context snapshot by running enrichments."""
        paper = await self._get_paper(paper_id, organization_id)
        if paper is None:
            raise NotFoundError("Paper", str(paper_id))

        research_fragment = self._build_research_fragment(paper)
        related_fragment = await self._build_related_research_fragment(
            paper_id=paper.id,
            organization_id=organization_id,
        )
        patent_fragment = await self._build_patent_fragment(paper)
        market_fragment = await self._build_market_fragment(
            paper=paper,
            organization_id=organization_id,
        )

        context_json = {
            "paper_id": str(paper.id),
            "enrichment_version": enrichment_version,
            "generated_at": datetime.now(UTC).isoformat(),
            "research": research_fragment,
            "related_research": related_fragment,
            "patents": patent_fragment,
            "market": market_fragment,
            "status": {
                "research": research_fragment["status"],
                "related_research": related_fragment["status"],
                "patents": patent_fragment["status"],
                "market": market_fragment["status"],
            },
        }

        snapshot = await self.get_snapshot(
            paper_id=paper.id,
            organization_id=organization_id,
            enrichment_version=enrichment_version,
        )
        if snapshot is None:
            snapshot = PaperContextSnapshot(
                paper_id=paper.id,
                organization_id=organization_id,
                enrichment_version=enrichment_version,
                context_json=context_json,
                freshness_at=datetime.now(UTC),
            )
            self.db.add(snapshot)
        else:
            snapshot.context_json = context_json
            snapshot.freshness_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def _get_paper(self, paper_id: UUID, organization_id: UUID) -> Paper | None:
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    def _build_research_fragment(self, paper: Paper) -> dict:
        return {
            "status": "ok",
            "data": {
                "title": paper.title,
                "abstract": paper.abstract,
                "keywords": paper.keywords or [],
                "journal": paper.journal,
                "publication_date": (
                    paper.publication_date.isoformat() if paper.publication_date else None
                ),
                "source": paper.source.value if hasattr(paper.source, "value") else str(paper.source),
                "references_count": paper.references_count,
                "citations_count": paper.citations_count,
            },
        }

    async def _build_related_research_fragment(
        self,
        paper_id: UUID,
        organization_id: UUID,
    ) -> dict:
        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.organization_id == organization_id,
                Paper.id != paper_id,
            )
            .order_by(Paper.created_at.desc())
            .limit(5)
        )
        related = list(result.scalars().all())

        return {
            "status": "ok",
            "data": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "doi": item.doi,
                    "journal": item.journal,
                    "publication_date": (
                        item.publication_date.isoformat() if item.publication_date else None
                    ),
                }
                for item in related
            ],
        }

    async def _build_patent_fragment(self, paper: Paper) -> dict:
        try:
            async with EPOOPSClient() as client:
                patents = await client.search_patents(query=paper.title, max_results=5)
            return {"status": "ok", "data": patents}
        except Exception as exc:
            return {"status": "partial", "data": [], "error": str(exc)[:500]}

    async def _build_market_fragment(
        self,
        paper: Paper,
        organization_id: UUID,
    ) -> dict:
        result = await self.db.execute(
            select(IntegrationConnector).where(
                IntegrationConnector.organization_id == organization_id,
                IntegrationConnector.connector_type == ConnectorType.MARKET_FEED,
                IntegrationConnector.status == ConnectorStatus.ACTIVE,
            )
        )
        connectors = list(result.scalars().all())
        if not connectors:
            return {
                "status": "partial",
                "data": [],
                "error": "No active market_feed connector configured",
            }

        keyword_hints = list(paper.keywords or [])
        keyword_hints.extend(word for word in paper.title.split()[:10])

        signals: list[dict] = []
        for connector in connectors:
            connector_signals = await self.market_connector.fetch_signals(
                config=connector.config_json or {},
                keywords=keyword_hints,
                limit=10,
            )
            signals.extend(connector_signals)

        return {"status": "ok", "data": signals[:20]}
