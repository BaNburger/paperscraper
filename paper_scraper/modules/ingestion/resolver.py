"""Entity resolution for ingestion bundles into canonical paper rows."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.ingestion.interfaces import (
    CanonicalPaperResult,
    EntityResolver,
    NormalizedPaperBundle,
)
from paper_scraper.modules.papers.models import Paper, PaperSource
from paper_scraper.modules.papers.service import PaperService


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
        self.paper_service = PaperService(db)

    async def resolve(self, bundle: NormalizedPaperBundle) -> CanonicalPaperResult:
        """Resolve paper identifiers and upsert paper row."""
        existing, matched_on = await self._find_existing(bundle)
        if existing is not None:
            return CanonicalPaperResult(
                paper_id=existing.id,
                matched_on=matched_on,
                created=False,
                dedupe_candidates=[existing.id],
            )

        paper_payload = self._bundle_to_paper_data(bundle)
        created = await self.paper_service._create_paper_from_data(  # noqa: SLF001
            data=paper_payload,
            organization_id=self.organization_id,
            created_by_id=self.created_by_id,
        )
        return CanonicalPaperResult(
            paper_id=created.id,
            matched_on="created",
            created=True,
            dedupe_candidates=[],
        )

    async def _find_existing(self, bundle: NormalizedPaperBundle) -> tuple[Paper | None, str]:
        if bundle.doi:
            result = await self.db.execute(
                select(Paper).where(
                    Paper.organization_id == self.organization_id,
                    Paper.doi == bundle.doi,
                )
            )
            paper = result.scalar_one_or_none()
            if paper is not None:
                return paper, "doi"

        source = self._coerce_source(bundle.source)
        if source and bundle.source_record_id:
            result = await self.db.execute(
                select(Paper).where(
                    Paper.organization_id == self.organization_id,
                    Paper.source == source,
                    Paper.source_id == bundle.source_record_id,
                )
            )
            paper = result.scalar_one_or_none()
            if paper is not None:
                return paper, "source_id"

        title = bundle.title.strip()
        publication_year = self._publication_year(bundle.publication_date)
        if title:
            query = select(Paper).where(
                Paper.organization_id == self.organization_id,
                func.lower(Paper.title) == title.lower(),
            )
            if publication_year is not None:
                query = query.where(func.extract("year", Paper.publication_date) == publication_year)

            result = await self.db.execute(query.limit(1))
            paper = result.scalar_one_or_none()
            if paper is not None:
                return paper, "title_year"

        return None, "none"

    def _coerce_source(self, source: str) -> PaperSource | None:
        try:
            return PaperSource(source)
        except ValueError:
            return None

    def _publication_year(self, publication_date: str | None) -> int | None:
        if not publication_date:
            return None
        try:
            return datetime.fromisoformat(publication_date).year
        except ValueError:
            return None

    def _bundle_to_paper_data(self, bundle: NormalizedPaperBundle) -> dict:
        metadata = bundle.metadata
        authors = [
            {
                "name": author.name,
                "orcid": author.orcid,
                "openalex_id": author.source_ids.get("openalex_id"),
                "affiliations": author.affiliations,
            }
            for author in bundle.authors
        ]

        return {
            "source": bundle.source,
            "source_id": metadata.get("source_id") or bundle.source_record_id,
            "doi": bundle.doi,
            "title": bundle.title,
            "abstract": bundle.abstract,
            "publication_date": bundle.publication_date,
            "journal": metadata.get("journal"),
            "volume": metadata.get("volume"),
            "issue": metadata.get("issue"),
            "pages": metadata.get("pages"),
            "keywords": metadata.get("keywords") or [],
            "mesh_terms": metadata.get("mesh_terms") or [],
            "references_count": metadata.get("references_count"),
            "citations_count": metadata.get("citations_count"),
            "authors": authors,
            "raw_metadata": metadata.get("raw_metadata") or {},
        }
