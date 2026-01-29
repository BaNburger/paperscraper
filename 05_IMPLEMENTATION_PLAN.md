# Paper Scraper - Implementation Plan

> **Purpose**: This document serves as a detailed instruction guide for Claude Code to implement the Paper Scraper platform sprint by sprint. Each sprint contains specific files to create, code patterns to follow, and verification steps.

---

## Overview

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 1 | Foundation & Auth | 2 weeks | ✅ Complete |
| 2 | Papers & Ingestion | 2 weeks | ✅ Complete |
| 3 | AI Scoring Pipeline | 2 weeks | ✅ Complete |
| 4 | Projects & KanBan | 2 weeks | ✅ Complete |
| 5 | Search & Discovery | 2 weeks | ✅ Complete |
| 6 | Frontend MVP | 2 weeks | ✅ Complete |

### Phase 2: Feature Completion (Sprints 7-12)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 7 | Production Hardening + One-Line Pitch | 2 weeks | 🔲 Pending |
| 8 | Ingestion Expansion (PubMed, arXiv, PDF) | 2 weeks | 🔲 Pending |
| 9 | Scoring Enhancements + Author Intelligence Start | 2 weeks | 🔲 Pending |
| 10 | Author Intelligence Complete | 2 weeks | 🔲 Pending |
| 11 | Search & Discovery Enhancements | 2 weeks | 🔲 Pending |
| 12 | Analytics & Export | 2 weeks | 🔲 Pending |

### Phase 3: Beta Readiness (Sprints 13-15)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 13 | User Management & Email Infrastructure | 2 weeks | 🔲 Pending |
| 14 | UX Polish & Onboarding | 2 weeks | 🔲 Pending |
| 15 | Deployment & Quality Assurance | 2 weeks | 🔲 Pending |

---

## Sprint 1: Foundation & Auth ✅ COMPLETE

### Completed Items

All Sprint 1 tasks have been implemented:

1. **Repository Scaffolding**
   - [pyproject.toml](pyproject.toml) with all dependencies
   - [docker-compose.yml](docker-compose.yml) (PostgreSQL, Redis, MinIO)
   - [.env.example](.env.example) with all environment variables
   - [Dockerfile](Dockerfile) for API container

2. **Core Module**
   - [paper_scraper/core/config.py](paper_scraper/core/config.py) - Pydantic Settings
   - [paper_scraper/core/database.py](paper_scraper/core/database.py) - Async SQLAlchemy
   - [paper_scraper/core/security.py](paper_scraper/core/security.py) - JWT + password hashing
   - [paper_scraper/core/exceptions.py](paper_scraper/core/exceptions.py) - Custom exceptions

3. **Auth Module**
   - [paper_scraper/modules/auth/models.py](paper_scraper/modules/auth/models.py) - User, Organization
   - [paper_scraper/modules/auth/schemas.py](paper_scraper/modules/auth/schemas.py) - Pydantic schemas
   - [paper_scraper/modules/auth/service.py](paper_scraper/modules/auth/service.py) - Business logic
   - [paper_scraper/modules/auth/router.py](paper_scraper/modules/auth/router.py) - FastAPI endpoints

4. **API Layer**
   - [paper_scraper/api/main.py](paper_scraper/api/main.py) - FastAPI app
   - [paper_scraper/api/dependencies.py](paper_scraper/api/dependencies.py) - DI (get_db, get_current_user)

5. **Tests** - 15 tests passing
   - [tests/conftest.py](tests/conftest.py) - pytest fixtures
   - [tests/test_auth.py](tests/test_auth.py) - Auth module tests

6. **Migrations**
   - [alembic/versions/20260128_2221_51fca12defc7_initial_auth_models.py](alembic/versions/20260128_2221_51fca12defc7_initial_auth_models.py)

---

## Sprint 2: Papers & Ingestion ✅ COMPLETE

### Completed Items

All Sprint 2 tasks have been implemented:

1. **Paper Models & Migration (Task 2.1)**
   - [paper_scraper/modules/papers/models.py](paper_scraper/modules/papers/models.py) - Paper, Author, PaperAuthor models
   - [alembic/versions/20260129_0001_a1b2c3d4e5f6_add_papers_and_authors.py](alembic/versions/20260129_0001_a1b2c3d4e5f6_add_papers_and_authors.py) - Migration with pgvector HNSW index

2. **External API Clients (Task 2.2)**
   - [paper_scraper/modules/papers/clients/base.py](paper_scraper/modules/papers/clients/base.py) - Abstract base client
   - [paper_scraper/modules/papers/clients/openalex.py](paper_scraper/modules/papers/clients/openalex.py) - OpenAlex API client
   - [paper_scraper/modules/papers/clients/crossref.py](paper_scraper/modules/papers/clients/crossref.py) - Crossref API client

3. **Paper Schemas (Task 2.3)**
   - [paper_scraper/modules/papers/schemas.py](paper_scraper/modules/papers/schemas.py) - Pydantic schemas for papers

4. **Paper Service (Task 2.4)**
   - [paper_scraper/modules/papers/service.py](paper_scraper/modules/papers/service.py) - Business logic with CRUD and ingestion

5. **Paper Router (Task 2.5)**
   - [paper_scraper/modules/papers/router.py](paper_scraper/modules/papers/router.py) - FastAPI endpoints

6. **Background Jobs (Task 2.7)**
   - [paper_scraper/jobs/ingestion.py](paper_scraper/jobs/ingestion.py) - arq task for async OpenAlex ingestion
   - Updated [paper_scraper/jobs/worker.py](paper_scraper/jobs/worker.py) with ingest_openalex_task

7. **Tests (Task 2.8)** - 15 new tests (30 total)
   - [tests/test_papers.py](tests/test_papers.py) - Paper module tests

### API Endpoints Implemented
- `GET /api/v1/papers/` - List papers with pagination and search
- `GET /api/v1/papers/{id}` - Get paper detail with authors
- `DELETE /api/v1/papers/{id}` - Delete paper
- `POST /api/v1/papers/ingest/doi` - Import paper by DOI
- `POST /api/v1/papers/ingest/openalex` - Batch import from OpenAlex
- `POST /api/v1/papers/ingest/openalex/async` - Async batch import via arq

---

### Original Sprint 2 Plan (Reference)

#### Goal
Implement paper data model and integrate with external APIs (OpenAlex, Crossref, arXiv, PubMed) for paper ingestion.

### Task 2.1: Paper Models & Migration

**Create directory structure:**
```
paper_scraper/modules/papers/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
```

**File: paper_scraper/modules/papers/__init__.py**
```python
"""Papers module for paper management and ingestion."""
```

**File: paper_scraper/modules/papers/models.py**
```python
"""SQLAlchemy models for papers module."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Index, Integer,
    JSON, String, Text, Uuid, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base

if TYPE_CHECKING:
    from paper_scraper.modules.auth.models import Organization


class PaperSource(str, enum.Enum):
    """Source from which paper was imported."""
    DOI = "doi"
    OPENALEX = "openalex"
    PUBMED = "pubmed"
    ARXIV = "arxiv"
    CROSSREF = "crossref"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    MANUAL = "manual"
    PDF = "pdf"


class Paper(Base):
    """Paper model representing a scientific publication."""

    __tablename__ = "papers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identifiers
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[PaperSource] = mapped_column(Enum(PaperSource), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Core metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    volume: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issue: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pages: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Extended metadata
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    mesh_terms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    references_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citations_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Content
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Vector embedding (1536d for OpenAI text-embedding-3-small)
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)

    # Raw API response for debugging
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    authors: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_papers_source_source_id", "source", "source_id"),
        Index("ix_papers_org_created", "organization_id", "created_at"),
    )


class Author(Base):
    """Author model representing a researcher."""

    __tablename__ = "authors"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # Identifiers
    orcid: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    openalex_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    # Profile
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    affiliations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Metrics
    h_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    works_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Vector embedding for author similarity (768d)
    embedding: Mapped[list | None] = mapped_column(Vector(768), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    papers: Mapped[list["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="author"
    )


class PaperAuthor(Base):
    """Association table for paper-author relationship."""

    __tablename__ = "paper_authors"

    paper_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_corresponding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="authors")
    author: Mapped["Author"] = relationship("Author", back_populates="papers")
```

**Alembic Migration:**
```bash
alembic revision --autogenerate -m "Add papers and authors models"
```

Then manually add to the migration:
```python
# At the top of upgrade():
op.execute('CREATE EXTENSION IF NOT EXISTS vector')

# After creating papers table, add HNSW index:
op.execute('''
    CREATE INDEX ix_papers_embedding ON papers
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
''')

# Add trigram indexes for full-text search:
op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
op.execute('CREATE INDEX ix_papers_title_trgm ON papers USING gin (title gin_trgm_ops)')
op.execute('CREATE INDEX ix_papers_abstract_trgm ON papers USING gin (abstract gin_trgm_ops)')
```

---

### Task 2.2: External API Clients

**Create directory structure:**
```
paper_scraper/modules/papers/clients/
├── __init__.py
├── base.py
├── openalex.py
├── crossref.py
├── pubmed.py
└── arxiv.py
```

**File: paper_scraper/modules/papers/clients/__init__.py**
```python
"""External API clients for paper data sources."""

from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.clients.crossref import CrossrefClient

__all__ = ["OpenAlexClient", "CrossrefClient"]
```

**File: paper_scraper/modules/papers/clients/base.py**
```python
"""Base class for external API clients."""

from abc import ABC, abstractmethod

import httpx


class BaseAPIClient(ABC):
    """Abstract base class for external API clients."""

    def __init__(self, timeout: float = 30.0):
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @abstractmethod
    async def search(self, query: str, max_results: int = 100) -> list[dict]:
        """Search for papers."""
        pass

    @abstractmethod
    async def get_by_id(self, identifier: str) -> dict | None:
        """Get paper by identifier."""
        pass

    @abstractmethod
    def normalize(self, raw_data: dict) -> dict:
        """Normalize API response to standard paper format."""
        pass
```

**File: paper_scraper/modules/papers/clients/openalex.py**
```python
"""OpenAlex API client - Primary data source."""

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient


class OpenAlexClient(BaseAPIClient):
    """
    Client for OpenAlex API.

    - Free, no API key required
    - Email for polite pool (higher rate limits)
    - 100k requests/day limit

    Docs: https://docs.openalex.org/
    """

    def __init__(self):
        super().__init__()
        self.base_url = settings.OPENALEX_BASE_URL
        self.email = settings.OPENALEX_EMAIL

    async def search(
        self,
        query: str,
        max_results: int = 100,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Search OpenAlex for papers.

        Args:
            query: Search query string
            max_results: Maximum results (max 200 per page)
            filters: OpenAlex filters, e.g. {"publication_year": ">2020"}

        Returns:
            List of normalized paper dicts
        """
        papers = []
        per_page = min(max_results, 200)

        params = {
            "search": query,
            "per_page": per_page,
            "mailto": self.email,
        }

        if filters:
            filter_parts = [f"{k}:{v}" for k, v in filters.items()]
            params["filter"] = ",".join(filter_parts)

        response = await self.client.get(
            f"{self.base_url}/works",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        for work in data.get("results", []):
            papers.append(self.normalize(work))
            if len(papers) >= max_results:
                break

        return papers

    async def get_by_id(self, openalex_id: str) -> dict | None:
        """Get paper by OpenAlex ID (e.g., 'W2741809807')."""
        response = await self.client.get(
            f"{self.base_url}/works/{openalex_id}",
            params={"mailto": self.email},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self.normalize(response.json())

    async def get_by_doi(self, doi: str) -> dict | None:
        """Get paper by DOI."""
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        response = await self.client.get(
            f"{self.base_url}/works/doi:{doi}",
            params={"mailto": self.email},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self.normalize(response.json())

    def normalize(self, work: dict) -> dict:
        """Normalize OpenAlex work to standard format."""
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            authors.append({
                "name": author.get("display_name", "Unknown"),
                "orcid": author.get("orcid"),
                "openalex_id": author.get("id"),
                "affiliations": [
                    inst.get("display_name")
                    for inst in authorship.get("institutions", [])
                    if inst.get("display_name")
                ],
                "is_corresponding": authorship.get("is_corresponding", False),
            })

        # Extract venue/journal
        venue = work.get("primary_location", {}) or {}
        source = venue.get("source", {}) or {}

        # Clean DOI
        doi = work.get("doi")
        if doi:
            doi = doi.replace("https://doi.org/", "")

        return {
            "source": "openalex",
            "source_id": work.get("id"),
            "doi": doi,
            "title": work.get("title") or "Untitled",
            "abstract": work.get("abstract"),
            "publication_date": work.get("publication_date"),
            "journal": source.get("display_name"),
            "volume": work.get("biblio", {}).get("volume"),
            "issue": work.get("biblio", {}).get("issue"),
            "pages": self._format_pages(work.get("biblio", {})),
            "keywords": [
                kw.get("display_name")
                for kw in work.get("keywords", [])
                if kw.get("display_name")
            ],
            "references_count": work.get("referenced_works_count"),
            "citations_count": work.get("cited_by_count"),
            "authors": authors,
            "raw_metadata": work,
        }

    def _format_pages(self, biblio: dict) -> str | None:
        """Format page range from biblio dict."""
        first = biblio.get("first_page")
        last = biblio.get("last_page")
        if first and last:
            return f"{first}-{last}"
        return first or last
```

**File: paper_scraper/modules/papers/clients/crossref.py**
```python
"""Crossref API client - DOI resolution fallback."""

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient


class CrossrefClient(BaseAPIClient):
    """
    Client for Crossref API.

    - Free, email for polite pool
    - 50 req/s in polite pool

    Docs: https://api.crossref.org/
    """

    def __init__(self):
        super().__init__()
        self.base_url = settings.CROSSREF_BASE_URL
        self.email = settings.CROSSREF_EMAIL

    async def search(self, query: str, max_results: int = 100) -> list[dict]:
        """Search Crossref for papers."""
        response = await self.client.get(
            f"{self.base_url}/works",
            params={
                "query": query,
                "rows": min(max_results, 1000),
                "mailto": self.email,
            },
        )
        response.raise_for_status()
        data = response.json()

        return [
            self.normalize(item)
            for item in data.get("message", {}).get("items", [])
        ]

    async def get_by_id(self, doi: str) -> dict | None:
        """Get paper by DOI from Crossref."""
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        response = await self.client.get(
            f"{self.base_url}/works/{doi}",
            params={"mailto": self.email},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self.normalize(response.json().get("message", {}))

    def normalize(self, item: dict) -> dict:
        """Normalize Crossref item to standard format."""
        # Extract authors
        authors = []
        for author in item.get("author", []):
            name = f"{author.get('given', '')} {author.get('family', '')}".strip()
            authors.append({
                "name": name or "Unknown",
                "orcid": author.get("ORCID"),
                "affiliations": [
                    aff.get("name")
                    for aff in author.get("affiliation", [])
                    if aff.get("name")
                ],
            })

        # Extract publication date
        pub_date = self._extract_date(item)

        # Extract title
        title = item.get("title", ["Untitled"])
        if isinstance(title, list):
            title = title[0] if title else "Untitled"

        # Extract journal
        journal = item.get("container-title", [""])
        if isinstance(journal, list):
            journal = journal[0] if journal else None

        return {
            "source": "crossref",
            "source_id": item.get("DOI"),
            "doi": item.get("DOI"),
            "title": title,
            "abstract": item.get("abstract"),
            "publication_date": pub_date,
            "journal": journal,
            "volume": item.get("volume"),
            "issue": item.get("issue"),
            "pages": item.get("page"),
            "keywords": item.get("subject", []),
            "references_count": item.get("references-count"),
            "citations_count": item.get("is-referenced-by-count"),
            "authors": authors,
            "raw_metadata": item,
        }

    def _extract_date(self, item: dict) -> str | None:
        """Extract publication date from Crossref item."""
        for date_field in ["published-print", "published-online", "created"]:
            date_parts = item.get(date_field, {}).get("date-parts", [[]])[0]
            if date_parts:
                year = date_parts[0] if len(date_parts) > 0 else 2000
                month = date_parts[1] if len(date_parts) > 1 else 1
                day = date_parts[2] if len(date_parts) > 2 else 1
                return f"{year}-{month:02d}-{day:02d}"
        return None
```

---

### Task 2.3: Paper Schemas

**File: paper_scraper/modules/papers/schemas.py**
```python
"""Pydantic schemas for papers module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.papers.models import PaperSource


# ============================================================================
# Author Schemas
# ============================================================================

class AuthorBase(BaseModel):
    """Base author schema."""
    name: str
    orcid: str | None = None
    affiliations: list[str] = Field(default_factory=list)


class AuthorResponse(AuthorBase):
    """Author response schema."""
    id: UUID
    openalex_id: str | None = None
    h_index: int | None = None
    citation_count: int | None = None
    works_count: int | None = None

    model_config = {"from_attributes": True}


class PaperAuthorResponse(BaseModel):
    """Paper-author relationship response."""
    author: AuthorResponse
    position: int
    is_corresponding: bool

    model_config = {"from_attributes": True}


# ============================================================================
# Paper Schemas
# ============================================================================

class PaperBase(BaseModel):
    """Base paper schema."""
    title: str
    abstract: str | None = None
    doi: str | None = None
    publication_date: datetime | None = None
    journal: str | None = None
    keywords: list[str] = Field(default_factory=list)


class PaperCreate(PaperBase):
    """Schema for manual paper creation."""
    pass


class PaperResponse(PaperBase):
    """Paper response schema."""
    id: UUID
    organization_id: UUID
    source: PaperSource
    source_id: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    references_count: int | None = None
    citations_count: int | None = None
    has_pdf: bool = False
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaperDetail(PaperResponse):
    """Detailed paper response with authors."""
    authors: list[PaperAuthorResponse] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)


class PaperListResponse(BaseModel):
    """Paginated paper list response."""
    items: list[PaperResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Ingestion Schemas
# ============================================================================

class IngestDOIRequest(BaseModel):
    """Request to ingest paper by DOI."""
    doi: str = Field(..., description="DOI of the paper to import")


class IngestOpenAlexRequest(BaseModel):
    """Request to batch ingest from OpenAlex."""
    query: str = Field(..., description="Search query for OpenAlex")
    max_results: int = Field(default=100, ge=1, le=1000)
    filters: dict = Field(default_factory=dict)


class IngestJobResponse(BaseModel):
    """Response for async ingestion job."""
    job_id: str
    status: str = "queued"
    message: str


class IngestResult(BaseModel):
    """Result of ingestion operation."""
    papers_created: int
    papers_updated: int
    papers_skipped: int
    errors: list[str] = Field(default_factory=list)
```

---

### Task 2.4: Paper Service

**File: paper_scraper/modules/papers/service.py**
```python
"""Service layer for papers module."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import DuplicateError, NotFoundError
from paper_scraper.modules.papers.clients.crossref import CrossrefClient
from paper_scraper.modules.papers.clients.openalex import OpenAlexClient
from paper_scraper.modules.papers.models import Author, Paper, PaperAuthor, PaperSource
from paper_scraper.modules.papers.schemas import IngestResult, PaperListResponse


class PaperService:
    """Service for paper management and ingestion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Paper CRUD
    # =========================================================================

    async def get_paper(
        self, paper_id: UUID, organization_id: UUID
    ) -> Paper | None:
        """Get paper by ID with tenant isolation."""
        result = await self.db.execute(
            select(Paper)
            .options(
                selectinload(Paper.authors).selectinload(PaperAuthor.author)
            )
            .where(
                Paper.id == paper_id,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_papers(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> PaperListResponse:
        """List papers with pagination and optional search."""
        query = select(Paper).where(Paper.organization_id == organization_id)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                Paper.title.ilike(search_filter) |
                Paper.abstract.ilike(search_filter)
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Paper.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        papers = list(result.scalars().all())

        return PaperListResponse(
            items=papers,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )

    async def get_paper_by_doi(
        self, doi: str, organization_id: UUID
    ) -> Paper | None:
        """Get paper by DOI within organization."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.doi == doi,
                Paper.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Ingestion
    # =========================================================================

    async def ingest_by_doi(
        self, doi: str, organization_id: UUID
    ) -> Paper:
        """
        Ingest paper by DOI.

        Strategy: OpenAlex first (richer metadata), Crossref fallback.
        """
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        # Check if already exists
        existing = await self.get_paper_by_doi(doi, organization_id)
        if existing:
            raise DuplicateError("Paper", "doi", doi)

        paper_data = None

        # Try OpenAlex first (better metadata)
        async with OpenAlexClient() as client:
            paper_data = await client.get_by_doi(doi)

        # Fallback to Crossref
        if not paper_data:
            async with CrossrefClient() as client:
                paper_data = await client.get_by_id(doi)

        if not paper_data:
            raise NotFoundError("Paper", "doi", doi)

        paper = await self._create_paper_from_data(paper_data, organization_id)
        await self.db.commit()
        return paper

    async def ingest_from_openalex(
        self,
        query: str,
        organization_id: UUID,
        max_results: int = 100,
        filters: dict | None = None,
    ) -> IngestResult:
        """Batch ingest papers from OpenAlex search."""
        created = 0
        skipped = 0
        errors: list[str] = []

        async with OpenAlexClient() as client:
            papers_data = await client.search(query, max_results, filters)

        for paper_data in papers_data:
            try:
                doi = paper_data.get("doi")
                if doi:
                    existing = await self.get_paper_by_doi(doi, organization_id)
                    if existing:
                        skipped += 1
                        continue

                await self._create_paper_from_data(paper_data, organization_id)
                created += 1
            except Exception as e:
                title = paper_data.get("title", "unknown")[:50]
                errors.append(f"Error importing '{title}': {str(e)}")

        await self.db.commit()

        return IngestResult(
            papers_created=created,
            papers_updated=0,
            papers_skipped=skipped,
            errors=errors,
        )

    async def _create_paper_from_data(
        self, data: dict, organization_id: UUID
    ) -> Paper:
        """Create paper and authors from normalized API data."""
        # Parse publication date
        pub_date = None
        if data.get("publication_date"):
            from datetime import datetime
            try:
                pub_date = datetime.fromisoformat(data["publication_date"])
            except ValueError:
                pass

        # Create paper
        paper = Paper(
            organization_id=organization_id,
            doi=data.get("doi"),
            source=PaperSource(data["source"]),
            source_id=data.get("source_id"),
            title=data["title"],
            abstract=data.get("abstract"),
            publication_date=pub_date,
            journal=data.get("journal"),
            volume=data.get("volume"),
            issue=data.get("issue"),
            pages=data.get("pages"),
            keywords=data.get("keywords", []),
            references_count=data.get("references_count"),
            citations_count=data.get("citations_count"),
            raw_metadata=data.get("raw_metadata", {}),
        )
        self.db.add(paper)
        await self.db.flush()

        # Create/link authors
        for idx, author_data in enumerate(data.get("authors", [])):
            author = await self._get_or_create_author(author_data)
            paper_author = PaperAuthor(
                paper_id=paper.id,
                author_id=author.id,
                position=idx,
                is_corresponding=author_data.get("is_corresponding", False),
            )
            self.db.add(paper_author)

        await self.db.flush()
        return paper

    async def _get_or_create_author(self, data: dict) -> Author:
        """Get existing author or create new one."""
        # Try to find by ORCID
        if data.get("orcid"):
            result = await self.db.execute(
                select(Author).where(Author.orcid == data["orcid"])
            )
            author = result.scalar_one_or_none()
            if author:
                return author

        # Try to find by OpenAlex ID
        if data.get("openalex_id"):
            result = await self.db.execute(
                select(Author).where(Author.openalex_id == data["openalex_id"])
            )
            author = result.scalar_one_or_none()
            if author:
                return author

        # Create new author
        author = Author(
            name=data["name"],
            orcid=data.get("orcid"),
            openalex_id=data.get("openalex_id"),
            affiliations=data.get("affiliations", []),
        )
        self.db.add(author)
        await self.db.flush()
        return author
```

---

### Task 2.5: Paper Router

**File: paper_scraper/modules/papers/router.py**
```python
"""FastAPI router for papers endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.core.exceptions import NotFoundError
from paper_scraper.modules.papers.schemas import (
    IngestDOIRequest,
    IngestJobResponse,
    IngestOpenAlexRequest,
    IngestResult,
    PaperDetail,
    PaperListResponse,
    PaperResponse,
)
from paper_scraper.modules.papers.service import PaperService

router = APIRouter()


def get_paper_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PaperService:
    """Dependency to get paper service instance."""
    return PaperService(db)


@router.get(
    "/",
    response_model=PaperListResponse,
    summary="List papers",
)
async def list_papers(
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> PaperListResponse:
    """List papers with pagination and optional full-text search."""
    return await paper_service.list_papers(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{paper_id}",
    response_model=PaperDetail,
    summary="Get paper details",
)
async def get_paper(
    paper_id: UUID,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperDetail:
    """Get detailed paper information including authors."""
    paper = await paper_service.get_paper(paper_id, current_user.organization_id)
    if not paper:
        raise NotFoundError("Paper", "id", str(paper_id))
    return paper  # type: ignore


@router.post(
    "/ingest/doi",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import paper by DOI",
)
async def ingest_by_doi(
    request: IngestDOIRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperResponse:
    """
    Import a single paper by DOI.

    Fetches metadata from OpenAlex (primary) or Crossref (fallback).
    """
    paper = await paper_service.ingest_by_doi(
        doi=request.doi,
        organization_id=current_user.organization_id,
    )
    return paper  # type: ignore


@router.post(
    "/ingest/openalex",
    response_model=IngestResult,
    status_code=status.HTTP_200_OK,
    summary="Batch import from OpenAlex",
)
async def ingest_from_openalex(
    request: IngestOpenAlexRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> IngestResult:
    """
    Synchronous batch import from OpenAlex.

    For large imports (>100 papers), use the async job endpoint.
    """
    return await paper_service.ingest_from_openalex(
        query=request.query,
        organization_id=current_user.organization_id,
        max_results=request.max_results,
        filters=request.filters,
    )


@router.post(
    "/ingest/openalex/async",
    response_model=IngestJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Async batch import from OpenAlex",
)
async def ingest_from_openalex_async(
    request: IngestOpenAlexRequest,
    current_user: CurrentUser,
) -> IngestJobResponse:
    """
    Start async batch import from OpenAlex via arq job queue.

    Returns job ID for progress tracking.
    """
    import arq
    from paper_scraper.core.config import settings

    redis = await arq.create_pool(settings.arq_redis_settings)
    job = await redis.enqueue_job(
        "ingest_openalex_task",
        str(current_user.organization_id),
        request.query,
        request.max_results,
        request.filters,
    )

    return IngestJobResponse(
        job_id=job.job_id,
        status="queued",
        message=f"Ingestion job queued for query: {request.query}",
    )
```

---

### Task 2.6: Register Papers Router

**Update paper_scraper/api/v1/router.py:**
```python
"""API v1 router."""

from fastapi import APIRouter

from paper_scraper.modules.auth.router import router as auth_router
from paper_scraper.modules.papers.router import router as papers_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(papers_router, prefix="/papers", tags=["papers"])
```

---

### Task 2.7: arq Background Jobs

**File: paper_scraper/jobs/__init__.py**
```python
"""Background jobs module."""
```

**File: paper_scraper/jobs/ingestion.py**
```python
"""Background tasks for paper ingestion."""

from uuid import UUID

from paper_scraper.core.database import get_async_session
from paper_scraper.modules.papers.service import PaperService


async def ingest_openalex_task(
    ctx: dict,
    organization_id: str,
    query: str,
    max_results: int = 100,
    filters: dict | None = None,
) -> dict:
    """
    arq task: Ingest papers from OpenAlex.

    Args:
        ctx: arq context (contains redis connection)
        organization_id: UUID string of organization
        query: OpenAlex search query
        max_results: Maximum papers to import
        filters: Optional OpenAlex filters

    Returns:
        Ingestion result dict
    """
    org_id = UUID(organization_id)

    async with get_async_session() as db:
        service = PaperService(db)
        result = await service.ingest_from_openalex(
            query=query,
            organization_id=org_id,
            max_results=max_results,
            filters=filters,
        )
        return result.model_dump()
```

**File: paper_scraper/jobs/worker.py**
```python
"""arq worker configuration."""

import arq

from paper_scraper.core.config import settings
from paper_scraper.jobs.ingestion import ingest_openalex_task


class WorkerSettings:
    """arq worker settings."""

    functions = [
        ingest_openalex_task,
    ]

    redis_settings = settings.arq_redis_settings
    max_jobs = 10
    job_timeout = 600  # 10 minutes
```

**Update paper_scraper/core/database.py** - Add context manager:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_session():
    """Context manager for async session (for background jobs)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

### Task 2.8: Tests

**File: tests/test_papers.py**
```python
"""Tests for papers module."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.modules.papers.models import Paper, PaperSource


class TestPaperEndpoints:
    """Test paper API endpoints."""

    async def test_list_papers_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing papers when none exist."""
        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    async def test_list_papers_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_user,
    ):
        """Test listing papers with data."""
        # Create test paper
        paper = Paper(
            organization_id=test_user.organization_id,
            title="Test Paper",
            abstract="Test abstract",
            source=PaperSource.MANUAL,
        )
        db.add(paper)
        await db.commit()

        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Test Paper"

    async def test_get_paper_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent paper."""
        import uuid
        response = await client.get(
            f"/api/v1/papers/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestOpenAlexClient:
    """Test OpenAlex API client."""

    @pytest.mark.asyncio
    async def test_normalize(self):
        """Test OpenAlex data normalization."""
        from paper_scraper.modules.papers.clients.openalex import OpenAlexClient

        client = OpenAlexClient()
        raw = {
            "id": "W123456789",
            "title": "Machine Learning for Science",
            "doi": "https://doi.org/10.1234/test.123",
            "abstract": "This paper explores...",
            "publication_date": "2024-01-15",
            "authorships": [
                {
                    "author": {
                        "display_name": "Jane Doe",
                        "orcid": "0000-0001-2345-6789",
                    },
                    "institutions": [{"display_name": "MIT"}],
                    "is_corresponding": True,
                }
            ],
            "primary_location": {
                "source": {"display_name": "Nature"}
            },
            "cited_by_count": 42,
        }

        normalized = client.normalize(raw)

        assert normalized["title"] == "Machine Learning for Science"
        assert normalized["doi"] == "10.1234/test.123"
        assert normalized["source"] == "openalex"
        assert len(normalized["authors"]) == 1
        assert normalized["authors"][0]["name"] == "Jane Doe"
        assert normalized["authors"][0]["is_corresponding"] is True
        assert normalized["citations_count"] == 42


class TestCrossrefClient:
    """Test Crossref API client."""

    @pytest.mark.asyncio
    async def test_normalize(self):
        """Test Crossref data normalization."""
        from paper_scraper.modules.papers.clients.crossref import CrossrefClient

        client = CrossrefClient()
        raw = {
            "DOI": "10.1234/test.456",
            "title": ["Deep Learning Applications"],
            "abstract": "We present...",
            "author": [
                {
                    "given": "John",
                    "family": "Smith",
                    "affiliation": [{"name": "Stanford"}],
                }
            ],
            "container-title": ["Science"],
            "published-print": {"date-parts": [[2024, 3, 1]]},
            "is-referenced-by-count": 15,
        }

        normalized = client.normalize(raw)

        assert normalized["title"] == "Deep Learning Applications"
        assert normalized["doi"] == "10.1234/test.456"
        assert normalized["source"] == "crossref"
        assert normalized["journal"] == "Science"
        assert normalized["publication_date"] == "2024-03-01"
        assert len(normalized["authors"]) == 1
        assert normalized["authors"][0]["name"] == "John Smith"
```

---

### Sprint 2 Definition of Done

- [ ] Paper and Author models created with migration
- [ ] pgvector extension enabled with HNSW index
- [ ] OpenAlex client working (search, get_by_doi)
- [ ] Crossref client working (get_by_id)
- [ ] Paper service with CRUD and ingestion
- [ ] API endpoints registered and functional:
  - [ ] `GET /api/v1/papers/` - list papers
  - [ ] `GET /api/v1/papers/{id}` - get paper detail
  - [ ] `POST /api/v1/papers/ingest/doi` - import by DOI
  - [ ] `POST /api/v1/papers/ingest/openalex` - batch import
- [ ] arq worker configuration with ingestion task
- [ ] Tests passing (>80% coverage for papers module)
- [ ] DOI import creates paper with authors in database

---

## Sprint 3: AI Scoring Pipeline ✅ COMPLETE

### Completed Items

All Sprint 3 tasks have been implemented:

1. **LLM Client Abstraction**
   - [paper_scraper/modules/scoring/llm_client.py](paper_scraper/modules/scoring/llm_client.py) - Provider-agnostic LLM abstraction
   - Supports OpenAI, Anthropic, Azure, and Ollama providers
   - JSON mode for structured output

2. **Embedding Generation**
   - [paper_scraper/modules/scoring/embeddings.py](paper_scraper/modules/scoring/embeddings.py) - Embedding generation
   - Uses text-embedding-3-small (1536 dimensions)
   - Batch embedding support

3. **Jinja2 Prompt Templates**
   - [paper_scraper/modules/scoring/prompts/novelty.jinja2](paper_scraper/modules/scoring/prompts/novelty.jinja2)
   - [paper_scraper/modules/scoring/prompts/ip_potential.jinja2](paper_scraper/modules/scoring/prompts/ip_potential.jinja2)
   - [paper_scraper/modules/scoring/prompts/marketability.jinja2](paper_scraper/modules/scoring/prompts/marketability.jinja2)
   - [paper_scraper/modules/scoring/prompts/feasibility.jinja2](paper_scraper/modules/scoring/prompts/feasibility.jinja2)
   - [paper_scraper/modules/scoring/prompts/commercialization.jinja2](paper_scraper/modules/scoring/prompts/commercialization.jinja2)

4. **Scoring Dimension Classes**
   - [paper_scraper/modules/scoring/dimensions/base.py](paper_scraper/modules/scoring/dimensions/base.py) - Base dimension class
   - [paper_scraper/modules/scoring/dimensions/novelty.py](paper_scraper/modules/scoring/dimensions/novelty.py)
   - [paper_scraper/modules/scoring/dimensions/ip_potential.py](paper_scraper/modules/scoring/dimensions/ip_potential.py)
   - [paper_scraper/modules/scoring/dimensions/marketability.py](paper_scraper/modules/scoring/dimensions/marketability.py)
   - [paper_scraper/modules/scoring/dimensions/feasibility.py](paper_scraper/modules/scoring/dimensions/feasibility.py)
   - [paper_scraper/modules/scoring/dimensions/commercialization.py](paper_scraper/modules/scoring/dimensions/commercialization.py)

5. **Scoring Orchestrator**
   - [paper_scraper/modules/scoring/orchestrator.py](paper_scraper/modules/scoring/orchestrator.py) - Parallel scoring with asyncio.gather
   - Configurable weights for each dimension
   - Weighted overall score calculation

6. **Models & Migration**
   - [paper_scraper/modules/scoring/models.py](paper_scraper/modules/scoring/models.py) - PaperScore, ScoringJob models
   - [alembic/versions/20260129_0002_b2c3d4e5f6g7_add_scoring_models.py](alembic/versions/20260129_0002_b2c3d4e5f6g7_add_scoring_models.py) - Migration

7. **Schemas & Service**
   - [paper_scraper/modules/scoring/schemas.py](paper_scraper/modules/scoring/schemas.py) - Pydantic schemas
   - [paper_scraper/modules/scoring/service.py](paper_scraper/modules/scoring/service.py) - Business logic

8. **API Router**
   - [paper_scraper/modules/scoring/router.py](paper_scraper/modules/scoring/router.py) - FastAPI endpoints

9. **Background Jobs**
   - [paper_scraper/jobs/scoring.py](paper_scraper/jobs/scoring.py) - arq tasks for scoring
   - Updated [paper_scraper/jobs/worker.py](paper_scraper/jobs/worker.py) with scoring tasks

10. **Tests** - 25+ new tests
    - [tests/test_scoring.py](tests/test_scoring.py) - Scoring module tests with mocked LLM responses

### API Endpoints Implemented
- `POST /api/v1/scoring/papers/{id}/score` - Score a paper
- `GET /api/v1/scoring/papers/{id}/scores` - Get paper score history
- `GET /api/v1/scoring/papers/{id}/scores/latest` - Get latest score
- `GET /api/v1/scoring/` - List all scores (with filters)
- `POST /api/v1/scoring/batch` - Start batch scoring job
- `GET /api/v1/scoring/jobs` - List scoring jobs
- `GET /api/v1/scoring/jobs/{id}` - Get job status
- `POST /api/v1/scoring/papers/{id}/embedding` - Generate paper embedding
- `POST /api/v1/scoring/embeddings/backfill` - Backfill embeddings

### Scoring Dimensions
| Dimension | Description |
|-----------|-------------|
| **Novelty** | Technological newness vs. state-of-the-art |
| **IP Potential** | Patentability, prior art risk, claim scope |
| **Marketability** | Market size, industry relevance, trends |
| **Feasibility** | TRL level, time-to-market, development cost |
| **Commercialization** | Recommended path, entry barriers, strategic value |

---

### Original Sprint 3 Plan (Reference)

#### Goal
Implement the 5-dimensional AI scoring system with LLM integration.

#### Key Files to Create

```
paper_scraper/modules/scoring/
├── __init__.py
├── llm_client.py           # Provider-agnostic LLM abstraction
├── embeddings.py           # Embedding generation
├── prompts/
│   ├── __init__.py
│   ├── novelty.jinja2
│   ├── ip_potential.jinja2
│   ├── marketability.jinja2
│   ├── feasibility.jinja2
│   └── commercialization.jinja2
├── dimensions/
│   ├── __init__.py
│   ├── base.py
│   ├── novelty.py
│   ├── ip_potential.py
│   ├── marketability.py
│   ├── feasibility.py
│   └── commercialization.py
├── orchestrator.py
├── models.py
├── schemas.py
├── service.py
└── router.py
```

#### Key Implementation Notes

1. **LLM Client**: Use `settings.LLM_PROVIDER` and `settings.LLM_MODEL` for provider-agnostic design
2. **Prompt Templates**: Jinja2 templates in `prompts/` directory
3. **JSON Mode**: Request structured JSON output from LLM
4. **Parallel Scoring**: Score dimensions concurrently with `asyncio.gather`
5. **Caching**: Cache similar papers lookup for repeated scoring

#### Sprint 3 Definition of Done

- [x] LLM client abstraction with OpenAI implementation
- [x] All 5 scoring dimension classes
- [x] Jinja2 prompt templates
- [x] Scoring orchestrator with weighted aggregation
- [x] PaperScore model and migration
- [x] Embedding generation for papers
- [x] API endpoints:
  - [x] `POST /api/v1/scoring/papers/{id}/score` - trigger scoring
  - [x] `GET /api/v1/scoring/papers/{id}/scores` - get scores
- [x] arq task for batch scoring
- [x] Tests with mocked LLM responses

---

## Sprint 4: Projects & KanBan ✅ COMPLETE

### Completed Items

All Sprint 4 tasks have been implemented:

1. **Projects Module**
   - [paper_scraper/modules/projects/__init__.py](paper_scraper/modules/projects/__init__.py) - Module init
   - [paper_scraper/modules/projects/models.py](paper_scraper/modules/projects/models.py) - Project, PaperProjectStatus, PaperStageHistory
   - [paper_scraper/modules/projects/schemas.py](paper_scraper/modules/projects/schemas.py) - Pydantic schemas
   - [paper_scraper/modules/projects/service.py](paper_scraper/modules/projects/service.py) - Business logic
   - [paper_scraper/modules/projects/router.py](paper_scraper/modules/projects/router.py) - FastAPI endpoints

2. **Migration**
   - [alembic/versions/20260129_0003_c3d4e5f6g7h8_add_projects_models.py](alembic/versions/20260129_0003_c3d4e5f6g7h8_add_projects_models.py) - Projects migration

3. **Tests** - 22 new tests (80 total)
   - [tests/test_projects.py](tests/test_projects.py) - Project module tests

### API Endpoints Implemented
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/{id}` - Get project detail
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `GET /api/v1/projects/{id}/kanban` - KanBan board view
- `GET /api/v1/projects/{id}/statistics` - Project statistics
- `POST /api/v1/projects/{id}/papers` - Add paper to project
- `POST /api/v1/projects/{id}/papers/batch` - Batch add papers
- `GET /api/v1/projects/{id}/papers/{paper_id}` - Get paper in project
- `DELETE /api/v1/projects/{id}/papers/{paper_id}` - Remove paper from project
- `PATCH /api/v1/projects/{id}/papers/{paper_id}/move` - Move paper to stage
- `POST /api/v1/projects/{id}/papers/{paper_id}/reject` - Reject paper with reason
- `PATCH /api/v1/projects/{id}/papers/{paper_id}/status` - Update paper status
- `GET /api/v1/projects/{id}/papers/{paper_id}/history` - Get paper stage history

### Key Features
- **Customizable Pipeline Stages**: Projects can define custom stages or use defaults (inbox, screening, evaluation, shortlisted, contacted, rejected, archived)
- **Scoring Weights per Project**: Each project can have custom scoring weights
- **Paper Assignment**: Papers can be assigned to team members
- **Priority & Tags**: Papers have priority levels (1-5) and custom tags
- **Rejection Tracking**: Predefined rejection reasons with notes
- **Stage History**: Full audit trail of paper movements between stages
- **Statistics**: Paper counts by stage, priority distribution, rejection reasons

### Sprint 4 Definition of Done

- [x] Project model with customizable stages
- [x] PaperProjectStatus for pipeline tracking
- [x] PaperStageHistory for audit trail
- [x] API endpoints:
  - [x] `GET /api/v1/projects/` - list projects
  - [x] `POST /api/v1/projects/` - create project
  - [x] `GET /api/v1/projects/{id}/kanban` - KanBan view
  - [x] `PATCH /api/v1/projects/{id}/papers/{paper_id}/move` - move paper
- [x] Rejection tracking with reasons
- [x] Tests for project workflows (22 tests)

---

## Sprint 5: Search & Discovery ✅ COMPLETE

### Completed Items

All Sprint 5 tasks have been implemented:

1. **Search Module**
   - [paper_scraper/modules/search/__init__.py](paper_scraper/modules/search/__init__.py) - Module init
   - [paper_scraper/modules/search/schemas.py](paper_scraper/modules/search/schemas.py) - Search request/response schemas
   - [paper_scraper/modules/search/service.py](paper_scraper/modules/search/service.py) - Search service with full-text, semantic, and hybrid search
   - [paper_scraper/modules/search/router.py](paper_scraper/modules/search/router.py) - FastAPI endpoints

2. **Search Types**
   - **Full-text search**: PostgreSQL `pg_trgm` trigram similarity on title and abstract
   - **Semantic search**: pgvector cosine distance for embedding similarity
   - **Hybrid search**: Reciprocal Rank Fusion (RRF) combining text and semantic results

3. **Background Jobs**
   - [paper_scraper/jobs/search.py](paper_scraper/jobs/search.py) - arq task for embedding backfill
   - Updated [paper_scraper/jobs/worker.py](paper_scraper/jobs/worker.py) with backfill_embeddings_task

4. **Tests** - 22 new tests (102 total)
   - [tests/test_search.py](tests/test_search.py) - Search module tests

### API Endpoints Implemented
- `POST /api/v1/search/` - Unified search (fulltext, semantic, or hybrid mode)
- `GET /api/v1/search/fulltext` - Full-text search with trigram similarity
- `GET /api/v1/search/semantic` - Semantic search using embeddings
- `POST /api/v1/search/similar` - Find similar papers by paper ID
- `GET /api/v1/search/similar/{paper_id}` - Find similar papers (GET version)
- `GET /api/v1/search/embeddings/stats` - Get embedding statistics
- `POST /api/v1/search/embeddings/backfill` - Start async embedding backfill job
- `POST /api/v1/search/embeddings/backfill/sync` - Synchronous embedding backfill

### Search Features
- **Search Modes**: fulltext, semantic, hybrid (default)
- **Filters**: sources, min/max score, date range, journals, keywords, has_embedding, has_score
- **Highlights**: Text snippets showing query matches in title and abstract
- **Scoring**: Results include relevance scores and paper scoring data
- **Pagination**: Full pagination support with configurable page size
- **Tenant Isolation**: All searches scoped to organization

### Hybrid Search with RRF
The hybrid search uses Reciprocal Rank Fusion (RRF) to combine full-text and semantic results:
- RRF formula: `score = weight_text * 1/(k+rank_text) + weight_semantic * 1/(k+rank_semantic)`
- Default k=60 (RRF constant)
- Configurable semantic_weight (0.0 = text only, 1.0 = semantic only, 0.5 = balanced)

### Sprint 5 Definition of Done

- [x] Full-text search with highlighting
- [x] Semantic search using paper embeddings
- [x] Hybrid search endpoint with RRF
- [x] Embedding backfill job (sync and async)
- [x] Filter by score ranges, date, source
- [x] Tests for search functionality (22 tests)

---

## Sprint 6: Frontend MVP ✅ COMPLETE

### Completed Items

All Sprint 6 tasks have been implemented:

1. **Project Setup**
   - [frontend/vite.config.ts](frontend/vite.config.ts) - Vite + React + TypeScript + Tailwind CSS v4
   - [frontend/package.json](frontend/package.json) - TanStack Query, axios, zod, react-router-dom, @dnd-kit
   - [frontend/src/index.css](frontend/src/index.css) - Tailwind CSS v4 with custom theme

2. **Core Infrastructure**
   - [frontend/src/lib/api.ts](frontend/src/lib/api.ts) - API client with auth interceptors
   - [frontend/src/lib/utils.ts](frontend/src/lib/utils.ts) - Utility functions (cn, formatDate, etc.)
   - [frontend/src/types/index.ts](frontend/src/types/index.ts) - TypeScript types matching backend API

3. **Auth & Context**
   - [frontend/src/contexts/AuthContext.tsx](frontend/src/contexts/AuthContext.tsx) - Authentication context
   - [frontend/src/components/ProtectedRoute.tsx](frontend/src/components/ProtectedRoute.tsx) - Route protection

4. **Custom Hooks**
   - [frontend/src/hooks/usePapers.ts](frontend/src/hooks/usePapers.ts) - Paper operations
   - [frontend/src/hooks/useProjects.ts](frontend/src/hooks/useProjects.ts) - Project operations
   - [frontend/src/hooks/useSearch.ts](frontend/src/hooks/useSearch.ts) - Search operations

5. **UI Components**
   - [frontend/src/components/ui/](frontend/src/components/ui/) - Button, Input, Card, Badge, Label
   - [frontend/src/components/layout/](frontend/src/components/layout/) - Layout, Navbar, Sidebar

6. **Pages**
   - [frontend/src/pages/LoginPage.tsx](frontend/src/pages/LoginPage.tsx) - Login form
   - [frontend/src/pages/RegisterPage.tsx](frontend/src/pages/RegisterPage.tsx) - Registration form
   - [frontend/src/pages/DashboardPage.tsx](frontend/src/pages/DashboardPage.tsx) - Dashboard with stats
   - [frontend/src/pages/PapersPage.tsx](frontend/src/pages/PapersPage.tsx) - Paper list with search/pagination
   - [frontend/src/pages/PaperDetailPage.tsx](frontend/src/pages/PaperDetailPage.tsx) - Paper detail with score visualization
   - [frontend/src/pages/ProjectsPage.tsx](frontend/src/pages/ProjectsPage.tsx) - Project list
   - [frontend/src/pages/ProjectKanbanPage.tsx](frontend/src/pages/ProjectKanbanPage.tsx) - KanBan board with drag-and-drop
   - [frontend/src/pages/SearchPage.tsx](frontend/src/pages/SearchPage.tsx) - Full-text/semantic/hybrid search

7. **App Routing**
   - [frontend/src/App.tsx](frontend/src/App.tsx) - React Router with protected routes

### Key Features
- **Authentication**: JWT-based login/register with protected routes
- **Papers**: List, search, pagination, DOI/OpenAlex import, detail view with scores
- **Scoring**: 5-dimension radar visualization with reasoning
- **Projects**: CRUD operations, KanBan board with drag-and-drop (@dnd-kit)
- **Search**: Full-text, semantic, and hybrid search modes
- **Responsive**: Mobile-friendly layout with sidebar navigation

### Sprint 6 Definition of Done

- [x] Authentication flow working
- [x] Paper list with search and pagination
- [x] Paper detail with score visualization
- [x] KanBan board with drag-and-drop
- [x] Responsive design
- [x] Loading and error states

---

## Quick Reference

### Commands

```bash
# Development
docker-compose up -d          # Start services
pytest tests/ -v              # Run tests
alembic upgrade head          # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration

# arq Worker
arq paper_scraper.jobs.worker.WorkerSettings

# Code Quality
ruff format .                 # Format code
ruff check .                  # Lint
mypy paper_scraper/           # Type check
```

### Adding New Endpoint

1. Schema: `modules/<feature>/schemas.py`
2. Service: `modules/<feature>/service.py`
3. Router: `modules/<feature>/router.py`
4. Register: `api/v1/router.py`
5. Test: `tests/test_<feature>.py`

### Adding New arq Job

1. Task: `jobs/<task>.py` (async function)
2. Register: `jobs/worker.py` WorkerSettings.functions
3. Queue: `await redis.enqueue_job("task_name", *args)`

---

# Phase 2: Feature Completion (Sprints 7-12)

---

## Sprint 7: Production Hardening + One-Line Pitch Generator

### Goal
Make the platform production-ready with observability (Langfuse, Sentry) and implement the highest-value feature: one-line pitch generation for papers.

### Task 7.1: Langfuse LLM Monitoring Integration

**Update file: paper_scraper/modules/scoring/llm_client.py**

Wrap all LLM calls with Langfuse tracing:

```python
"""LLM client with Langfuse observability."""

from langfuse import Langfuse
from langfuse.decorators import observe

from paper_scraper.core.config import settings

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
    enabled=bool(settings.LANGFUSE_PUBLIC_KEY),
)


class LLMClient:
    """Provider-agnostic LLM client with observability."""

    @observe(as_type="generation")
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        json_mode: bool = False,
    ) -> str:
        """Complete prompt with LLM, tracked by Langfuse."""
        # ... existing implementation ...
        # Langfuse will automatically track:
        # - Prompt content
        # - Model used
        # - Latency
        # - Token usage
        # - Cost estimation
```

**Add to pyproject.toml:**
```toml
langfuse = "^2.0"
```

---

### Task 7.2: Sentry Error Tracking

**Update file: paper_scraper/api/main.py**

```python
"""FastAPI application with Sentry integration."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from paper_scraper.core.config import settings

# Initialize Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,
    )

# ... rest of app setup ...
```

---

### Task 7.3: Rate Limiting Middleware

**Create file: paper_scraper/api/middleware.py**

```python
"""API middleware for rate limiting and security."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from paper_scraper.core.config import settings

# Create limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"],
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
)


def get_rate_limit_key(request):
    """Get rate limit key based on user or IP."""
    # If authenticated, use user ID; otherwise IP
    auth = request.headers.get("Authorization")
    if auth:
        # Extract user from token for per-user limits
        return f"user:{request.state.user_id}" if hasattr(request.state, "user_id") else get_remote_address(request)
    return get_remote_address(request)
```

**Update paper_scraper/api/main.py:**
```python
from paper_scraper.api.middleware import limiter, SlowAPIMiddleware

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
```

**Apply to scoring endpoint (expensive operation):**
```python
from paper_scraper.api.middleware import limiter

@router.post("/papers/{paper_id}/score")
@limiter.limit(f"{settings.RATE_LIMIT_SCORING_PER_MINUTE}/minute")
async def score_paper(request: Request, paper_id: UUID, ...):
    ...
```

---

### Task 7.4: API Startup/Shutdown Handlers

**Update file: paper_scraper/api/main.py**

```python
"""FastAPI app with proper lifecycle management."""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
import redis.asyncio as redis

from paper_scraper.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting Paper Scraper API...")

    # Initialize database connection pool
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )
    app.state.db_engine = engine

    # Initialize Redis connection pool
    app.state.redis = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    await app.state.redis.ping()
    print("✅ Redis connected")

    # Check MinIO bucket exists
    from paper_scraper.core.storage import ensure_bucket_exists
    await ensure_bucket_exists(settings.S3_BUCKET_NAME)
    print("✅ S3 bucket verified")

    yield

    # Shutdown
    print("🛑 Shutting down Paper Scraper API...")
    await app.state.redis.close()
    await engine.dispose()
    print("✅ Cleanup complete")


app = FastAPI(
    title="Paper Scraper API",
    lifespan=lifespan,
    # ...
)
```

---

### Task 7.5: Structured Logging

**Create file: paper_scraper/core/logging.py**

```python
"""Structured JSON logging configuration."""

import logging
import sys
import json
from datetime import datetime

from paper_scraper.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production."""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id

        return json.dumps(log_obj)


def setup_logging():
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    root_logger.addHandler(handler)

    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

---

### Task 7.6: One-Line Pitch Generator

**Create file: paper_scraper/modules/scoring/prompts/one_line_pitch.jinja2**

```jinja2
You are an expert at distilling complex research into compelling one-line pitches for technology transfer and commercialization.

Given the following scientific paper, generate a single-sentence pitch (maximum 15 words) that:
1. Captures the core innovation or breakthrough
2. Hints at commercial/practical application
3. Uses active, compelling language
4. Avoids jargon - accessible to business audiences

## Paper Information

**Title:** {{ title }}

**Abstract:** {{ abstract }}

{% if keywords %}
**Keywords:** {{ keywords | join(", ") }}
{% endif %}

## Output Format

Return ONLY the one-line pitch, nothing else. No quotes, no explanation.

Example good pitches:
- "AI system predicts drug interactions 10x faster than traditional methods"
- "Novel battery material doubles electric vehicle range at lower cost"
- "Gene therapy approach reverses age-related blindness in clinical trials"
```

**Create file: paper_scraper/modules/scoring/pitch_generator.py**

```python
"""One-line pitch generator for papers."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from paper_scraper.modules.scoring.llm_client import LLMClient

PROMPTS_DIR = Path(__file__).parent / "prompts"


class PitchGenerator:
    """Generate compelling one-line pitches for papers."""

    def __init__(self):
        self.llm = LLMClient()
        self.env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
        self.template = self.env.get_template("one_line_pitch.jinja2")

    async def generate(
        self,
        title: str,
        abstract: str | None,
        keywords: list[str] | None = None,
    ) -> str:
        """Generate one-line pitch for paper."""
        prompt = self.template.render(
            title=title,
            abstract=abstract or "",
            keywords=keywords or [],
        )

        pitch = await self.llm.complete(
            prompt=prompt,
            temperature=0.7,  # Slightly creative
            max_tokens=50,
        )

        # Clean up response
        pitch = pitch.strip().strip('"').strip()

        # Enforce max length
        words = pitch.split()
        if len(words) > 15:
            pitch = " ".join(words[:15])

        return pitch
```

**Add migration for one_line_pitch field:**

```bash
alembic revision --autogenerate -m "Add one_line_pitch to papers"
```

```python
# In migration file
def upgrade():
    op.add_column('papers', sa.Column('one_line_pitch', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('papers', 'one_line_pitch')
```

**Update paper_scraper/modules/papers/models.py:**

```python
class Paper(Base):
    # ... existing fields ...

    # AI-generated content
    one_line_pitch: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**Add endpoint: paper_scraper/modules/papers/router.py**

```python
@router.post(
    "/{paper_id}/generate-pitch",
    response_model=PaperResponse,
    summary="Generate one-line pitch",
)
async def generate_pitch(
    paper_id: UUID,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> PaperResponse:
    """Generate AI one-line pitch for paper."""
    paper = await paper_service.generate_pitch(paper_id, current_user.organization_id)
    return paper
```

**Frontend: Display pitch on paper cards**

Update `frontend/src/pages/PapersPage.tsx` to show one_line_pitch on cards.

---

### Task 7.7: Tests for Sprint 7

**Create file: tests/test_production.py**

```python
"""Tests for production infrastructure."""

import pytest
from httpx import AsyncClient


class TestRateLimiting:
    """Test rate limiting middleware."""

    async def test_rate_limit_headers(self, client: AsyncClient, auth_headers: dict):
        """Test rate limit headers are present."""
        response = await client.get("/api/v1/papers/", headers=auth_headers)
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestHealthCheck:
    """Test health endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check returns OK."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPitchGenerator:
    """Test one-line pitch generation."""

    async def test_generate_pitch(self, client: AsyncClient, auth_headers: dict, test_paper):
        """Test pitch generation for paper."""
        response = await client.post(
            f"/api/v1/papers/{test_paper.id}/generate-pitch",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["one_line_pitch"] is not None
        assert len(data["one_line_pitch"].split()) <= 15
```

---

### Sprint 7 Definition of Done

- [ ] Langfuse integration tracking all LLM calls
- [ ] Sentry capturing errors with FastAPI integration
- [ ] Rate limiting on all endpoints (stricter on scoring)
- [ ] API startup/shutdown handlers (DB, Redis, S3)
- [ ] Structured JSON logging in production
- [ ] One-line pitch generator working
- [ ] Pitch displayed on frontend paper cards
- [ ] Tests passing for production features

---

## Sprint 8: Ingestion Expansion (PubMed, arXiv, PDF)

### Goal
Expand paper import capabilities to include PubMed, arXiv, and PDF file uploads.

### Task 8.1: PubMed API Client

**Create file: paper_scraper/modules/papers/clients/pubmed.py**

```python
"""PubMed E-utilities API client."""

import xml.etree.ElementTree as ET
from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient


class PubMedClient(BaseAPIClient):
    """
    Client for PubMed E-utilities API.

    - Free, API key optional (higher rate limits with key)
    - Rate limit: 3 req/s without key, 10 req/s with key

    Docs: https://www.ncbi.nlm.nih.gov/books/NBK25497/
    """

    def __init__(self):
        super().__init__()
        self.base_url = settings.PUBMED_BASE_URL
        self.api_key = settings.PUBMED_API_KEY

    async def search(
        self,
        query: str,
        max_results: int = 100,
    ) -> list[dict]:
        """
        Search PubMed for papers.

        Args:
            query: PubMed search query
            max_results: Maximum results to return

        Returns:
            List of normalized paper dicts
        """
        # Step 1: Search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "usehistory": "y",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key

        search_response = await self.client.get(
            f"{self.base_url}/esearch.fcgi",
            params=search_params,
        )
        search_response.raise_for_status()
        search_data = search_response.json()

        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []

        # Step 2: Fetch details for PMIDs
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "xml",
            "retmode": "xml",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        fetch_response = await self.client.get(
            f"{self.base_url}/efetch.fcgi",
            params=fetch_params,
        )
        fetch_response.raise_for_status()

        # Parse XML response
        return self._parse_pubmed_xml(fetch_response.text)

    async def get_by_id(self, pmid: str) -> dict | None:
        """Get paper by PubMed ID."""
        params = {
            "db": "pubmed",
            "id": pmid,
            "rettype": "xml",
            "retmode": "xml",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        response = await self.client.get(
            f"{self.base_url}/efetch.fcgi",
            params=params,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()

        papers = self._parse_pubmed_xml(response.text)
        return papers[0] if papers else None

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        """Parse PubMed XML response."""
        root = ET.fromstring(xml_text)
        papers = []

        for article in root.findall(".//PubmedArticle"):
            papers.append(self.normalize(article))

        return papers

    def normalize(self, article: ET.Element) -> dict:
        """Normalize PubMed article to standard format."""
        medline = article.find(".//MedlineCitation")
        article_data = medline.find(".//Article")

        # Extract PMID
        pmid = medline.findtext("PMID", "")

        # Extract title
        title = article_data.findtext(".//ArticleTitle", "Untitled")

        # Extract abstract
        abstract_parts = []
        for abstract_text in article_data.findall(".//AbstractText"):
            label = abstract_text.get("Label", "")
            text = abstract_text.text or ""
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts) if abstract_parts else None

        # Extract authors
        authors = []
        for author in article_data.findall(".//Author"):
            last_name = author.findtext("LastName", "")
            first_name = author.findtext("ForeName", "")
            name = f"{first_name} {last_name}".strip()

            affiliations = [
                aff.text for aff in author.findall(".//Affiliation")
                if aff.text
            ]

            authors.append({
                "name": name or "Unknown",
                "affiliations": affiliations,
            })

        # Extract publication date
        pub_date = article_data.find(".//PubDate")
        if pub_date is not None:
            year = pub_date.findtext("Year", "2000")
            month = pub_date.findtext("Month", "01")
            day = pub_date.findtext("Day", "01")
            # Convert month name to number if needed
            try:
                month = int(month)
            except ValueError:
                month_map = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
                month = month_map.get(month[:3], 1)
            publication_date = f"{year}-{month:02d}-{int(day):02d}"
        else:
            publication_date = None

        # Extract journal
        journal = article_data.findtext(".//Journal/Title", None)

        # Extract DOI
        doi = None
        for article_id in article.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text
                break

        # Extract MeSH terms
        mesh_terms = [
            mesh.findtext("DescriptorName", "")
            for mesh in medline.findall(".//MeshHeading")
        ]

        return {
            "source": "pubmed",
            "source_id": pmid,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "publication_date": publication_date,
            "journal": journal,
            "authors": authors,
            "mesh_terms": [m for m in mesh_terms if m],
            "keywords": [],
            "raw_metadata": {"pmid": pmid},
        }
```

---

### Task 8.2: arXiv API Client

**Create file: paper_scraper/modules/papers/clients/arxiv.py**

```python
"""arXiv API client."""

import xml.etree.ElementTree as ET
import asyncio
from paper_scraper.core.config import settings
from paper_scraper.modules.papers.clients.base import BaseAPIClient


class ArxivClient(BaseAPIClient):
    """
    Client for arXiv API.

    - Free, no API key required
    - Rate limit: 1 request per 3 seconds

    Docs: https://info.arxiv.org/help/api/
    """

    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(self):
        super().__init__()
        self.base_url = settings.ARXIV_BASE_URL
        self._last_request = 0

    async def _rate_limit(self):
        """Ensure we don't exceed rate limit (1 req/3s)."""
        import time
        now = time.time()
        wait_time = 3 - (now - self._last_request)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self._last_request = time.time()

    async def search(
        self,
        query: str,
        max_results: int = 100,
        category: str | None = None,
    ) -> list[dict]:
        """
        Search arXiv for papers.

        Args:
            query: Search query
            max_results: Maximum results
            category: Optional category filter (e.g., "cs.AI", "physics.med-ph")

        Returns:
            List of normalized paper dicts
        """
        await self._rate_limit()

        search_query = query
        if category:
            search_query = f"cat:{category} AND all:{query}"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        response = await self.client.get(
            f"{self.base_url}/query",
            params=params,
        )
        response.raise_for_status()

        return self._parse_arxiv_xml(response.text)

    async def get_by_id(self, arxiv_id: str) -> dict | None:
        """
        Get paper by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2301.07041" or "arxiv:2301.07041")
        """
        await self._rate_limit()

        # Clean arXiv ID
        arxiv_id = arxiv_id.replace("arxiv:", "").replace("arXiv:", "")

        params = {"id_list": arxiv_id}

        response = await self.client.get(
            f"{self.base_url}/query",
            params=params,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()

        papers = self._parse_arxiv_xml(response.text)
        return papers[0] if papers else None

    def _parse_arxiv_xml(self, xml_text: str) -> list[dict]:
        """Parse arXiv Atom XML response."""
        root = ET.fromstring(xml_text)
        papers = []

        for entry in root.findall("atom:entry", self.NAMESPACES):
            papers.append(self.normalize(entry))

        return papers

    def normalize(self, entry: ET.Element) -> dict:
        """Normalize arXiv entry to standard format."""
        ns = self.NAMESPACES

        # Extract arXiv ID from URL
        id_url = entry.findtext("atom:id", "", ns)
        arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else id_url

        # Extract title (remove newlines)
        title = entry.findtext("atom:title", "Untitled", ns)
        title = " ".join(title.split())

        # Extract abstract (remove newlines)
        abstract = entry.findtext("atom:summary", "", ns)
        abstract = " ".join(abstract.split()) if abstract else None

        # Extract authors
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", "Unknown", ns)
            affiliation = author.findtext("arxiv:affiliation", None, ns)
            authors.append({
                "name": name,
                "affiliations": [affiliation] if affiliation else [],
            })

        # Extract publication date
        published = entry.findtext("atom:published", None, ns)
        if published:
            publication_date = published[:10]  # YYYY-MM-DD
        else:
            publication_date = None

        # Extract DOI
        doi = entry.findtext("arxiv:doi", None, ns)

        # Extract categories as keywords
        categories = [
            cat.get("term", "")
            for cat in entry.findall("atom:category", ns)
        ]

        # Extract PDF link
        pdf_url = None
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break

        return {
            "source": "arxiv",
            "source_id": arxiv_id,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "publication_date": publication_date,
            "journal": "arXiv",
            "authors": authors,
            "keywords": categories,
            "mesh_terms": [],
            "raw_metadata": {"arxiv_id": arxiv_id, "pdf_url": pdf_url},
        }
```

---

### Task 8.3: PDF Upload & Processing Service

**Create file: paper_scraper/modules/papers/pdf_service.py**

```python
"""PDF upload and text extraction service."""

import io
from uuid import UUID, uuid4
from pathlib import Path

import fitz  # PyMuPDF
from minio import Minio

from paper_scraper.core.config import settings
from paper_scraper.modules.papers.models import Paper, PaperSource


class PDFService:
    """Service for PDF upload and text extraction."""

    def __init__(self):
        self.minio = Minio(
            f"{settings.S3_ENDPOINT_URL.replace('http://', '').replace('https://', '')}",
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_ENDPOINT_URL.startswith("https"),
        )
        self.bucket = settings.S3_BUCKET_NAME

    async def upload_and_extract(
        self,
        file_content: bytes,
        filename: str,
        organization_id: UUID,
    ) -> dict:
        """
        Upload PDF to S3 and extract text/metadata.

        Args:
            file_content: PDF file bytes
            filename: Original filename
            organization_id: Organization UUID

        Returns:
            Dict with extracted metadata and S3 path
        """
        # Generate unique path
        file_id = uuid4()
        s3_path = f"papers/{organization_id}/{file_id}/{filename}"

        # Upload to S3
        self.minio.put_object(
            self.bucket,
            s3_path,
            io.BytesIO(file_content),
            length=len(file_content),
            content_type="application/pdf",
        )

        # Extract text and metadata
        extracted = self._extract_from_pdf(file_content)
        extracted["pdf_path"] = s3_path

        return extracted

    def _extract_from_pdf(self, pdf_content: bytes) -> dict:
        """Extract text and metadata from PDF using PyMuPDF."""
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        # Extract metadata
        metadata = doc.metadata or {}
        title = metadata.get("title") or self._extract_title_from_text(doc)

        # Extract full text
        full_text_parts = []
        for page in doc:
            text = page.get_text("text")
            full_text_parts.append(text)

        full_text = "\n".join(full_text_parts)

        # Extract abstract (heuristic: first paragraph after "Abstract")
        abstract = self._extract_abstract(full_text)

        # Extract authors from metadata or text
        authors = []
        if metadata.get("author"):
            for name in metadata["author"].split(","):
                authors.append({"name": name.strip(), "affiliations": []})

        doc.close()

        return {
            "title": title or "Untitled PDF",
            "abstract": abstract,
            "authors": authors,
            "full_text": full_text[:100000],  # Limit to 100k chars
            "keywords": [],
            "source": "pdf",
        }

    def _extract_title_from_text(self, doc: fitz.Document) -> str | None:
        """Extract title from first page (usually largest font text)."""
        if len(doc) == 0:
            return None

        page = doc[0]
        blocks = page.get_text("dict")["blocks"]

        # Find the largest text on first page (likely title)
        largest_size = 0
        title = None

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > largest_size:
                            largest_size = span["size"]
                            title = span["text"]

        return title

    def _extract_abstract(self, text: str) -> str | None:
        """Extract abstract from full text."""
        import re

        # Try to find abstract section
        patterns = [
            r"(?i)abstract[:\s]*\n(.+?)(?=\n\n|\nintroduction|\n1\.)",
            r"(?i)abstract[:\s]*(.+?)(?=\n\n|keywords|introduction)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up
                abstract = " ".join(abstract.split())
                if len(abstract) > 100:  # Reasonable abstract length
                    return abstract[:2000]  # Limit length

        return None
```

**Add to pyproject.toml:**
```toml
pymupdf = "^1.24"
minio = "^7.2"
```

---

### Task 8.4: API Endpoints for New Sources

**Update file: paper_scraper/modules/papers/router.py**

```python
from fastapi import UploadFile, File

@router.post(
    "/ingest/pubmed",
    response_model=IngestResult,
    summary="Batch import from PubMed",
)
async def ingest_from_pubmed(
    request: IngestPubMedRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> IngestResult:
    """Batch import papers from PubMed search."""
    return await paper_service.ingest_from_pubmed(
        query=request.query,
        organization_id=current_user.organization_id,
        max_results=request.max_results,
    )


@router.post(
    "/ingest/arxiv",
    response_model=IngestResult,
    summary="Batch import from arXiv",
)
async def ingest_from_arxiv(
    request: IngestArxivRequest,
    current_user: CurrentUser,
    paper_service: Annotated[PaperService, Depends(get_paper_service)],
) -> IngestResult:
    """Batch import papers from arXiv search."""
    return await paper_service.ingest_from_arxiv(
        query=request.query,
        organization_id=current_user.organization_id,
        max_results=request.max_results,
        category=request.category,
    )


@router.post(
    "/upload/pdf",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF file",
)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(),
    paper_service: Annotated[PaperService, Depends(get_paper_service)] = Depends(),
) -> PaperResponse:
    """
    Upload a PDF file and extract paper metadata.

    The PDF will be stored in S3 and text extracted for search/scoring.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    content = await file.read()
    if len(content) > 50_000_000:  # 50MB limit
        raise HTTPException(400, "File too large (max 50MB)")

    paper = await paper_service.ingest_from_pdf(
        file_content=content,
        filename=file.filename,
        organization_id=current_user.organization_id,
    )
    return paper
```

---

### Task 8.5: Frontend - Import Forms

**Update frontend/src/pages/PapersPage.tsx**

Add import modal with tabs for DOI, OpenAlex, PubMed, arXiv, and PDF upload.

```typescript
// Import modal component
const ImportModal = ({ isOpen, onClose, onSuccess }) => {
  const [activeTab, setActiveTab] = useState<'doi' | 'openalex' | 'pubmed' | 'arxiv' | 'pdf'>('doi');

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import Papers</DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-5 w-full">
            <TabsTrigger value="doi">DOI</TabsTrigger>
            <TabsTrigger value="openalex">OpenAlex</TabsTrigger>
            <TabsTrigger value="pubmed">PubMed</TabsTrigger>
            <TabsTrigger value="arxiv">arXiv</TabsTrigger>
            <TabsTrigger value="pdf">PDF</TabsTrigger>
          </TabsList>

          <TabsContent value="doi">
            <DOIImportForm onSuccess={onSuccess} />
          </TabsContent>

          <TabsContent value="openalex">
            <OpenAlexImportForm onSuccess={onSuccess} />
          </TabsContent>

          <TabsContent value="pubmed">
            <PubMedImportForm onSuccess={onSuccess} />
          </TabsContent>

          <TabsContent value="arxiv">
            <ArxivImportForm onSuccess={onSuccess} />
          </TabsContent>

          <TabsContent value="pdf">
            <PDFUploadForm onSuccess={onSuccess} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
```

---

### Sprint 8 Definition of Done

- [ ] PubMed client working (search, get_by_id)
- [ ] arXiv client working (search, get_by_id) with rate limiting
- [ ] PDF upload to S3 working
- [ ] PDF text extraction with PyMuPDF
- [ ] API endpoints:
  - [ ] `POST /papers/ingest/pubmed` - PubMed batch import
  - [ ] `POST /papers/ingest/arxiv` - arXiv batch import
  - [ ] `POST /papers/upload/pdf` - PDF file upload
- [ ] Background jobs for async imports
- [ ] Frontend import modal with all sources
- [ ] Source filter chips updated
- [ ] Tests passing (>80% coverage)

---

## Sprint 9: Scoring Enhancements + Author Intelligence Start

### Goal
Enhance AI scoring with simplified abstracts and detailed breakdowns, begin author intelligence features.

### Task 9.1: Simplified Abstract Generator

**Create file: paper_scraper/modules/scoring/prompts/simplified_abstract.jinja2**

```jinja2
You are an expert science communicator who makes complex research accessible to general audiences.

Given the following scientific paper abstract, rewrite it in simple, everyday language that a high school student could understand.

## Guidelines
1. Replace technical jargon with simple explanations
2. Use short sentences (max 20 words each)
3. Focus on: What did they do? What did they find? Why does it matter?
4. Keep it under 150 words
5. No citations or references

## Original Abstract
{{ abstract }}

## Paper Title (for context)
{{ title }}

## Simplified Abstract
Write the simplified version below. Start directly with the content, no preamble.
```

**Add to Paper model:**

```python
# In paper_scraper/modules/papers/models.py
class Paper(Base):
    # ... existing fields ...
    simplified_abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
```

---

### Task 9.2: Enhanced Score Response with Evidence

**Update file: paper_scraper/modules/scoring/schemas.py**

```python
class ScoreEvidence(BaseModel):
    """Evidence supporting a score."""
    factor: str
    description: str
    impact: Literal["positive", "negative", "neutral"]
    source: str | None = None  # Quote from paper


class DimensionScoreDetail(BaseModel):
    """Detailed breakdown of a dimension score."""
    score: float
    confidence: float
    summary: str
    key_factors: list[str]
    evidence: list[ScoreEvidence]
    comparison_to_field: str | None = None


class EnhancedPaperScoreResponse(BaseModel):
    """Enhanced score response with evidence."""
    id: UUID
    paper_id: UUID
    overall_score: float

    # Dimension scores with details
    novelty: DimensionScoreDetail
    ip_potential: DimensionScoreDetail
    marketability: DimensionScoreDetail
    feasibility: DimensionScoreDetail
    commercialization: DimensionScoreDetail

    model_version: str
    created_at: datetime
```

---

### Task 9.3: Paper Notes & Comments

**Create file: paper_scraper/modules/papers/notes.py**

```python
"""Paper notes and comments system."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import ForeignKey, Text, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base


class PaperNote(Base):
    """Note/comment on a paper."""

    __tablename__ = "paper_notes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    paper_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # User UUIDs mentioned

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="notes")
    user: Mapped["User"] = relationship("User")
```

**Add API endpoints:**

```python
# paper_scraper/modules/papers/router.py

@router.get("/{paper_id}/notes", response_model=list[NoteResponse])
async def list_notes(paper_id: UUID, current_user: CurrentUser, ...):
    """List notes for a paper."""
    ...

@router.post("/{paper_id}/notes", response_model=NoteResponse)
async def create_note(paper_id: UUID, request: NoteCreate, current_user: CurrentUser, ...):
    """Add note to paper."""
    ...

@router.delete("/{paper_id}/notes/{note_id}")
async def delete_note(paper_id: UUID, note_id: UUID, current_user: CurrentUser, ...):
    """Delete note (own notes only)."""
    ...
```

---

### Task 9.4: Lead Author Highlighting

**Update frontend components to show author badges:**

```typescript
// frontend/src/components/AuthorBadge.tsx
interface AuthorBadgeProps {
  position: number;
  isCorresponding: boolean;
  totalAuthors: number;
}

export const AuthorBadge = ({ position, isCorresponding, totalAuthors }: AuthorBadgeProps) => {
  const badges = [];

  if (position === 0) {
    badges.push(
      <Badge key="first" variant="default" className="bg-blue-500">
        First Author
      </Badge>
    );
  }

  if (position === totalAuthors - 1 && totalAuthors > 1) {
    badges.push(
      <Badge key="last" variant="default" className="bg-purple-500">
        Senior Author
      </Badge>
    );
  }

  if (isCorresponding) {
    badges.push(
      <Badge key="corresponding" variant="outline" className="border-green-500 text-green-500">
        Corresponding
      </Badge>
    );
  }

  return <div className="flex gap-1">{badges}</div>;
};
```

---

### Sprint 9 Definition of Done

- [ ] Simplified abstract generator working
- [ ] Enhanced score response with evidence
- [ ] Paper notes/comments CRUD
- [ ] @mention extraction
- [ ] Author badges on paper detail
- [ ] Frontend toggle for original/simplified abstract
- [ ] Tests passing

---

## Sprint 10: Author Intelligence Complete

### Goal
Complete author profiles with metrics enrichment and contact tracking.

### Task 10.1: Author Module

**Create directory structure:**
```
paper_scraper/modules/authors/
├── __init__.py
├── models.py      # Contact tracking
├── schemas.py
├── service.py     # Profile enrichment
└── router.py
```

**Key features:**
- Author profile page with metrics (h-index, citations, works)
- Contact tracking (last contacted, by whom, notes)
- Author enrichment from OpenAlex, ORCID, Semantic Scholar

### Sprint 10 Definition of Done

- [ ] Author enrichment service
- [ ] Contact tracking fields and API
- [ ] Author profile endpoint
- [ ] Frontend author modal/page
- [ ] "Log Contact" functionality
- [ ] Tests passing

---

## Sprint 11: Search & Discovery Enhancements

### Goal
Advanced search with saved searches, alerts, and paper classification.

### Task 11.1: Saved Searches

**Create model and endpoints for saved searches with shareable URLs.**

### Task 11.2: Alert System

**Create notification module with email alerts for saved searches.**

### Task 11.3: Paper Classification

**Add LLM-based paper type classification (Original Research, Review, etc.).**

### Sprint 11 Definition of Done

- [ ] Saved search CRUD
- [ ] Alert configuration
- [ ] Email notification sending
- [ ] Paper classification working
- [ ] Frontend saved searches UI
- [ ] Tests passing

---

## Sprint 12: Analytics & Export

### Goal
Analytics dashboard and data export for reporting.

### Task 12.1: Analytics Module

**Create analytics service with team/paper metrics.**

### Task 12.2: Export Module

**Create export service for CSV, PDF, BibTeX.**

### Sprint 12 Definition of Done

- [ ] Team dashboard API
- [ ] Paper analytics API
- [ ] CSV export working
- [ ] PDF export working
- [ ] BibTeX export working
- [ ] Frontend dashboard with charts
- [ ] Tests passing

---

# Phase 3: Beta Readiness (Sprints 13-15)

---

## Sprint 13: User Management & Email Infrastructure

### Goal
Enable team collaboration with invitations, password reset, and email notifications.

### Task 13.1: Email Service Integration

**Create file: paper_scraper/modules/email/service.py**

```python
"""Email service using Resend."""

import resend
from paper_scraper.core.config import settings

resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Email sending service."""

    FROM_EMAIL = settings.EMAIL_FROM_ADDRESS

    async def send_verification_email(self, to: str, token: str) -> bool:
        """Send email verification link."""
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        resend.Emails.send({
            "from": self.FROM_EMAIL,
            "to": to,
            "subject": "Verify your Paper Scraper email",
            "html": f"""
                <h1>Verify your email</h1>
                <p>Click the link below to verify your email address:</p>
                <a href="{verify_url}">Verify Email</a>
                <p>This link expires in 24 hours.</p>
            """,
        })
        return True

    async def send_password_reset_email(self, to: str, token: str) -> bool:
        """Send password reset link."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        resend.Emails.send({
            "from": self.FROM_EMAIL,
            "to": to,
            "subject": "Reset your Paper Scraper password",
            "html": f"""
                <h1>Reset your password</h1>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_url}">Reset Password</a>
                <p>This link expires in 1 hour.</p>
            """,
        })
        return True

    async def send_team_invite_email(self, to: str, token: str, inviter_name: str, org_name: str) -> bool:
        """Send team invitation."""
        invite_url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"

        resend.Emails.send({
            "from": self.FROM_EMAIL,
            "to": to,
            "subject": f"You're invited to join {org_name} on Paper Scraper",
            "html": f"""
                <h1>You're invited!</h1>
                <p>{inviter_name} has invited you to join {org_name} on Paper Scraper.</p>
                <a href="{invite_url}">Accept Invitation</a>
                <p>This invitation expires in 7 days.</p>
            """,
        })
        return True
```

---

### Task 13.2: Auth Endpoints for Email Flows

**Update paper_scraper/modules/auth/router.py**

```python
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, ...):
    """Send password reset email."""
    ...

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, ...):
    """Reset password with token."""
    ...

@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest, ...):
    """Verify email with token."""
    ...

@router.post("/invite")
async def invite_user(request: InviteUserRequest, current_user: CurrentUser, ...):
    """Invite user to organization (admin only)."""
    ...

@router.post("/accept-invite")
async def accept_invite(request: AcceptInviteRequest, ...):
    """Accept team invitation."""
    ...

@router.get("/users")
async def list_users(current_user: CurrentUser, ...):
    """List organization users (admin only)."""
    ...

@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: UUID, request: UpdateRoleRequest, current_user: CurrentUser, ...):
    """Update user role (admin only)."""
    ...
```

---

### Sprint 13 Definition of Done

- [ ] Resend email integration
- [ ] Email verification flow
- [ ] Password reset flow
- [ ] Team invitations
- [ ] User listing (admin)
- [ ] Role management (admin)
- [ ] Frontend pages for all flows
- [ ] Tests passing

---

## Sprint 14: UX Polish & Onboarding

### Goal
Create polished user experience with onboarding, empty states, and error handling.

### Task 14.1: Empty State Components

**Create frontend/src/components/EmptyState.tsx**

```typescript
interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState = ({ icon, title, description, action }: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 mb-4 text-muted-foreground">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground mb-4 max-w-sm">{description}</p>
      {action && (
        <Button onClick={action.onClick}>{action.label}</Button>
      )}
    </div>
  );
};
```

---

### Task 14.2: Onboarding Wizard

**Create frontend/src/components/Onboarding/OnboardingWizard.tsx**

4-step wizard:
1. Organization setup (name, type)
2. Import first papers (DOI or OpenAlex)
3. Create first project
4. Score a paper

---

### Sprint 14 Definition of Done

- [ ] Empty states for all list pages
- [ ] Onboarding wizard (4 steps)
- [ ] Toast notifications
- [ ] Error boundary
- [ ] Skeleton loading components
- [ ] User settings page
- [ ] Organization settings page
- [ ] Confirmation dialogs
- [ ] Backend onboarding tracking

---

## Sprint 15: Deployment & Quality Assurance

### Goal
Production-ready deployment with CI/CD, testing, and compliance.

### Task 15.1: CI/CD Pipeline

**Create .github/workflows/ci.yml**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff mypy
      - run: ruff check .
      - run: ruff format --check .

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov=paper_scraper --cov-report=xml
      - uses: codecov/codecov-action@v4

  test-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run build

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npx playwright install --with-deps
      - run: docker-compose up -d
      - run: npx playwright test
```

---

### Task 15.2: E2E Tests with Playwright

**Create e2e/tests/auth.spec.ts**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can register and login', async ({ page }) => {
    // Register
    await page.goto('/register');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.fill('[name="organization_name"]', 'Test Org');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Logout
    await page.click('[data-testid="logout"]');

    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });
});
```

---

### Task 15.3: GDPR Compliance

**Add endpoints:**

```python
@router.get("/export-data")
async def export_user_data(current_user: CurrentUser, ...):
    """Export all user and organization data as JSON."""
    ...

@router.delete("/delete-account")
async def delete_account(current_user: CurrentUser, ...):
    """Permanently delete account and all associated data."""
    ...
```

---

### Task 15.4: Audit Logging

**Create paper_scraper/modules/audit/models.py**

```python
class AuditLog(Base):
    """Audit trail for security-relevant actions."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    organization_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)  # login, logout, export, delete, etc.
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

---

### Sprint 15 Definition of Done

- [ ] CI/CD pipeline (lint, test, build)
- [ ] Deploy workflow (staging, production)
- [ ] Frontend unit tests (Vitest)
- [ ] E2E tests (Playwright) for critical flows
- [ ] GDPR data export endpoint
- [ ] GDPR account deletion endpoint
- [ ] Audit logging for security events
- [ ] Security headers middleware
- [ ] DEPLOYMENT.md guide
- [ ] All tests passing
- [ ] >80% backend coverage

---

## Beta Launch Checklist

Before inviting external users:

### Security
- [ ] Rate limiting active on all endpoints
- [ ] Sentry capturing errors
- [ ] Security headers configured
- [ ] Email verification required
- [ ] Password reset working
- [ ] Audit logging enabled

### Infrastructure
- [ ] CI/CD pipeline passing
- [ ] Staging environment running
- [ ] Database backups configured
- [ ] SSL certificates valid
- [ ] Monitoring dashboards set up

### User Experience
- [ ] Onboarding wizard tested
- [ ] Empty states for all pages
- [ ] Error messages user-friendly
- [ ] Loading states smooth
- [ ] Mobile responsiveness checked

### Compliance
- [ ] GDPR data export working
- [ ] Account deletion working
- [ ] Privacy policy page
- [ ] Terms of service page

### Testing
- [ ] Backend test coverage >80%
- [ ] Frontend critical paths tested
- [ ] E2E tests passing
- [ ] Manual QA completed
