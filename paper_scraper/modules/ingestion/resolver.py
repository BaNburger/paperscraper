"""Entity resolution for ingestion bundles into canonical paper rows."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.ingestion.interfaces import (
    CanonicalPaperResult,
    EntityResolver,
    NormalizedPaperBundle,
)
from paper_scraper.modules.papers.upsert_service import PaperUpsertService


class PaperEntityResolver(EntityResolver):
    """Resolve normalized bundles to existing papers or create new rows."""

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID,
        created_by_id: UUID | None = None,
    ) -> None:
        self.db = db
        self.organization_id = organization_id
        self.created_by_id = created_by_id
        self.upsert_service = PaperUpsertService(db)

    async def resolve(self, bundle: NormalizedPaperBundle) -> CanonicalPaperResult:
        """Resolve paper identifiers and upsert paper row."""
        result = await self.upsert_service.upsert_from_bundle(
            bundle=bundle,
            organization_id=self.organization_id,
            created_by_id=self.created_by_id,
        )
        return CanonicalPaperResult(
            paper_id=result.paper.id,
            matched_on=result.matched_on,
            created=result.created,
            dedupe_candidates=[] if result.created else [result.paper.id],
        )

    async def resolve_many(
        self,
        bundles: list[NormalizedPaperBundle],
    ) -> list[CanonicalPaperResult]:
        """Resolve multiple bundles with a shared prefetch strategy."""
        if not bundles:
            return []

        results = await self.upsert_service.upsert_many(
            bundles=bundles,
            organization_id=self.organization_id,
            created_by_id=self.created_by_id,
        )
        return [
            CanonicalPaperResult(
                paper_id=result.paper.id,
                matched_on=result.matched_on,
                created=result.created,
                dedupe_candidates=[] if result.created else [result.paper.id],
            )
            for result in results
        ]
