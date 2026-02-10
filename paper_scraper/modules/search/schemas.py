"""Pydantic schemas for search module."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from paper_scraper.modules.papers.models import PaperSource


class SearchMode(str, Enum):
    """Search mode enumeration."""

    FULLTEXT = "fulltext"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


# =============================================================================
# Search Request Schemas
# =============================================================================


class SearchFilters(BaseModel):
    """Filters for search queries."""

    sources: list[PaperSource] | None = Field(
        default=None, description="Filter by paper sources"
    )
    min_score: float | None = Field(
        default=None, ge=0, le=10, description="Minimum overall score"
    )
    max_score: float | None = Field(
        default=None, ge=0, le=10, description="Maximum overall score"
    )
    date_from: datetime | None = Field(
        default=None, description="Filter papers published after this date"
    )
    date_to: datetime | None = Field(
        default=None, description="Filter papers published before this date"
    )
    ingested_from: datetime | None = Field(
        default=None, description="Filter papers ingested after this date"
    )
    ingested_to: datetime | None = Field(
        default=None, description="Filter papers ingested before this date"
    )
    has_embedding: bool | None = Field(
        default=None, description="Filter by embedding presence"
    )
    has_score: bool | None = Field(
        default=None, description="Filter by score presence"
    )
    journals: list[str] | None = Field(
        default=None, description="Filter by journal names"
    )
    keywords: list[str] | None = Field(
        default=None, description="Filter by keywords (any match)"
    )


class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(
        ..., min_length=1, max_length=1000, description="Search query text"
    )
    mode: SearchMode = Field(
        default=SearchMode.HYBRID, description="Search mode to use"
    )
    filters: SearchFilters | None = Field(
        default=None, description="Optional search filters"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")
    include_highlights: bool = Field(
        default=True, description="Include text highlights for fulltext search"
    )
    semantic_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for semantic results in hybrid search (0=fulltext only, 1=semantic only)",
    )


class SimilarPapersRequest(BaseModel):
    """Request to find similar papers."""

    paper_id: UUID = Field(..., description="ID of paper to find similar papers for")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum papers to return")
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0-1)",
    )
    filters: SearchFilters | None = Field(
        default=None, description="Optional search filters"
    )


class SemanticSearchRequest(BaseModel):
    """Request for pure semantic search with query embedding."""

    query: str = Field(
        ..., min_length=1, max_length=5000, description="Query text to embed and search"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum papers to return")
    filters: SearchFilters | None = Field(
        default=None, description="Optional search filters"
    )


# =============================================================================
# Search Response Schemas
# =============================================================================


class SearchHighlight(BaseModel):
    """Text highlight from search."""

    field: str = Field(..., description="Field containing the match (title/abstract)")
    snippet: str = Field(..., description="Highlighted snippet")


class ScoreSummary(BaseModel):
    """Brief score summary for search results."""

    overall_score: float
    novelty: float
    ip_potential: float
    marketability: float
    feasibility: float
    commercialization: float


class SearchResultItem(BaseModel):
    """Individual search result item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    source: PaperSource
    journal: str | None = None
    publication_date: datetime | None = None
    keywords: list[str] = Field(default_factory=list)
    citations_count: int | None = None
    has_embedding: bool = False
    created_at: datetime

    # Search-specific fields
    relevance_score: float = Field(
        default=0.0, description="Combined relevance score (0-1)"
    )
    text_score: float | None = Field(
        default=None, description="Full-text search score"
    )
    semantic_score: float | None = Field(
        default=None, description="Semantic similarity score"
    )
    highlights: list[SearchHighlight] = Field(
        default_factory=list, description="Highlighted snippets"
    )
    score: ScoreSummary | None = Field(
        default=None, description="Paper scores if available"
    )


class SearchResponse(BaseModel):
    """Paginated search response."""

    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    pages: int
    query: str
    mode: SearchMode
    search_time_ms: float = Field(default=0.0, description="Search execution time in ms")


class SimilarPaperItem(BaseModel):
    """Similar paper result item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    abstract: str | None = None
    doi: str | None = None
    source: PaperSource
    journal: str | None = None
    publication_date: datetime | None = None
    keywords: list[str] = Field(default_factory=list)

    similarity_score: float = Field(
        default=0.0, description="Cosine similarity score (0-1)"
    )


class SimilarPapersResponse(BaseModel):
    """Response for similar papers query."""

    paper_id: UUID
    similar_papers: list[SimilarPaperItem]
    total_found: int


# =============================================================================
# Embedding Backfill Schemas
# =============================================================================


class EmbeddingBackfillRequest(BaseModel):
    """Request to backfill embeddings."""

    batch_size: int = Field(default=100, ge=1, le=500, description="Papers per batch")
    max_papers: int | None = Field(
        default=None, ge=1, description="Maximum papers to process (None = all)"
    )


class EmbeddingBackfillResponse(BaseModel):
    """Response for embedding backfill operation."""

    job_id: str
    status: str = "queued"
    papers_to_process: int
    message: str


class EmbeddingBackfillResult(BaseModel):
    """Result of embedding backfill operation."""

    papers_processed: int
    papers_succeeded: int
    papers_failed: int
    errors: list[str] = Field(default_factory=list)


class EmbeddingStats(BaseModel):
    """Statistics about paper embeddings."""

    total_papers: int
    with_embedding: int
    without_embedding: int
    embedding_coverage: float = Field(description="Percentage of papers with embeddings")
