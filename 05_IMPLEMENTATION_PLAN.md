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
| 6 | Frontend MVP | 2 weeks | 🔲 Not Started |

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

## Sprint 6: Frontend MVP

### Goal
React frontend with core functionality.

### Setup Commands

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install @tanstack/react-query axios zod react-router-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn-ui@latest init
```

### Key Pages

1. `/login`, `/register` - Auth pages
2. `/` - Dashboard with recent papers
3. `/papers` - Paper list with search
4. `/papers/:id` - Paper detail with scores
5. `/projects` - Project list
6. `/projects/:id` - KanBan board

### Sprint 6 Definition of Done

- [ ] Authentication flow working
- [ ] Paper list with search and pagination
- [ ] Paper detail with score visualization
- [ ] KanBan board with drag-and-drop
- [ ] Responsive design
- [ ] Loading and error states

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
