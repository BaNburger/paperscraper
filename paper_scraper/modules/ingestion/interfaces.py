"""Core ingestion/enrichment/scoring interfaces for pipeline composition."""

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID


@dataclass
class ConnectorBatch:
    """Batch payload returned by source connectors."""

    records: list[dict[str, Any]]
    cursor_before: dict[str, Any] = field(default_factory=dict)
    cursor_after: dict[str, Any] = field(default_factory=dict)
    has_more: bool = False


class SourceConnector(Protocol):
    """Protocol for external source connectors."""

    async def fetch(
        self,
        cursor: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        limit: int,
    ) -> ConnectorBatch: ...


@dataclass
class NormalizedAuthor:
    """Canonical author payload from source normalization."""

    name: str
    orcid: str | None = None
    source_ids: dict[str, str] = field(default_factory=dict)
    affiliations: list[str] = field(default_factory=list)


@dataclass
class NormalizedPaperBundle:
    """Canonical candidate paper payload from source normalization."""

    source: str
    source_record_id: str
    title: str
    abstract: str | None
    publication_date: str | None
    doi: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    authors: list[NormalizedAuthor] = field(default_factory=list)


class Normalizer(Protocol):
    """Protocol for normalizing raw source records."""

    def normalize(self, record: dict[str, Any]) -> NormalizedPaperBundle: ...


@dataclass
class CanonicalPaperResult:
    """Resolution result for canonical paper upsert."""

    paper_id: UUID
    matched_on: str
    created: bool
    dedupe_candidates: list[UUID] = field(default_factory=list)


class EntityResolver(Protocol):
    """Protocol for entity resolution/upsert logic."""

    async def resolve(self, bundle: NormalizedPaperBundle) -> CanonicalPaperResult: ...


@dataclass
class EnrichmentFragment:
    """Output fragment from a single enrichment provider."""

    source: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class EnrichmentProvider(Protocol):
    """Protocol for enrichment providers."""

    async def enrich(
        self,
        paper_id: UUID,
        context_hints: dict[str, Any] | None = None,
    ) -> EnrichmentFragment: ...


@dataclass
class ScoreContext:
    """Assembled context for model scoring."""

    paper_id: UUID
    organization_id: UUID
    user_id: UUID | None
    prompt_context: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ScoreContextAssembler(Protocol):
    """Protocol for assembling scoring context."""

    async def build(
        self,
        paper_id: UUID,
        organization_id: UUID,
        user_id: UUID | None = None,
    ) -> ScoreContext: ...
