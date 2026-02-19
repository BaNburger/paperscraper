"""Canonical paper upsert service for ingestion and integration pipelines."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.ingestion.interfaces import NormalizedAuthor, NormalizedPaperBundle
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource

_DOI_PREFIXES = ("https://doi.org/", "http://dx.doi.org/", "doi:")
_TITLE_WS_RE = re.compile(r"\s+")


@dataclass(slots=True)
class PaperUpsertResult:
    """Result of canonical paper upsert."""

    paper: Paper
    created: bool
    matched_on: str
    merged: bool = False


class PaperUpsertService:
    """Tenant-scoped paper upsert service with deterministic dedupe precedence.

    Dedupe precedence:
    1) normalized DOI
    2) (source, source_id)
    3) (normalized_title, publication_year)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert_from_bundle(
        self,
        bundle: NormalizedPaperBundle,
        organization_id: UUID,
        created_by_id: UUID | None = None,
    ) -> PaperUpsertResult:
        """Upsert a single normalized bundle."""
        results = await self.upsert_many(
            bundles=[bundle],
            organization_id=organization_id,
            created_by_id=created_by_id,
        )
        return results[0]

    async def upsert_many(
        self,
        bundles: list[NormalizedPaperBundle],
        organization_id: UUID,
        created_by_id: UUID | None = None,
    ) -> list[PaperUpsertResult]:
        """Batch upsert normalized bundles with lookup prefetch."""
        if not bundles:
            return []

        doi_keys = {
            doi for bundle in bundles if (doi := self._normalize_doi(bundle.doi)) is not None
        }
        source_keys = {
            key
            for bundle in bundles
            if (key := self._source_key(bundle.source, bundle.source_record_id)) is not None
        }
        title_keys = {
            key
            for bundle in bundles
            if (key := self._title_year_key(bundle.title, bundle.publication_date)) is not None
        }

        doi_lookup = await self._prefetch_by_doi(organization_id, doi_keys)
        source_lookup = await self._prefetch_by_source_id(organization_id, source_keys)
        title_lookup = await self._prefetch_by_title_year(organization_id, title_keys)

        orcid_lookup, openalex_lookup = await self._prefetch_authors(bundles, organization_id)

        results: list[PaperUpsertResult] = []
        for bundle in bundles:
            existing: Paper | None = None
            matched_on = "none"

            doi_key = self._normalize_doi(bundle.doi)
            if doi_key and doi_key in doi_lookup:
                existing = doi_lookup[doi_key]
                matched_on = "doi"

            if existing is None:
                source_key = self._source_key(bundle.source, bundle.source_record_id)
                if source_key and source_key in source_lookup:
                    existing = source_lookup[source_key]
                    matched_on = "source_id"

            if existing is None:
                title_year_key = self._title_year_key(bundle.title, bundle.publication_date)
                if title_year_key:
                    existing = title_lookup.get(title_year_key)
                    if existing is not None:
                        matched_on = "title_year"

            if existing is not None:
                merged = self._merge_existing(existing, bundle)
                results.append(
                    PaperUpsertResult(
                        paper=existing,
                        created=False,
                        matched_on=matched_on,
                        merged=merged,
                    )
                )
                continue

            created = await self._create_paper(
                bundle=bundle,
                organization_id=organization_id,
                created_by_id=created_by_id,
                orcid_lookup=orcid_lookup,
                openalex_lookup=openalex_lookup,
            )
            created_doi = self._normalize_doi(created.doi)
            if created_doi:
                doi_lookup[created_doi] = created
            created_source_key = self._source_key(
                created.source.value,
                created.source_id,
            )
            if created_source_key:
                source_lookup[created_source_key] = created
            created_title_key = self._title_year_key(
                created.title,
                created.publication_date.isoformat() if created.publication_date else None,
            )
            if created_title_key:
                title_lookup[created_title_key] = created

            results.append(
                PaperUpsertResult(
                    paper=created,
                    created=True,
                    matched_on="created",
                    merged=False,
                )
            )

        await self.db.flush()
        return results

    async def _prefetch_by_doi(
        self,
        organization_id: UUID,
        doi_keys: set[str],
    ) -> dict[str, Paper]:
        if not doi_keys:
            return {}

        result = await self.db.execute(
            select(Paper).where(
                Paper.organization_id == organization_id,
                Paper.doi.is_not(None),
                func.lower(Paper.doi).in_(doi_keys),
            )
        )
        papers = list(result.scalars().all())
        return {
            key: paper for paper in papers if (key := self._normalize_doi(paper.doi)) is not None
        }

    async def _prefetch_by_source_id(
        self,
        organization_id: UUID,
        source_keys: set[tuple[str, str]],
    ) -> dict[tuple[str, str], Paper]:
        if not source_keys:
            return {}

        sources = {source for source, _ in source_keys}
        source_ids = {source_id for _, source_id in source_keys}
        result = await self.db.execute(
            select(Paper).where(
                Paper.organization_id == organization_id,
                Paper.source.in_([PaperSource(source) for source in sources]),
                Paper.source_id.in_(source_ids),
            )
        )
        lookup: dict[tuple[str, str], Paper] = {}
        for paper in result.scalars().all():
            if paper.source_id:
                lookup[(paper.source.value, paper.source_id)] = paper
        return lookup

    async def _prefetch_by_title_year(
        self,
        organization_id: UUID,
        title_keys: set[tuple[str, int | None]],
    ) -> dict[tuple[str, int | None], Paper]:
        if not title_keys:
            return {}

        normalized_titles = {title for title, _ in title_keys}
        result = await self.db.execute(
            select(Paper).where(
                Paper.organization_id == organization_id,
                func.lower(Paper.title).in_(normalized_titles),
            )
        )

        lookup: dict[tuple[str, int | None], Paper] = {}
        for paper in result.scalars().all():
            title_key = self._normalize_title(paper.title)
            year = paper.publication_date.year if paper.publication_date else None
            lookup.setdefault((title_key, year), paper)
            lookup.setdefault((title_key, None), paper)
        return lookup

    async def _prefetch_authors(
        self,
        bundles: list[NormalizedPaperBundle],
        organization_id: UUID,
    ) -> tuple[dict[str, Author], dict[str, Author]]:
        orcids = {
            author.orcid.strip()
            for bundle in bundles
            for author in bundle.authors
            if author.orcid and author.orcid.strip()
        }
        openalex_ids = {
            str(author.source_ids.get("openalex_id")).strip()
            for bundle in bundles
            for author in bundle.authors
            if author.source_ids.get("openalex_id")
        }

        orcid_lookup: dict[str, Author] = {}
        openalex_lookup: dict[str, Author] = {}

        if orcids:
            result = await self.db.execute(
                select(Author).where(
                    Author.organization_id == organization_id,
                    Author.orcid.in_(orcids),
                )
            )
            for author in result.scalars().all():
                if author.orcid:
                    orcid_lookup[author.orcid] = author

        if openalex_ids:
            result = await self.db.execute(
                select(Author).where(
                    Author.organization_id == organization_id,
                    Author.openalex_id.in_(openalex_ids),
                )
            )
            for author in result.scalars().all():
                if author.openalex_id:
                    openalex_lookup[author.openalex_id] = author

        return orcid_lookup, openalex_lookup

    async def _create_paper(
        self,
        bundle: NormalizedPaperBundle,
        organization_id: UUID,
        created_by_id: UUID | None,
        orcid_lookup: dict[str, Author],
        openalex_lookup: dict[str, Author],
    ) -> Paper:
        metadata = bundle.metadata or {}
        source = self._coerce_source(bundle.source)

        paper = Paper(
            organization_id=organization_id,
            created_by_id=created_by_id,
            doi=self._normalize_doi(bundle.doi),
            source=source,
            source_id=metadata.get("source_id") or bundle.source_record_id,
            title=bundle.title,
            abstract=bundle.abstract,
            publication_date=self._parse_publication_date(bundle.publication_date),
            journal=metadata.get("journal"),
            volume=metadata.get("volume"),
            issue=metadata.get("issue"),
            pages=metadata.get("pages"),
            keywords=metadata.get("keywords") or [],
            mesh_terms=metadata.get("mesh_terms") or [],
            references_count=metadata.get("references_count"),
            citations_count=metadata.get("citations_count"),
            raw_metadata=metadata.get("raw_metadata") or {},
        )
        self.db.add(paper)
        await self.db.flush()

        for idx, author_data in enumerate(bundle.authors):
            author = await self._get_or_create_author(
                data=author_data,
                organization_id=organization_id,
                orcid_lookup=orcid_lookup,
                openalex_lookup=openalex_lookup,
            )
            self.db.add(
                PaperAuthor(
                    paper_id=paper.id,
                    author_id=author.id,
                    position=idx,
                    is_corresponding=False,
                )
            )
        await self.db.flush()
        return paper

    async def _get_or_create_author(
        self,
        data: NormalizedAuthor,
        organization_id: UUID,
        orcid_lookup: dict[str, Author],
        openalex_lookup: dict[str, Author],
    ) -> Author:
        normalized_orcid = data.orcid.strip() if data.orcid else None
        if normalized_orcid and normalized_orcid in orcid_lookup:
            return orcid_lookup[normalized_orcid]

        openalex_id = data.source_ids.get("openalex_id")
        openalex_id = openalex_id.strip() if openalex_id else None
        if openalex_id and openalex_id in openalex_lookup:
            return openalex_lookup[openalex_id]

        author = Author(
            organization_id=organization_id,
            name=data.name.strip() or "Unknown",
            orcid=normalized_orcid,
            openalex_id=openalex_id,
            affiliations=[item for item in data.affiliations if item],
        )
        self.db.add(author)
        await self.db.flush()

        if normalized_orcid:
            orcid_lookup[normalized_orcid] = author
        if openalex_id:
            openalex_lookup[openalex_id] = author
        return author

    def _merge_existing(self, paper: Paper, bundle: NormalizedPaperBundle) -> bool:
        metadata = bundle.metadata or {}
        merged = False

        normalized_doi = self._normalize_doi(bundle.doi)
        if normalized_doi and not paper.doi:
            paper.doi = normalized_doi
            merged = True

        if not paper.source_id and bundle.source_record_id:
            paper.source_id = bundle.source_record_id
            merged = True

        if not paper.abstract and bundle.abstract:
            paper.abstract = bundle.abstract
            merged = True

        parsed_date = self._parse_publication_date(bundle.publication_date)
        if paper.publication_date is None and parsed_date is not None:
            paper.publication_date = parsed_date
            merged = True

        if not paper.journal and metadata.get("journal"):
            paper.journal = metadata.get("journal")
            merged = True

        if not paper.volume and metadata.get("volume"):
            paper.volume = metadata.get("volume")
            merged = True

        if not paper.issue and metadata.get("issue"):
            paper.issue = metadata.get("issue")
            merged = True

        if not paper.pages and metadata.get("pages"):
            paper.pages = metadata.get("pages")
            merged = True

        new_keywords = self._merge_string_lists(
            paper.keywords or [], metadata.get("keywords") or []
        )
        if new_keywords != (paper.keywords or []):
            paper.keywords = new_keywords
            merged = True

        new_mesh = self._merge_string_lists(
            paper.mesh_terms or [], metadata.get("mesh_terms") or []
        )
        if new_mesh != (paper.mesh_terms or []):
            paper.mesh_terms = new_mesh
            merged = True

        new_refs = metadata.get("references_count")
        if isinstance(new_refs, int) and (
            paper.references_count is None or new_refs > paper.references_count
        ):
            paper.references_count = new_refs
            merged = True

        new_citations = metadata.get("citations_count")
        if isinstance(new_citations, int) and (
            paper.citations_count is None or new_citations > paper.citations_count
        ):
            paper.citations_count = new_citations
            merged = True

        incoming_raw = metadata.get("raw_metadata")
        if isinstance(incoming_raw, dict) and incoming_raw:
            current = paper.raw_metadata or {}
            if not isinstance(current, dict):
                current = {}
            merged_raw = {**incoming_raw, **current}
            if merged_raw != current:
                paper.raw_metadata = merged_raw
                merged = True

        return merged

    def _coerce_source(self, source: str) -> PaperSource:
        try:
            return PaperSource(source)
        except ValueError:
            return PaperSource.MANUAL

    def _normalize_doi(self, doi: str | None) -> str | None:
        if doi is None:
            return None
        normalized = doi.strip().lower()
        if not normalized:
            return None
        for prefix in _DOI_PREFIXES:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]
        return normalized or None

    def _normalize_title(self, title: str | None) -> str:
        if not title:
            return ""
        normalized = _TITLE_WS_RE.sub(" ", title).strip().lower()
        return normalized

    def _title_year_key(
        self,
        title: str | None,
        publication_date: str | None,
    ) -> tuple[str, int | None] | None:
        normalized_title = self._normalize_title(title)
        if not normalized_title:
            return None
        parsed_date = self._parse_publication_date(publication_date)
        return (normalized_title, parsed_date.year if parsed_date else None)

    def _source_key(self, source: str | None, source_id: str | None) -> tuple[str, str] | None:
        if not source or not source_id:
            return None
        try:
            coerced_source = PaperSource(source).value
        except ValueError:
            return None
        normalized_source_id = source_id.strip()
        if not normalized_source_id:
            return None
        return (coerced_source, normalized_source_id)

    def _parse_publication_date(self, publication_date: str | None) -> datetime | None:
        if not publication_date:
            return None

        value = publication_date.strip()
        if not value:
            return None
        value = value.replace("Z", "+00:00")

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        for fmt, length in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
            try:
                return datetime.strptime(value[:length], fmt)
            except ValueError:
                continue
        return None

    def _merge_string_lists(self, current: list[str], incoming: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for item in [*current, *incoming]:
            normalized = item.strip() if isinstance(item, str) else ""
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)
        return merged
