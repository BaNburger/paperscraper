"""Typed payload schemas for background jobs."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.scoring.schemas import ScoringWeightsSchema


class OpenAlexIngestionJobPayload(BaseModel):
    """Payload for OpenAlex ingestion job."""

    organization_id: UUID
    query: str
    max_results: int = Field(default=100, ge=1, le=1000)
    filters: dict = Field(default_factory=dict)


class SourceIngestionJobPayload(BaseModel):
    """Payload for async source ingestion jobs."""

    ingest_run_id: UUID
    source: Literal["openalex", "pubmed", "arxiv", "semantic_scholar"]
    organization_id: UUID
    initiated_by_id: UUID | None = None
    query: str
    max_results: int = Field(default=100, ge=1, le=1000)
    filters: dict = Field(default_factory=dict)


class BatchScoringJobPayload(BaseModel):
    """Payload for async batch scoring job."""

    job_id: UUID
    organization_id: UUID
    paper_ids: list[UUID] = Field(min_length=1, max_length=100)
    weights: ScoringWeightsSchema | None = None


class EmbeddingBackfillJobPayload(BaseModel):
    """Payload for embedding backfill jobs."""

    organization_id: UUID
    batch_size: int = Field(default=100, ge=1, le=500)
    max_papers: int | None = Field(default=None, ge=1)
