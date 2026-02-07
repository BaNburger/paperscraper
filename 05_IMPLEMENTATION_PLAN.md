# Paper Scraper - Implementation Plan

> **Purpose**: This document serves as a detailed instruction guide for Claude Code to implement the Paper Scraper platform sprint by sprint. Each sprint contains specific files to create, code patterns to follow, and verification steps.

---

## Overview

### Phase 1: Foundation & MVP (Sprints 1-6)

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
| 7 | Production Hardening + One-Line Pitch | 2 weeks | ✅ Complete |
| 8 | Ingestion Expansion (PubMed, arXiv, PDF) | 2 weeks | ✅ Complete |
| 9 | Scoring Enhancements + Author Intelligence Start | 2 weeks | ✅ Complete |
| 10 | Author Intelligence Complete | 2 weeks | ✅ Complete |
| 11 | Search & Discovery Enhancements | 2 weeks | ✅ Complete |
| 12 | Analytics & Export | 2 weeks | ✅ Complete |

### Phase 3: Beta Readiness (Sprints 13-15)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 13 | User Management & Email Infrastructure | 2 weeks | ✅ Complete |
| 14 | UX Polish & Onboarding | 2 weeks | ✅ Complete |
| 15 | Deployment & Quality Assurance | 2 weeks | ✅ Complete |

### Phase 4: Lovable Prototype Features (Sprints 16-19)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 16 | Researcher Groups & Collaboration | 2 weeks | ✅ Complete |
| 17 | Technology Transfer Conversations | 2 weeks | ✅ Complete |
| 18 | Research Submission Portal | 2 weeks | ✅ Complete |
| 19 | Gamification & Knowledge Management | 2 weeks | ✅ Complete |

### Phase 5: Stabilization & Frontend Integration (Sprints 20-21)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 20 | Critical Fixes & Deployment Readiness | 1 week | ✅ Complete |
| 21 | Phase 4 Frontend Integration | 2 weeks | ✅ Complete |

### Phase 6: Security & AI Advancement (Sprints 22-24)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 22 | Security Hardening & RBAC | 2 weeks | ✅ Complete |
| 23 | 6-Dimension Scoring + Model Settings | 2 weeks | ✅ Complete |
| 24 | AI Intelligence Enhancements | 2 weeks | ✅ Complete |

### Phase 7: Platform & Developer Experience (Sprints 25-27)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 25 | Developer API, MCP Server & Repository Management | 2 weeks | ✅ Complete |
| 26 | UX Polish, Keyboard Nav & Mobile Responsiveness | 2 weeks | ✅ Complete |
| 27 | Analytics, Reporting & AI Insights | 2 weeks | ✅ Complete |

### Phase 8: Enterprise Readiness (Sprints 28-30)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 28 | Compliance, Governance, Data Retention & SOC2 | 2 weeks | ✅ Complete |
| 29 | Internationalization & Platform Features | 2 weeks | ✅ Complete |
| 30 | Technical Debt & Quality | 2 weeks | ✅ Complete |

### Phase 9: Quality & Production Readiness (Sprints 31-36)

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| 31 | Bug Fixes, RBAC Enforcement & Code Hygiene | 1 week | ✅ Complete |
| 32 | Test Fixes & Missing Coverage | 1 week | ✅ Complete |
| 33 | Frontend Unit Tests (Hooks) | 1 week | ✅ Complete |
| 34 | Dedicated Alerts Page | 1 week | ✅ Complete |
| 35 | Complete i18n (English + German) | 1 week | ✅ Complete |
| 36 | Server-side Notifications & Real-time Polling | 1 week | ✅ Complete |

---

## Improvement Summary (February 2026 Review)

### Completed Since Last Review
- **22 Backend Modules** operational (was 17 at last review)
- **6 Scoring Dimensions** (added Team Readiness)
- **28 Frontend Pages** with full routing
- **208+ API Endpoints** across 22 modules
- **Granular RBAC** via `core/permissions.py` on all routers
- **CSV Injection Protection** via `core/csv_utils.py`
- **Innovation Radar** chart component
- **Model Configuration** module for org-level LLM settings
- **Badge Auto-Award** engine (`jobs/badges.py`)
- **Server-side Notifications** module with real-time polling
- **Full i18n** (English + German) via react-i18next
- **Developer API** with API keys, webhooks, repository sources
- **Compliance & Retention** policies with automated enforcement
- **Scheduled Reports** module

### Key Additions (Sprints 31-36)
| Sprint | Items Completed |
|--------|-----------------|
| **31** | Bug fixes, client exports, RBAC enforcement on all 9 remaining routers |
| **32** | Test fixes, missing test coverage for alerts/saved_searches/model_settings |
| **33** | Frontend unit tests for usePapers, useNotifications, useSavedSearches, useAlerts |
| **34** | Dedicated AlertsPage with list, create/edit, results history, trigger |
| **35** | Complete i18n coverage (English + German, ~400 translation keys) |
| **36** | Server-side notifications module, backend persistence, real-time polling |

### Remaining AI Integration Gaps
| ID | Feature | Status | Notes |
|----|---------|--------|-------|
| **AI-001** | Embedding-based group suggestions | Prompt ready | Needs pgvector integration in `groups/service.py` |
| **AI-005** | Knowledge-enhanced scoring | Planned | Inject knowledge sources into scoring prompts |
| **AI-006** | WebSocket for real-time transfer | Planned | Currently polling-based |

### Technical Debt Addressed
- ✅ TD-006: Transfer module migration
- ✅ TD-004: Submission file storage (MinIO)
- ✅ TD-008: Transfer resource storage
- ✅ TD-009: Badge auto-award engine
- ✅ TD-010: RBAC enforcement on all routers
- ✅ TD-011: Server-side notification persistence (replaced localStorage)
- ✅ TD-012: Frontend i18n coverage
- ✅ TD-013: Console.log cleanup in production code

---

## User Stories Reference (Lovable Prototype)

> Source: `06_LOVABLE_FEATURES.md` - 64 user stories across 18 domains

| Domain | Story IDs | Sprint | Status |
|--------|-----------|--------|--------|
| Paper Management | P1-P7 | 1-6 | ✅ Backend, ✅ Frontend |
| KanBan Board | K1-K4 | 4 | ✅ Backend, ✅ Frontend |
| Researcher Management | R1-R5 | 10 | ✅ Backend, ✅ Frontend |
| Researcher Groups | G1-G4 | 16 (backend), 21 (frontend) | ✅ Backend, ✅ Frontend |
| Technology Transfer | T1-T6 | 17 (backend), 21 (frontend) | ✅ Backend, ✅ Frontend |
| Search & Discovery | S1-S2 | 5, 11 | ✅ Complete |
| Search & Discovery | S3-S4 | **26, 27** | ✅ Complete |
| Reports & Analytics | A1, A3 | 12 | ✅ Complete |
| Reports & Analytics | A2, A4, A5 | **27** | ✅ Complete |
| Alerts & Notifications | N1-N2, N4 | 11 | ✅ Backend |
| Alerts & Notifications | N3 | **26** | ✅ Complete |
| User Settings | U1-U2, U4 | 13-14 | ✅ Complete |
| User Settings | U3 (i18n) | **29** | ✅ Complete |
| Organization Settings | O1 | 13 | ✅ User management |
| Organization Settings | O2 (branding) | **29** | ✅ Complete |
| Organization Settings | O3 (billing) | **29** | ✅ Complete |
| Organization Settings | O4 (integrations) | **25** | ✅ Complete |
| Model Settings | M1-M4 | 23 | ✅ Complete |
| Repository Settings | RS1-RS3 | **25** | ✅ Complete |
| Developer Settings | D1-D3 | **25** | ✅ Complete |
| Compliance & Governance | C1-C2 | 22 | ✅ RBAC & Audit Logging |
| Compliance & Governance | C3 (SOC2) | **28** | ✅ Complete |
| Keyboard Shortcuts | KB1-KB3 | **26** | ✅ Complete |
| Gamification | GA1-GA3 | 19 (backend), 21 (frontend) | ✅ Backend, ✅ Frontend |
| Research Submission | SUB1-SUB3 | 18 (backend), 21 (frontend) | ✅ Backend, ✅ Frontend |
| Knowledge Management | KM1-KM2 | 19 (backend), 21 (frontend) | ✅ Backend, ✅ Frontend |

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

- [x] Langfuse integration tracking all LLM calls
- [x] Sentry capturing errors with FastAPI integration
- [x] Rate limiting on all endpoints (stricter on scoring)
- [x] API startup/shutdown handlers (DB, Redis, S3)
- [x] Structured JSON logging in production
- [x] One-line pitch generator working
- [x] Pitch displayed on frontend paper cards
- [x] Tests passing for production features

**Sprint 7 completed: 2026-01-30**

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

- [x] PubMed client working (search, get_by_id)
- [x] arXiv client working (search, get_by_id) with rate limiting
- [x] PDF upload to S3 working
- [x] PDF text extraction with PyMuPDF
- [x] API endpoints:
  - [x] `POST /papers/ingest/pubmed` - PubMed batch import
  - [x] `POST /papers/ingest/arxiv` - arXiv batch import
  - [x] `POST /papers/upload/pdf` - PDF file upload
- [ ] Background jobs for async imports (deferred - sync imports work for MVP)
- [x] Frontend import modal with all sources
- [x] Source filter chips updated
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

- [x] Simplified abstract generator working
- [x] Enhanced score response with evidence
- [x] Paper notes/comments CRUD
- [x] @mention extraction
- [x] Author badges on paper detail
- [x] Frontend toggle for original/simplified abstract
- [ ] Tests passing

**Sprint 9 completed: 2026-01-31**

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

- [x] Author enrichment service
- [x] Contact tracking fields and API
- [x] Author profile endpoint
- [x] Frontend author modal/page
- [x] "Log Contact" functionality
- [ ] Tests passing

**Sprint 10 completed: 2026-01-31**

### Implementation Summary

**Backend:**
- Created `paper_scraper/modules/authors/` with models, schemas, service, router
- `AuthorContact` model with `ContactType` and `ContactOutcome` enums
- Author enrichment from OpenAlex API
- Contact CRUD operations with statistics
- New migration: `f6g7h8i9j0k1_sprint10_author_contacts`

**Frontend:**
- `AuthorModal` component (slide-over panel)
- `useAuthors` hooks for React Query integration
- Authors API client in `lib/api.ts`
- Updated types in `types/index.ts`
- Integrated into `PaperDetailPage` - clickable author rows

**API Endpoints:**
- `GET /authors/` - List authors
- `GET /authors/{id}` - Author profile
- `GET /authors/{id}/detail` - Full detail with papers & contacts
- `POST /authors/{id}/contacts` - Log contact
- `PATCH /authors/{id}/contacts/{cid}` - Update contact
- `DELETE /authors/{id}/contacts/{cid}` - Delete contact
- `GET /authors/{id}/contacts/stats` - Contact statistics
- `POST /authors/{id}/enrich` - Enrich from OpenAlex

---

## Sprint 11: Search & Discovery Enhancements ✅ COMPLETED

### Goal
Advanced search with saved searches, alerts, and paper classification.

### Task 11.1: Saved Searches ✅

**Created model and endpoints for saved searches with shareable URLs.**

Files created:
- `paper_scraper/modules/saved_searches/__init__.py`
- `paper_scraper/modules/saved_searches/models.py` - SavedSearch model
- `paper_scraper/modules/saved_searches/schemas.py` - Request/Response schemas
- `paper_scraper/modules/saved_searches/service.py` - CRUD, share tokens
- `paper_scraper/modules/saved_searches/router.py` - REST API endpoints

API Endpoints:
- `GET /saved-searches/` - List saved searches
- `POST /saved-searches/` - Create saved search
- `GET /saved-searches/{id}` - Get saved search
- `PATCH /saved-searches/{id}` - Update saved search
- `DELETE /saved-searches/{id}` - Delete saved search
- `POST /saved-searches/{id}/share` - Generate share link
- `DELETE /saved-searches/{id}/share` - Revoke share link
- `POST /saved-searches/{id}/run` - Execute saved search
- `GET /saved-searches/shared/{token}` - Get by share token (public)

### Task 11.2: Alert System ✅

**Created notification module with email alerts for saved searches.**

Files created:
- `paper_scraper/modules/alerts/__init__.py`
- `paper_scraper/modules/alerts/models.py` - Alert, AlertResult models
- `paper_scraper/modules/alerts/schemas.py` - Request/Response schemas
- `paper_scraper/modules/alerts/service.py` - Alert processing
- `paper_scraper/modules/alerts/email_service.py` - Resend integration
- `paper_scraper/modules/alerts/router.py` - REST API endpoints
- `paper_scraper/jobs/alerts.py` - Background jobs (daily/weekly cron)

API Endpoints:
- `GET /alerts/` - List alerts
- `POST /alerts/` - Create alert
- `GET /alerts/{id}` - Get alert
- `PATCH /alerts/{id}` - Update alert
- `DELETE /alerts/{id}` - Delete alert
- `GET /alerts/{id}/results` - Get alert history
- `POST /alerts/{id}/test` - Test alert (dry run)
- `POST /alerts/{id}/trigger` - Manually trigger alert

### Task 11.3: Paper Classification ✅

**Added LLM-based paper type classification (Original Research, Review, etc.).**

Files created/modified:
- `paper_scraper/modules/papers/models.py` - Added PaperType enum, paper_type field
- `paper_scraper/modules/scoring/classifier.py` - PaperClassifier service
- `paper_scraper/modules/scoring/prompts/paper_classification.jinja2` - Classification prompt
- `paper_scraper/modules/scoring/router.py` - Classification endpoints

Classification Types:
- ORIGINAL_RESEARCH - Primary research with new data
- REVIEW - Literature reviews, systematic reviews, meta-analyses
- CASE_STUDY - Individual case reports
- METHODOLOGY - New methods/protocols
- THEORETICAL - Conceptual/mathematical models
- COMMENTARY - Editorials, opinions, letters
- PREPRINT - Early-stage research
- OTHER - Conference abstracts, datasets, etc.

API Endpoints:
- `POST /scoring/papers/{id}/classify` - Classify single paper
- `POST /scoring/classification/batch` - Batch classify
- `GET /scoring/classification/unclassified` - List unclassified papers

### Frontend Components ✅

Files created:
- `frontend/src/pages/SavedSearchesPage.tsx` - Saved searches management UI
- `frontend/src/hooks/useSavedSearches.ts` - React Query hooks
- `frontend/src/hooks/useAlerts.ts` - React Query hooks
- `frontend/src/types/index.ts` - Added SavedSearch, Alert, PaperType types
- `frontend/src/lib/api.ts` - Added savedSearchesApi, alertsApi, classificationApi

### Database Migrations

- `alembic/versions/20260131_0002_f6g7h8i9j0k1_add_saved_searches.py`
- `alembic/versions/20260131_0003_g7h8i9j0k1l2_add_alerts.py`
- `alembic/versions/20260131_0004_h8i9j0k1l2m3_add_paper_classification.py`

### Sprint 11 Definition of Done

- [x] Saved search CRUD
- [x] Alert configuration
- [x] Email notification sending
- [x] Paper classification working
- [x] Frontend saved searches UI
- [x] Tests passing

---

## Sprint 12: Analytics & Export ✅ COMPLETED

### Goal
Analytics dashboard and data export for reporting.

### Task 12.1: Analytics Module ✅

**Created analytics service with team/paper metrics.**

Files created:
- `paper_scraper/modules/analytics/__init__.py`
- `paper_scraper/modules/analytics/schemas.py` - Analytics response schemas
- `paper_scraper/modules/analytics/service.py` - Analytics computation logic
- `paper_scraper/modules/analytics/router.py` - API endpoints

Endpoints:
- `GET /api/v1/analytics/dashboard` - Dashboard summary with key metrics
- `GET /api/v1/analytics/team` - Team overview and user activity
- `GET /api/v1/analytics/papers` - Paper import trends and scoring stats

### Task 12.2: Export Module ✅

**Created export service for CSV, PDF, BibTeX.**

Files created:
- `paper_scraper/modules/export/__init__.py`
- `paper_scraper/modules/export/schemas.py` - Export options schemas
- `paper_scraper/modules/export/service.py` - Export generation logic
- `paper_scraper/modules/export/router.py` - Export endpoints

Endpoints:
- `GET /api/v1/export/csv` - Export papers to CSV
- `GET /api/v1/export/bibtex` - Export papers to BibTeX
- `GET /api/v1/export/pdf` - Export papers to PDF report
- `POST /api/v1/export/batch` - Batch export with format selection

### Frontend Implementation ✅

Files created/updated:
- `frontend/src/pages/AnalyticsPage.tsx` - Analytics dashboard with charts
- `frontend/src/hooks/useAnalytics.ts` - React Query hooks for analytics
- `frontend/src/lib/api.ts` - Added analyticsApi and exportApi
- `frontend/src/types/index.ts` - Added analytics types
- Updated sidebar navigation

### Tests ✅

Files created:
- `tests/test_analytics.py` - Analytics API tests
- `tests/test_export.py` - Export API tests

### Sprint 12 Definition of Done

- [x] Team dashboard API
- [x] Paper analytics API
- [x] CSV export working
- [x] PDF export working
- [x] BibTeX export working
- [x] Frontend dashboard with charts
- [x] Tests passing

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

- [x] Resend email integration
- [x] Email verification flow
- [x] Password reset flow
- [x] Team invitations
- [x] User listing (admin)
- [x] Role management (admin)
- [x] Frontend pages for all flows
- [x] Tests passing

**Sprint 13 Completed: 2026-01-31**

Implementation includes:
- Email service module (`paper_scraper/modules/email/service.py`)
- User model extended with email verification and password reset fields
- TeamInvitation model for team collaboration
- Database migration for new fields
- Auth router with 14 new endpoints
- Frontend pages: ForgotPassword, ResetPassword, VerifyEmail, AcceptInvite, TeamMembers
- Comprehensive test coverage for all new flows

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

- [x] Empty states for all list pages
- [x] Onboarding wizard (4 steps)
- [x] Toast notifications
- [x] Error boundary
- [x] Skeleton loading components
- [x] User settings page
- [x] Organization settings page
- [x] Confirmation dialogs
- [x] Backend onboarding tracking

### Sprint 14 Completed Components

**UI Components Created (frontend/src/components/ui/):**
- `EmptyState.tsx` - Reusable empty state with icon, title, description, and action buttons
- `Skeleton.tsx` - Loading skeletons (SkeletonCard, SkeletonTable, SkeletonKanban, etc.)
- `Toast.tsx` - Toast notification system with ToastProvider and useToast hook
- `ConfirmDialog.tsx` - Confirmation dialog component with destructive variant

**Core Components:**
- `ErrorBoundary.tsx` - React error boundary with fallback UI

**Onboarding (frontend/src/components/Onboarding/):**
- `OnboardingWizard.tsx` - 4-step wizard orchestrator
- `steps/OrganizationStep.tsx` - Organization type selection
- `steps/ImportPapersStep.tsx` - DOI/OpenAlex/PDF import
- `steps/CreateProjectStep.tsx` - First project creation
- `steps/ScorePaperStep.tsx` - AI scoring demonstration

**Settings Pages (frontend/src/pages/):**
- `UserSettingsPage.tsx` - Profile, notifications, password change
- `OrganizationSettingsPage.tsx` - Org profile, team management, subscription info

**Backend Changes:**
- Added `onboarding_completed` and `onboarding_completed_at` fields to User model
- Added `POST /auth/onboarding/complete` endpoint
- Created migration `20260131_sprint14_onboarding_tracking.py`

**Updated Pages with EmptyState & Skeleton:**
- `PapersPage.tsx` - Skeleton loading, contextual empty states
- `ProjectsPage.tsx` - Skeleton loading, empty state, ConfirmDialog for delete
- `SearchPage.tsx` - Skeleton loading, search-specific empty states

**App.tsx Updates:**
- Wrapped with ErrorBoundary and ToastProvider
- Added routes: `/settings`, `/settings/organization`

**Layout Updates:**
- `Sidebar.tsx` - Added Team and Settings nav items
- `Navbar.tsx` - User dropdown with settings links

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

- [x] CI/CD pipeline (lint, test, build) - `.github/workflows/ci.yml`
- [x] Deploy workflow (staging, production) - `.github/workflows/deploy.yml`
- [x] Frontend unit tests (Vitest) - `frontend/vitest.config.ts`, component tests
- [x] E2E tests (Playwright) for critical flows - `e2e/tests/auth.spec.ts`, `e2e/tests/papers.spec.ts`
- [x] GDPR data export endpoint - `GET /api/v1/auth/export-data`
- [x] GDPR account deletion endpoint - `DELETE /api/v1/auth/delete-account`
- [x] Audit logging for security events - `paper_scraper/modules/audit/`
- [x] Security headers middleware - `paper_scraper/api/middleware.py`
- [x] DEPLOYMENT.md guide - `DEPLOYMENT.md`
- [ ] All tests passing
- [ ] >80% backend coverage

---

## Beta Launch Checklist

Before inviting external users:

### Security
- [x] Rate limiting active on all endpoints
- [x] Sentry capturing errors
- [x] Security headers configured
- [x] Email verification required
- [x] Password reset working
- [x] Audit logging enabled

### Infrastructure
- [x] CI/CD pipeline passing
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
- [x] GDPR data export working
- [x] Account deletion working
- [ ] Privacy policy page
- [ ] Terms of service page

### Testing
- [ ] Backend test coverage >80%
- [ ] Frontend critical paths tested
- [ ] E2E tests passing
- [ ] Manual QA completed

---

# Phase 4: Lovable Prototype Features (Sprints 16-19)

> Features extracted from the Lovable prototype to achieve feature parity.
> Source: `06_LOVABLE_FEATURES.md`

---

## Sprint 16: Researcher Groups & Collaboration ✅ COMPLETE

### Goal
Implement researcher grouping functionality with support for mailing lists, speaker pools, and AI-powered member suggestions.

### User Stories
- **G1**: As a TTO manager, I want to create researcher groups so I can organize researchers by expertise
- **G2**: As an admin, I want to create mailing lists so I can send targeted communications
- **G3**: As a user, I want AI to suggest group members based on keywords for efficient group creation
- **G4**: As an event organizer, I want speaker pools so I can quickly find presenters

---

### Task 16.1: Researcher Groups Model

**Create directory structure:**
```
paper_scraper/modules/groups/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
├── router.py
└── prompts/
    └── suggest_members.jinja2
```

**File: paper_scraper/modules/groups/models.py**
```python
"""SQLAlchemy models for researcher groups."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base


class GroupType(str, enum.Enum):
    """Type of researcher group."""
    CUSTOM = "custom"
    MAILING_LIST = "mailing_list"
    SPEAKER_POOL = "speaker_pool"


class ResearcherGroup(Base):
    """Group of researchers for organization and outreach."""

    __tablename__ = "researcher_groups"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[GroupType] = mapped_column(
        Enum(GroupType), default=GroupType.CUSTOM, nullable=False
    )
    keywords: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    # Relationships
    members: Mapped[list["GroupMember"]] = relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class GroupMember(Base):
    """Association table for group membership."""

    __tablename__ = "group_members"

    group_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("researcher_groups.id", ondelete="CASCADE"),
        primary_key=True
    )
    researcher_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="CASCADE"),
        primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    added_by: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    group: Mapped["ResearcherGroup"] = relationship(
        "ResearcherGroup", back_populates="members"
    )
    researcher: Mapped["Author"] = relationship("Author")
```

**Migration:**
```bash
alembic revision --autogenerate -m "add_researcher_groups"
```

---

### Task 16.2: Researcher Groups Schemas

**File: paper_scraper/modules/groups/schemas.py**
```python
"""Pydantic schemas for researcher groups."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from paper_scraper.modules.groups.models import GroupType


class GroupMemberResponse(BaseModel):
    """Response schema for group member."""
    researcher_id: UUID
    researcher_name: str
    researcher_email: str | None = None
    h_index: int | None = None
    added_at: datetime

    model_config = {"from_attributes": True}


class GroupBase(BaseModel):
    """Base schema for group."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    type: GroupType = GroupType.CUSTOM
    keywords: list[str] = Field(default_factory=list)


class GroupCreate(GroupBase):
    """Schema for creating a group."""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name: str | None = None
    description: str | None = None
    type: GroupType | None = None
    keywords: list[str] | None = None


class GroupResponse(GroupBase):
    """Response schema for group."""
    id: UUID
    organization_id: UUID
    created_by: UUID | None
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class GroupDetail(GroupResponse):
    """Detailed response schema for group with members."""
    members: list[GroupMemberResponse] = Field(default_factory=list)


class GroupListResponse(BaseModel):
    """Paginated list of groups."""
    items: list[GroupResponse]
    total: int
    page: int
    page_size: int


class AddMembersRequest(BaseModel):
    """Request to add members to a group."""
    researcher_ids: list[UUID]


class RemoveMemberRequest(BaseModel):
    """Request to remove a member from a group."""
    researcher_id: UUID


class SuggestMembersRequest(BaseModel):
    """Request for AI-suggested members."""
    keywords: list[str] = Field(..., min_length=1)
    target_size: int = Field(default=10, ge=1, le=50)


class SuggestedMember(BaseModel):
    """AI-suggested group member."""
    researcher_id: UUID
    name: str
    relevance_score: float = Field(..., ge=0, le=1)
    matching_keywords: list[str]
    affiliations: list[str] = Field(default_factory=list)


class SuggestMembersResponse(BaseModel):
    """Response for suggested members."""
    suggestions: list[SuggestedMember]
    query_keywords: list[str]


class GroupExportResponse(BaseModel):
    """Response for group export."""
    group_name: str
    member_count: int
    export_url: str
```

---

### Task 16.3: Researcher Groups Service

**File: paper_scraper/modules/groups/service.py**
```python
"""Service layer for researcher groups."""

from uuid import UUID

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from paper_scraper.core.exceptions import NotFoundError, DuplicateError
from paper_scraper.modules.authors.models import Author
from paper_scraper.modules.groups.models import GroupMember, ResearcherGroup, GroupType
from paper_scraper.modules.groups.schemas import (
    GroupCreate, GroupUpdate, GroupListResponse, SuggestedMember
)


class GroupService:
    """Service for managing researcher groups."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_groups(
        self,
        organization_id: UUID,
        group_type: GroupType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> GroupListResponse:
        """List groups with optional type filter."""
        query = select(ResearcherGroup).where(
            ResearcherGroup.organization_id == organization_id
        )

        if group_type:
            query = query.where(ResearcherGroup.type == group_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(ResearcherGroup.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        groups = list(result.scalars().all())

        # Add member counts
        for group in groups:
            count_result = await self.db.execute(
                select(func.count()).where(GroupMember.group_id == group.id)
            )
            group.member_count = count_result.scalar() or 0

        return GroupListResponse(
            items=groups,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_group(
        self, group_id: UUID, organization_id: UUID
    ) -> ResearcherGroup:
        """Get group with members."""
        result = await self.db.execute(
            select(ResearcherGroup)
            .options(
                selectinload(ResearcherGroup.members)
                .selectinload(GroupMember.researcher)
            )
            .where(
                ResearcherGroup.id == group_id,
                ResearcherGroup.organization_id == organization_id,
            )
        )
        group = result.scalar_one_or_none()
        if not group:
            raise NotFoundError("Group", "id", str(group_id))
        return group

    async def create_group(
        self,
        organization_id: UUID,
        user_id: UUID,
        data: GroupCreate,
    ) -> ResearcherGroup:
        """Create a new group."""
        group = ResearcherGroup(
            organization_id=organization_id,
            created_by=user_id,
            **data.model_dump(),
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def update_group(
        self,
        group_id: UUID,
        organization_id: UUID,
        data: GroupUpdate,
    ) -> ResearcherGroup:
        """Update a group."""
        group = await self.get_group(group_id, organization_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)

        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete_group(
        self, group_id: UUID, organization_id: UUID
    ) -> None:
        """Delete a group."""
        group = await self.get_group(group_id, organization_id)
        await self.db.delete(group)
        await self.db.commit()

    async def add_members(
        self,
        group_id: UUID,
        organization_id: UUID,
        researcher_ids: list[UUID],
        added_by: UUID,
    ) -> int:
        """Add members to a group."""
        # Verify group exists
        await self.get_group(group_id, organization_id)

        added = 0
        for researcher_id in researcher_ids:
            # Check if already a member
            existing = await self.db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == group_id,
                    GroupMember.researcher_id == researcher_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            member = GroupMember(
                group_id=group_id,
                researcher_id=researcher_id,
                added_by=added_by,
            )
            self.db.add(member)
            added += 1

        await self.db.commit()
        return added

    async def remove_member(
        self,
        group_id: UUID,
        organization_id: UUID,
        researcher_id: UUID,
    ) -> None:
        """Remove a member from a group."""
        await self.get_group(group_id, organization_id)

        await self.db.execute(
            delete(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.researcher_id == researcher_id,
            )
        )
        await self.db.commit()

    async def suggest_members(
        self,
        organization_id: UUID,
        keywords: list[str],
        target_size: int = 10,
    ) -> list[SuggestedMember]:
        """AI-powered member suggestions based on keywords."""
        # Use embedding similarity search
        # For now, simplified implementation
        query = (
            select(Author)
            .limit(target_size)
        )
        result = await self.db.execute(query)
        authors = result.scalars().all()

        suggestions = []
        for author in authors:
            suggestions.append(SuggestedMember(
                researcher_id=author.id,
                name=author.name,
                relevance_score=0.8,  # Placeholder - implement embedding similarity
                matching_keywords=keywords[:2],
                affiliations=author.affiliations or [],
            ))

        return suggestions

    async def export_group(
        self, group_id: UUID, organization_id: UUID
    ) -> bytes:
        """Export group members as CSV."""
        group = await self.get_group(group_id, organization_id)

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email", "H-Index", "Affiliations"])

        for member in group.members:
            researcher = member.researcher
            writer.writerow([
                researcher.name,
                "",  # Email not in Author model yet
                researcher.h_index or "",
                ", ".join(researcher.affiliations or []),
            ])

        return output.getvalue().encode("utf-8")
```

---

### Task 16.4: Researcher Groups Router

**File: paper_scraper/modules/groups/router.py**
```python
"""FastAPI router for researcher groups."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from paper_scraper.api.dependencies import CurrentUser
from paper_scraper.core.database import get_db
from paper_scraper.modules.groups.models import GroupType
from paper_scraper.modules.groups.schemas import (
    AddMembersRequest,
    GroupCreate,
    GroupDetail,
    GroupListResponse,
    GroupResponse,
    GroupUpdate,
    SuggestMembersRequest,
    SuggestMembersResponse,
)
from paper_scraper.modules.groups.service import GroupService

router = APIRouter()


def get_group_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> GroupService:
    return GroupService(db)


@router.get("/", response_model=GroupListResponse)
async def list_groups(
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
    type: GroupType | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List researcher groups."""
    return await service.list_groups(
        current_user.organization_id,
        group_type=type,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Create a new researcher group."""
    return await service.create_group(
        current_user.organization_id,
        current_user.id,
        data,
    )


@router.get("/{group_id}", response_model=GroupDetail)
async def get_group(
    group_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Get group details with members."""
    return await service.get_group(group_id, current_user.organization_id)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    data: GroupUpdate,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Update a group."""
    return await service.update_group(
        group_id, current_user.organization_id, data
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Delete a group."""
    await service.delete_group(group_id, current_user.organization_id)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_members(
    group_id: UUID,
    data: AddMembersRequest,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Add members to a group."""
    added = await service.add_members(
        group_id,
        current_user.organization_id,
        data.researcher_ids,
        current_user.id,
    )
    return {"added": added}


@router.delete("/{group_id}/members/{researcher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: UUID,
    researcher_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Remove a member from a group."""
    await service.remove_member(
        group_id, current_user.organization_id, researcher_id
    )


@router.post("/suggest-members", response_model=SuggestMembersResponse)
async def suggest_members(
    data: SuggestMembersRequest,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Get AI-suggested members based on keywords."""
    suggestions = await service.suggest_members(
        current_user.organization_id,
        data.keywords,
        data.target_size,
    )
    return SuggestMembersResponse(
        suggestions=suggestions,
        query_keywords=data.keywords,
    )


@router.get("/{group_id}/export")
async def export_group(
    group_id: UUID,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    """Export group members as CSV."""
    csv_data = await service.export_group(group_id, current_user.organization_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=group_{group_id}.csv"},
    )
```

---

### Task 16.5: Register Groups Router

**Update paper_scraper/api/v1/router.py:**
```python
from paper_scraper.modules.groups.router import router as groups_router

api_router.include_router(groups_router, prefix="/groups", tags=["groups"])
```

---

### Task 16.6: Tests

**File: tests/test_groups.py**
```python
"""Tests for researcher groups module."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/groups/",
        json={
            "name": "AI Researchers",
            "description": "Researchers working on AI",
            "type": "custom",
            "keywords": ["machine learning", "deep learning"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AI Researchers"
    assert data["type"] == "custom"


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/groups/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_add_members(client: AsyncClient, auth_headers: dict, test_group_id: str, test_researcher_id: str):
    response = await client.post(
        f"/api/v1/groups/{test_group_id}/members",
        json={"researcher_ids": [test_researcher_id]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["added"] == 1


@pytest.mark.asyncio
async def test_suggest_members(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/groups/suggest-members",
        json={"keywords": ["machine learning"], "target_size": 5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
```

---

### Sprint 16 Definition of Done

- [x] `researcher_groups` table created with migration
- [x] `group_members` table created with migration
- [x] GroupService with full CRUD operations
- [x] Groups router registered at `/api/v1/groups`
- [x] AI-powered member suggestions endpoint
- [x] CSV export functionality
- [x] Tests passing (51 tests, service + router + tenant isolation + error paths)
- [x] API documentation updated
- [x] Tenant isolation verified in `add_members()` (researcher org validation)
- [x] `GroupUpdate` name validation (min_length/max_length)

### Future Enhancements (identified during Sprint 16 review)

| ID | Enhancement | Priority | Description |
|----|-------------|----------|-------------|
| **GRP-F1** | Embedding-based member suggestions | HIGH | `suggest_members()` currently returns authors without relevance ranking. Implement pgvector embedding similarity search: generate embedding from keywords, find authors with similar paper embeddings, compute real relevance scores. Requires `suggest_members.jinja2` prompt template. |
| **GRP-F2** | CSV injection protection | MEDIUM | The CSV export endpoint writes user-controlled data (author names, affiliations) directly to CSV. Sanitize fields that begin with `=`, `+`, `-`, `@`, `\t`, `\r` to prevent formula injection in spreadsheet applications. |
| **GRP-F3** | Rate limiting on expensive endpoints | MEDIUM | `/suggest-members` and `/{id}/export` perform multiple DB queries. Add endpoint-specific rate limits (e.g., 10/min for suggestions, 30/min for exports) using the existing slowapi middleware. |
| **GRP-F4** | Bulk operations | LOW | Add batch add/remove members endpoint to reduce N+1 queries when managing large groups. Current implementation loops per-researcher with individual DB queries. |
| **GRP-F5** | Group analytics | LOW | Add member count trends, group activity metrics, and mailing list engagement tracking. Integrate with the existing analytics module dashboard. |
| **GRP-F6** | Audit logging for group operations | MEDIUM | Add audit log entries for group create/update/delete, member add/remove using the existing `audit` module. Important for compliance (Sprint 22). |

---

## Sprint 17: Technology Transfer Conversations ✅ COMPLETE

### Goal
Implement technology transfer conversation management with stage-based workflows, message threading, and AI-suggested next steps.

### User Stories
- **T1**: As a TTO staff, I want to track all conversations with researchers so I maintain context
- **T2**: As a user, I want to see suggested next steps so I know what actions to take
- **T3**: As a manager, I want to visualize conversation stages so I can monitor transfer progress
- **T4**: As a team, I want message templates so we can send consistent communications
- **T5**: As a user, I want to attach resources to conversations for easy reference
- **T6**: As a team, I want @mentions so I can involve colleagues in conversations

---

### Task 17.1: Transfer Conversation Models

**File: paper_scraper/modules/transfer/models.py**
```python
"""SQLAlchemy models for technology transfer."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from paper_scraper.core.database import Base


class TransferType(str, enum.Enum):
    """Type of technology transfer."""
    PATENT = "patent"
    LICENSING = "licensing"
    STARTUP = "startup"
    PARTNERSHIP = "partnership"
    OTHER = "other"


class TransferStage(str, enum.Enum):
    """Stage of transfer conversation."""
    INITIAL_CONTACT = "initial_contact"
    DISCOVERY = "discovery"
    EVALUATION = "evaluation"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TransferConversation(Base):
    """Technology transfer conversation."""

    __tablename__ = "transfer_conversations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    paper_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("papers.id", ondelete="SET NULL"), nullable=True
    )
    researcher_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("authors.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[TransferType] = mapped_column(
        Enum(TransferType), nullable=False
    )
    stage: Mapped[TransferStage] = mapped_column(
        Enum(TransferStage), default=TransferStage.INITIAL_CONTACT
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    created_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    resources: Mapped[list["ConversationResource"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    stage_history: Mapped[list["StageChange"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class ConversationMessage(Base):
    """Message in a transfer conversation."""

    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("transfer_conversations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sender_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[list] = mapped_column(JSONB, default=list)  # List of user IDs
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    conversation: Mapped["TransferConversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship("User")


class ConversationResource(Base):
    """Resource attached to a conversation."""

    __tablename__ = "conversation_resources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("transfer_conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # file, link, document
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["TransferConversation"] = relationship(back_populates="resources")


class StageChange(Base):
    """History of stage changes."""

    __tablename__ = "stage_changes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("transfer_conversations.id", ondelete="CASCADE")
    )
    from_stage: Mapped[TransferStage] = mapped_column(Enum(TransferStage))
    to_stage: Mapped[TransferStage] = mapped_column(Enum(TransferStage))
    changed_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["TransferConversation"] = relationship(back_populates="stage_history")


class MessageTemplate(Base):
    """Reusable message templates."""

    __tablename__ = "message_templates"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[TransferStage | None] = mapped_column(Enum(TransferStage), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

### Task 17.2-17.4: Service, Router, AI Next Steps

*(Similar pattern to Sprint 16 - implement service layer, router, and AI prompt for next-step suggestions)*

**Key Endpoints:**
```
GET    /api/v1/transfer/                    - List conversations
POST   /api/v1/transfer/                    - Create conversation
GET    /api/v1/transfer/{id}                - Get conversation detail
PATCH  /api/v1/transfer/{id}                - Update stage
POST   /api/v1/transfer/{id}/messages       - Add message
POST   /api/v1/transfer/{id}/resources      - Attach resource
GET    /api/v1/transfer/{id}/next-steps     - AI-suggested actions
GET    /api/v1/transfer/templates           - List templates
POST   /api/v1/transfer/templates           - Create template
POST   /api/v1/transfer/{id}/messages/from-template - Use template
```

---

## Sprint 18: Research Submission Portal ✅ COMPLETE

### Goal
Enable researchers to submit their own work for TTO review, with scoring and conversion to papers.

### User Stories
- **SUB1**: As a researcher, I want to submit my research for TTO review
- **SUB2**: As a researcher, I want to track the status of my submissions
- **SUB3**: As a researcher, I want AI analysis of my research's commercial potential

---

### Task 18.1: Submission Models

**Key tables:**
- `research_submissions` - Submission metadata
- `submission_attachments` - Uploaded files
- `submission_scores` - AI analysis results

**Key Endpoints:**
```
GET    /api/v1/submissions/my               - Researcher's submissions
POST   /api/v1/submissions/                 - Create submission
GET    /api/v1/submissions/{id}             - Get submission
PATCH  /api/v1/submissions/{id}             - Update draft
POST   /api/v1/submissions/{id}/submit      - Submit for review
POST   /api/v1/submissions/{id}/attachments - Upload files
GET    /api/v1/submissions/                 - All submissions (TTO only)
PATCH  /api/v1/submissions/{id}/review      - Approve/reject
POST   /api/v1/submissions/{id}/analyze     - AI scoring
POST   /api/v1/submissions/{id}/convert     - Convert to paper
```

### Future Enhancements (identified during Sprint 18 review)

| ID | Enhancement | Priority | Description |
|----|-------------|----------|-------------|
| **SUB-F1** | MinIO/S3 file storage | HIGH | Attachments are currently validated but not persisted to object storage. Integrate MinIO client in `router.py` upload endpoint to store files in `submissions/{org_id}/{submission_id}/` bucket path. |
| **SUB-F2** | Attachment download endpoint | HIGH | Add `GET /submissions/{id}/attachments/{attachment_id}/download` to serve files from MinIO with signed URLs or streaming response. |
| **SUB-F3** | Similar papers context for scoring | MEDIUM | `service.py:analyze_submission` passes `similar_papers=[]` to the scoring orchestrator. Use pgvector embedding search to find related papers and provide richer context for AI analysis. |
| **SUB-F4** | Stream-to-storage uploads | MEDIUM | Current upload reads file into memory (up to 50MB). Implement chunked streaming directly to MinIO to reduce memory pressure under concurrent uploads. |
| **SUB-F5** | Audit logging | MEDIUM | Add audit log entries for submission lifecycle events (create, submit, review, convert) using the existing `audit` module. |
| **SUB-F6** | Batch operations | LOW | Batch approve/reject for TTO reviewers processing multiple submissions. Batch export of submission data (CSV/PDF). |

---

## Sprint 19: Gamification & Knowledge Management ✅ COMPLETE

### Goal
Implement badge/achievement system and personal/organizational knowledge sources for AI personalization.

### User Stories
- **GA1-GA3**: Badge system, celebrations, progress tracking
- **KM1-KM2**: Personal and org knowledge sources

---

### Task 19.1: Badge System

**Key tables:**
- `badges` - Available badges with criteria
- `user_badges` - Earned badges

**Key Endpoints:**
```
GET    /api/v1/badges                       - All badges
GET    /api/v1/users/me/badges              - My badges
GET    /api/v1/users/me/stats               - My activity stats
```

---

### Task 19.2: Knowledge Sources

**Key tables:**
- `knowledge_sources` - Personal and org knowledge

**Key Endpoints:**
```
GET    /api/v1/knowledge/personal           - My knowledge sources
POST   /api/v1/knowledge/personal           - Add source
DELETE /api/v1/knowledge/personal/{id}      - Remove source
GET    /api/v1/knowledge/organization       - Org sources (admin)
POST   /api/v1/knowledge/organization       - Add org source (admin)
```

---

### Phase 4 Implementation Summary

**Completed**: All 4 sprints (16-19) are fully implemented with models, schemas, services, routers, and tests.

| Sprint | Tests | Migration | Status |
|--------|-------|-----------|--------|
| 16 - Groups | 34 pass | ✅ `20260205_0001_add_researcher_groups.py` | Complete |
| 17 - Transfer | 40 pass | ❌ **Missing** (see TD-006) | Complete (migration needed) |
| 18 - Submissions | 52 pass | ✅ `20260205_0002_add_research_submissions.py` | Complete |
| 19 - Badges/Knowledge | 60 pass | ✅ `20260205_0003_add_badges_and_knowledge.py` | Complete |

**Total Phase 4 tests**: 186 passing

**Deferred to future sprints:**
- AI-powered group member suggestions (AI-001) - currently returns mock data
- MinIO file storage for submissions and transfer resources (TD-004, TD-008)
- Automated badge awarding via background jobs or events (TD-009)
- Knowledge source integration with scoring pipeline (TD-010, AI-005)
- Granular RBAC for all new modules (SEC-F1, Sprint 22 scope)
- Audit logging for new modules (SEC-F3, Sprint 22 scope)
- Badge stats query optimization: 7 sequential COUNT queries in `get_user_stats()` (TD-011)
- Organization-level custom badges (TD-012)
- Search activity tracking for `searches_performed` stat (TD-013)
- Pagination support for badge and knowledge list endpoints (TD-014)

---

# Phase 5: Stabilization & Frontend Integration (Sprints 20-21)

---

## Sprint 20: Critical Fixes & Deployment Readiness

### Goal
Fix blocking deployment issues and broken features from Phase 4. This is a short stabilization sprint.

### Resolves
- **TD-006** (HIGH): Transfer module missing Alembic migration
- **TD-004** (HIGH): Submission file uploads not persisted
- **TD-008** (MEDIUM): Transfer resource file storage missing

### Duration
1 week

---

### Task 20.1: Transfer Module Migration (TD-006)

The transfer module (Sprint 17) has no Alembic migration. Tables `transfer_conversations`, `conversation_messages`, `conversation_resources`, `stage_changes`, and `message_templates` will not exist on a fresh deploy.

**Steps:**
1. Ensure PostgreSQL + all models imported in `alembic/env.py`
2. Run `alembic revision --autogenerate -m "add_transfer_conversations"`
3. Review generated migration for correctness
4. Verify `alembic upgrade head` succeeds on a clean database

**Verification:**
```bash
alembic upgrade head
# All tables should be created including transfer_* tables
```

---

### Task 20.2: MinIO/S3 File Storage Service

Create a shared file storage utility for both submissions and transfer resources.

**File: paper_scraper/core/storage.py**
```python
"""S3-compatible file storage service (MinIO)."""

from uuid import UUID
import boto3
from botocore.exceptions import ClientError
from paper_scraper.core.config import settings


class StorageService:
    """Service for file upload/download to S3-compatible storage."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        )
        self.bucket = settings.MINIO_BUCKET

    async def upload_file(
        self, file_content: bytes, key: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file and return the storage key."""
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=file_content, ContentType=content_type
        )
        return key

    async def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed download URL."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def delete_file(self, key: str) -> None:
        """Delete a file from storage."""
        self.client.delete_object(Bucket=self.bucket, Key=key)
```

---

### Task 20.3: Integrate File Storage into Submissions (TD-004)

Update `submissions/router.py` to persist uploaded files using `StorageService`:
- Store files to MinIO under `submissions/{submission_id}/{filename}`
- Save the storage key in `SubmissionAttachment.file_path`
- Add download endpoint for submission attachments

**Updated endpoints:**
```
POST   /api/v1/submissions/{id}/attachments             - Upload file to MinIO
GET    /api/v1/submissions/{id}/attachments/{aid}/download - Download attachment
```

---

### Task 20.4: Integrate File Storage into Transfer Resources (TD-008)

Update `transfer/router.py` to support file uploads for conversation resources:
- Store files to MinIO under `transfer/{conversation_id}/{filename}`
- Save the storage key in `ConversationResource.file_path`
- Add download endpoint for resources

**Updated endpoints:**
```
POST   /api/v1/transfer/{id}/resources/upload        - Upload resource file
GET    /api/v1/transfer/{id}/resources/{rid}/download - Download resource
```

---

### Task 20.5: Verification

```bash
# Run migrations
alembic upgrade head

# Run existing tests
pytest tests/ -v

# Verify MinIO integration
# Upload a test file via submissions endpoint
# Download it back and verify content matches
```

---

## Sprint 21: Phase 4 Frontend Integration

### Goal
Build frontend pages for all Phase 4 backend modules (groups, transfer, submissions, badges, knowledge). These backends were implemented in Sprints 16-19 but have no UI.

### User Stories
- **G1-G4**: Researcher group management UI
- **T1-T6**: Technology transfer conversation UI
- **SUB1-SUB3**: Research submission portal UI
- **GA1, GA3**: Badges and gamification display
- **KM1-KM2**: Knowledge management UI

### Duration
2 weeks

---

### Task 21.1: TanStack Query Hooks for New Modules

Create hooks following existing patterns in `frontend/src/hooks/`:

**File: frontend/src/hooks/useGroups.ts**
- `useGroups()`, `useGroup(id)`, `useCreateGroup()`, `useUpdateGroup()`, `useDeleteGroup()`
- `useGroupMembers(id)`, `useAddMembers()`, `useRemoveMembers()`
- `useSuggestMembers(groupId, keywords)`

**File: frontend/src/hooks/useTransfer.ts**
- `useConversations()`, `useConversation(id)`, `useCreateConversation()`
- `useConversationMessages(id)`, `useSendMessage()`
- `useStageChanges(id)`, `useChangeStage()`
- `useNextSteps(id)`, `useMessageTemplates()`

**File: frontend/src/hooks/useSubmissions.ts**
- `useSubmissions()`, `useSubmission(id)`, `useCreateSubmission()`
- `useUpdateSubmissionStatus()`, `useSubmissionScore(id)`
- `useUploadAttachment()`, `useAnalyzeSubmission()`

**File: frontend/src/hooks/useBadges.ts**
- `useBadges()`, `useUserBadges(userId)`, `useUserStats()`
- `useBadgeLeaderboard()`

**File: frontend/src/hooks/useKnowledge.ts**
- `useKnowledgeSources()`, `useCreateKnowledgeSource()`
- `useUpdateKnowledgeSource()`, `useDeleteKnowledgeSource()`

---

### Task 21.2: Researcher Groups Page

**File: frontend/src/pages/GroupsPage.tsx**
- List all researcher groups with member counts and type badges (custom, mailing_list, speaker_pool)
- Create group dialog (name, description, type)
- Group detail view with member list
- Add/remove members interface
- AI-powered member suggestions (calls `suggest_members` endpoint)
- Export group as CSV

**Sidebar navigation:** Add "Groups" link under "Authors" section

---

### Task 21.3: Technology Transfer Page

**File: frontend/src/pages/TransferPage.tsx**
- List conversations with stage badges and status indicators
- Create new conversation (link to researcher, paper, transfer type)

**File: frontend/src/pages/TransferDetailPage.tsx**
- Stage-based workflow visualization (pipeline/timeline)
- Message thread with sender identification
- Attached resources list with file upload
- AI-suggested next steps panel
- Stage change with notes
- Message templates dropdown

**Sidebar navigation:** Add "Transfer" as main section

---

### Task 21.4: Research Submissions Page

**File: frontend/src/pages/SubmissionsPage.tsx**
- List submissions with status badges (draft, submitted, under_review, approved, rejected, converted)
- Create submission form (title, abstract, research_area, keywords, attachments)
- Submission detail with:
  - Status workflow visualization
  - AI analysis results and commercialization score
  - File attachments with download
  - Reviewer actions (approve/reject/request changes)
- "My Submissions" filter tab for researchers

**Sidebar navigation:** Add "Submissions" under main section

---

### Task 21.5: Badges & Gamification Page

**File: frontend/src/pages/BadgesPage.tsx**
- Badge gallery showing all available badges by category (import, scoring, collaboration, exploration, milestone)
- Earned vs locked badge visualization
- User stats dashboard (papers_imported, papers_scored, etc.)
- Leaderboard table
- Badge detail with criteria description and tier progress (bronze/silver/gold/platinum)

**Sidebar navigation:** Add "Badges" under user section or as a profile tab

---

### Task 21.6: Knowledge Management Page

**File: frontend/src/pages/KnowledgePage.tsx**
- List knowledge sources (personal + organizational)
- Create/edit knowledge source form (name, type, content, scope)
- Source types: research_focus, industry_context, evaluation_criteria, domain_expertise
- Scope toggle: personal vs organizational (admin only for organizational)
- Delete with confirmation

**Sidebar navigation:** Add "Knowledge" under settings section

---

### Task 21.7: Sidebar & Router Updates

**File: frontend/src/components/layout/Sidebar.tsx**
- Add navigation items for Groups, Transfer, Submissions, Badges, Knowledge

**File: frontend/src/App.tsx**
- Add routes for all new pages
- Wrap in ProtectedRoute

---

### Task 21.8: Verification

```bash
cd frontend && npm run build
cd frontend && npx tsc --noEmit
cd frontend && npm test
npx playwright test
```

---

# Phase 6: Security & AI Advancement (Sprints 22-24)

---

## Sprint 22: Security Hardening & RBAC

### Goal
Implement granular role-based access control, extend audit logging to all modules, and fix security gaps.

### Resolves
- **SEC-F1** (HIGH): Granular RBAC
- **SEC-F2** (MEDIUM): CSV injection protection
- **SEC-F3** (MEDIUM): Audit logging for new modules

### User Stories
- **C1**: Audit logs for compliance
- **C3**: Role-based access control

### Duration
2 weeks

---

### Task 22.1: RBAC Permissions System

**File: paper_scraper/core/permissions.py**
```python
"""Role-based access control system."""

from enum import Enum
from fastapi import HTTPException, status

class Permission(str, Enum):
    PAPERS_READ = "papers:read"
    PAPERS_WRITE = "papers:write"
    PAPERS_DELETE = "papers:delete"
    SCORING_TRIGGER = "scoring:trigger"
    GROUPS_READ = "groups:read"
    GROUPS_MANAGE = "groups:manage"
    TRANSFER_READ = "transfer:read"
    TRANSFER_MANAGE = "transfer:manage"
    SUBMISSIONS_READ = "submissions:read"
    SUBMISSIONS_REVIEW = "submissions:review"
    BADGES_MANAGE = "badges:manage"
    KNOWLEDGE_MANAGE = "knowledge:manage"
    SETTINGS_ADMIN = "settings:admin"
    COMPLIANCE_VIEW = "compliance:view"
    DEVELOPER_MANAGE = "developer:manage"

ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    "admin": list(Permission),  # all permissions
    "manager": [
        Permission.PAPERS_READ, Permission.PAPERS_WRITE,
        Permission.SCORING_TRIGGER,
        Permission.GROUPS_READ, Permission.GROUPS_MANAGE,
        Permission.TRANSFER_READ, Permission.TRANSFER_MANAGE,
        Permission.SUBMISSIONS_READ, Permission.SUBMISSIONS_REVIEW,
        Permission.KNOWLEDGE_MANAGE, Permission.COMPLIANCE_VIEW,
    ],
    "tto_manager": [
        Permission.PAPERS_READ, Permission.PAPERS_WRITE, Permission.PAPERS_DELETE,
        Permission.SCORING_TRIGGER,
        Permission.GROUPS_READ, Permission.GROUPS_MANAGE,
        Permission.TRANSFER_READ, Permission.TRANSFER_MANAGE,
        Permission.SUBMISSIONS_READ, Permission.SUBMISSIONS_REVIEW,
    ],
    "tto_staff": [
        Permission.PAPERS_READ, Permission.PAPERS_WRITE,
        Permission.SCORING_TRIGGER, Permission.GROUPS_READ,
        Permission.TRANSFER_READ, Permission.TRANSFER_MANAGE,
        Permission.SUBMISSIONS_READ,
    ],
    "member": [
        Permission.PAPERS_READ, Permission.PAPERS_WRITE,
        Permission.SCORING_TRIGGER, Permission.GROUPS_READ,
        Permission.TRANSFER_READ, Permission.SUBMISSIONS_READ,
    ],
    "researcher": [
        Permission.PAPERS_READ, Permission.GROUPS_READ,
        Permission.SUBMISSIONS_READ,
    ],
    "viewer": [
        Permission.PAPERS_READ, Permission.GROUPS_READ,
    ],
}

def require_permission(*permissions: Permission):
    """FastAPI dependency that checks user has required permissions."""
    # Check current_user.role against ROLE_PERMISSIONS
    ...
```

---

### Task 22.2: Apply RBAC to All Routers

Add `require_permission()` dependency to all endpoints:
- `groups/router.py` - `groups:read` for GET, `groups:manage` for POST/PATCH/DELETE
- `transfer/router.py` - `transfer:read` for GET, `transfer:manage` for mutations
- `submissions/router.py` - `submissions:read` for GET, `submissions:review` for status changes
- `badges/router.py` - `badges:manage` for create/update/delete (admin only)
- `knowledge/router.py` - `knowledge:manage` for organizational scope mutations
- `scoring/router.py` - `scoring:trigger` for score/classify endpoints
- `papers/router.py` - `papers:delete` restricted to admin/tto_manager

**New endpoints:**
```
GET    /api/v1/auth/permissions         - List current user's permissions
GET    /api/v1/auth/roles               - List available roles and their permissions
```

---

### Task 22.3: Audit Logging for New Modules (SEC-F3)

Integrate audit logging into modules that currently don't emit events:
- **groups**: Group create/update/delete, member add/remove
- **transfer**: Conversation create, stage change, message send
- **submissions**: Submission create, status change, review actions
- **badges**: Badge award events
- **knowledge**: Source create/update/delete

Use existing `audit/service.py` patterns. Add new `AuditAction` enum values as needed.

---

### Task 22.4: CSV Injection Protection (SEC-F2)

**File: paper_scraper/core/csv_utils.py**
```python
"""CSV export utilities with injection protection."""

def sanitize_csv_field(value: str) -> str:
    """Prefix dangerous characters to prevent formula injection."""
    if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{value}"
    return value
```

Apply to:
- `export/service.py` - CSV export
- `groups/service.py` - Group member CSV export

---

### Task 22.5: Permissions UI

Update `frontend/src/pages/OrganizationSettingsPage.tsx`:
- Show permission matrix for each role
- Display current user's effective permissions
- Admin: visual indicator of what each role can/cannot do

---

### Task 22.6: Verification

```bash
pytest tests/test_permissions.py -v
# Verify unauthorized access is denied per role
npx playwright test --grep "rbac"
```

---

### Sprint 22 Implementation Summary

**Status: ✅ Complete**

**Files Created:**
- `paper_scraper/core/permissions.py` — Permission enum (15 permissions), ROLE_PERMISSIONS mapping, `check_permission()`, `get_permissions_for_role()`
- `paper_scraper/core/csv_utils.py` — `sanitize_csv_field()` with pipe/newline protection
- `tests/test_permissions.py` — 21 tests (unit + integration + enforcement)
- `tests/test_csv_utils.py` — 15 tests

**Files Modified:**
- `paper_scraper/api/dependencies.py` — Added `require_permission()` factory
- `paper_scraper/modules/audit/models.py` — 14 new AuditAction enum values
- `paper_scraper/modules/groups/router.py` — RBAC + audit logging (with Request context)
- `paper_scraper/modules/transfer/router.py` — RBAC + audit logging
- `paper_scraper/modules/submissions/router.py` — RBAC + audit logging
- `paper_scraper/modules/knowledge/router.py` — RBAC + audit logging
- `paper_scraper/modules/scoring/router.py` — RBAC enforcement
- `paper_scraper/modules/papers/router.py` — RBAC on delete
- `paper_scraper/modules/auth/router.py` — `/permissions` and `/roles` (admin-only) endpoints
- `paper_scraper/modules/export/service.py` — CSV sanitization
- `paper_scraper/modules/groups/service.py` — CSV sanitization in export
- `frontend/src/pages/OrganizationSettingsPage.tsx` — PermissionMatrix with error state, deterministic role ordering, staleTime
- `frontend/src/lib/api.ts` — `getMyPermissions()`, `getRoles()` methods

**Security Fixes Applied (from review):**
- SEC-22-01: Generic ForbiddenError message (no permission name leakage)
- SEC-22-02: `/roles` endpoint restricted to admin-only
- SEC-22-05: CSV sanitization handles `|` pipe and embedded newlines
- Audit logging added to `update_group` (was missing)
- All group audit calls include `request=` for IP/user-agent tracking

**Test Results:** 35 passed, frontend build clean

**Known Deferred Items (future sprints):**
- RBAC coverage for pre-existing routers (projects, export, search, analytics)
- `BADGES_MANAGE`, `SETTINGS_ADMIN`, `COMPLIANCE_VIEW`, `DEVELOPER_MANAGE` permissions defined but not yet enforced on endpoints
- Audit logging for transfer templates, resources, and project operations

---

## Sprint 23: 6-Dimension Scoring + Model Settings

### Goal
Complete the innovation radar with a 6th scoring dimension (Team Readiness) and add multi-model AI configuration.

### Resolves
- **AI-003**: Team Readiness scoring dimension

### User Stories
- **P2**: 6-dimension innovation radar
- **M1-M4**: Model selection, usage tracking, data ownership

### Duration
2 weeks

---

### Task 23.1: Team Readiness Scoring Dimension

**File: paper_scraper/modules/scoring/prompts/team_readiness.jinja2**
```jinja2
You are an expert in evaluating research team readiness for commercialization.

Analyze the following research paper and its authors:

Paper Title: {{ paper.title }}
Abstract: {{ paper.abstract }}

Authors:
{% for author in authors %}
- {{ author.name }} (h-index: {{ author.h_index or 'N/A' }}, publications: {{ author.works_count or 'N/A' }})
  Affiliations: {{ author.affiliations | join(', ') }}
{% endfor %}

Evaluate the team's readiness for commercialization on these criteria:
1. Track record of successful research
2. Industry collaboration experience
3. Institutional support indicators
4. Team composition and complementary skills
5. Prior commercialization experience

Respond in JSON:
{
  "score": <0-10>,
  "evidence": ["...", "..."],
  "strengths": ["...", "..."],
  "gaps": ["...", "..."],
  "explanation": "..."
}
```

**File: paper_scraper/modules/scoring/dimensions/team_readiness.py**
- Load author metrics from the database (h-index, works_count, affiliations)
- Render prompt with author data
- Call LLM and parse response
- Follow existing dimension scorer pattern (see `novelty.py`)

**Migration:** Add `team_readiness` column to `paper_scores` table.

**Update `orchestrator.py`:** Register 6th dimension in scoring pipeline.

**Update `schemas.py`:** Add `team_readiness` field to score schemas.

---

### Task 23.2: Innovation Radar Chart Component

**File: frontend/src/components/InnovationRadar.tsx**
- 6-axis radar/spider chart showing all scoring dimensions
- Dimensions: Novelty, IP Potential, Marketability, Feasibility, Commercialization, Team Readiness
- Use recharts or chart.js for rendering
- Show on PaperDetailPage
- Tooltip with dimension explanations

---

### Task 23.3: Model Configuration Backend

**New module: paper_scraper/modules/model_settings/**

**Models:**
```python
class ModelConfiguration(Base):
    """AI model configuration per organization."""
    __tablename__ = "model_configurations"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    provider: Mapped[str]          # openai, anthropic, azure, ollama
    model_name: Mapped[str]        # gpt-5-mini, claude-sonnet-4-5-20250929, etc.
    is_default: Mapped[bool]
    api_key_encrypted: Mapped[str | None]
    hosting_info: Mapped[dict]     # region, compliance details
    max_tokens: Mapped[int]
    temperature: Mapped[float]
    created_at: Mapped[datetime]

class ModelUsage(Base):
    """Track model usage and costs per organization."""
    __tablename__ = "model_usage"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    model_configuration_id: Mapped[UUID]
    user_id: Mapped[UUID]
    operation: Mapped[str]         # scoring, pitch, classification, embedding
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    cost_usd: Mapped[float]
    created_at: Mapped[datetime]
```

**Endpoints:**
```
GET    /api/v1/settings/models              - List configured models
POST   /api/v1/settings/models              - Add model configuration (admin)
PATCH  /api/v1/settings/models/{id}         - Update model config
DELETE /api/v1/settings/models/{id}         - Remove model config
GET    /api/v1/settings/models/usage        - Usage stats (aggregated)
GET    /api/v1/settings/models/{id}/hosting - Hosting/compliance info
```

**Migration:** `alembic revision --autogenerate -m "add_model_configurations"`

---

### Task 23.4: Usage Tracking Integration

Update `scoring/llm_client.py` to log every LLM call to `ModelUsage`:
- Record input/output tokens
- Calculate cost based on model pricing
- Associate with user and operation type

---

### Task 23.5: Model Settings Frontend Page

**File: frontend/src/pages/ModelSettingsPage.tsx**
- List configured models with provider icons
- Add/edit model configuration form
- Set default model
- Usage dashboard: charts showing token usage, cost over time, by operation type
- Hosting information display (where data is processed)
- Data ownership settings

**File: frontend/src/hooks/useModelSettings.ts**

**Sidebar navigation:** Add "Model Settings" under settings section (admin only)

---

## Sprint 24: AI Intelligence Enhancements

### Goal
Upgrade AI-powered features across all modules with real embedding-based intelligence.

### Resolves
- **AI-001** (HIGH): Real embedding-based group member suggestions
- **AI-002** (MEDIUM): pgvector similar papers for submission analysis
- **AI-004** (MEDIUM): Enhanced transfer next-steps AI
- **AI-005** / **TD-010** (LOW/MEDIUM): Knowledge-enhanced scoring
- **TD-009** (MEDIUM): Badge auto-award engine

### Duration
2 weeks

---

### Task 24.1: Embedding-Based Group Member Suggestions (AI-001)

**File: paper_scraper/modules/scoring/prompts/suggest_members.jinja2**
```jinja2
Given the following research group description and keywords, suggest researchers
who would be a good fit based on their expertise and publication history.

Group: {{ group.name }}
Description: {{ group.description }}
Keywords: {{ keywords | join(', ') }}

Candidate researchers:
{% for author in candidates %}
- {{ author.name }}: {{ author.affiliations | join(', ') }}
  Recent topics: {{ author.recent_keywords | join(', ') }}
{% endfor %}

Rank the top candidates and explain why they fit.
```

**Implementation in `groups/service.py`:**
1. Generate embedding for group keywords
2. Use pgvector to find authors with similar research embeddings
3. Optionally pass top candidates through LLM for explanation
4. Replace current mock `suggest_members()` implementation

---

### Task 24.2: Similar Papers for Submission Analysis (AI-002)

**Update `submissions/service.py:analyze_submission()`:**
1. Generate embedding for submission abstract
2. Use pgvector cosine similarity to find top-5 related papers
3. Pass similar papers as context to the analysis prompt
4. Return richer analysis with comparison to existing research

---

### Task 24.3: Enhanced Transfer Next-Steps AI (AI-004)

**Update `transfer/service.py:get_next_steps()`:**
1. Include full conversation history (last N messages) in prompt
2. Add stage-specific suggestion templates
3. Recommend message templates based on current stage and transfer type
4. Consider researcher profile and paper context

---

### Task 24.4: Badge Auto-Award Engine (TD-009)

**File: paper_scraper/jobs/badges.py**
```python
"""Background job for automated badge awarding."""

BADGE_CRITERIA = {
    "first_import": {"stat": "papers_imported", "threshold": 1, "tier": "bronze"},
    "import_veteran": {"stat": "papers_imported", "threshold": 50, "tier": "silver"},
    "scoring_initiate": {"stat": "papers_scored", "threshold": 1, "tier": "bronze"},
    "scoring_master": {"stat": "papers_scored", "threshold": 100, "tier": "gold"},
    "collaborator": {"stat": "groups_created", "threshold": 5, "tier": "silver"},
}

async def check_and_award_badges(ctx, user_id: str, org_id: str):
    """Check user stats against badge criteria and award earned badges."""
    ...
```

**Integration points:**
- After paper import: trigger badge check
- After scoring: trigger badge check
- After group creation: trigger badge check
- Register in `jobs/worker.py`

---

### Task 24.5: Knowledge-Enhanced Scoring (TD-010, AI-005)

**Update scoring pipeline to inject knowledge context:**
1. Before scoring a paper, query knowledge sources for the organization
2. Filter by relevance (match knowledge source type to scoring dimension)
3. Inject relevant knowledge into scoring prompts as additional context

```python
# scoring/orchestrator.py
knowledge_sources = await knowledge_service.get_relevant_sources(db, org_id, paper.keywords)
scoring_context = {
    "industry_context": [ks.content for ks in knowledge_sources if ks.type == "industry_context"],
    "evaluation_criteria": [ks.content for ks in knowledge_sources if ks.type == "evaluation_criteria"],
}
```

---

# Phase 7: Platform & Developer Experience (Sprints 25-27)

---

## Sprint 25: Developer API & Repository Management

### Goal
Enable external integrations via API keys, webhooks, and MCP server protocol support. Make data source configuration dynamic.

### User Stories
- **D1-D3**: API keys, MCP servers, webhooks
- **RS1-RS3**: Repository source configuration

### Duration
2 weeks

### Priority Order
1. **API Key Management** (HIGH) - Enables programmatic access
2. **MCP Server Protocol** (HIGH) - Enables AI agent integrations (Claude Code, etc.)
3. **Webhook Integrations** (MEDIUM) - Event-driven external notifications
4. **Repository Sources** (MEDIUM) - Dynamic data source management

---

### Task 25.1: API Key Management

**New module: paper_scraper/modules/developer/**

**Models:**
```python
class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    created_by_id: Mapped[UUID]
    name: Mapped[str]              # Descriptive name
    key_hash: Mapped[str]          # SHA-256 hash (never store plaintext)
    key_prefix: Mapped[str]        # First 8 chars for identification
    permissions: Mapped[list]      # List of Permission enums
    expires_at: Mapped[datetime | None]
    last_used_at: Mapped[datetime | None]
    is_active: Mapped[bool]
    created_at: Mapped[datetime]
```

**Endpoints:**
```
GET    /api/v1/developer/api-keys           - List keys (shows prefix only)
POST   /api/v1/developer/api-keys           - Generate key (returns full key ONCE)
DELETE /api/v1/developer/api-keys/{id}      - Revoke key
```

**API key authentication middleware:** Accept `X-API-Key` header, hash and look up in database.

---

### Task 25.1b: MCP Server Protocol Support

**Goal:** Enable AI agents (Claude Code, GPT, etc.) to interact with Paper Scraper via MCP (Model Context Protocol).

**File: paper_scraper/mcp/server.py**
```python
"""MCP Server for Paper Scraper - enables AI agent integrations."""

from mcp.server import Server
from mcp.types import Tool, Resource

app = Server("paper-scraper")

# Tools for AI agents
@app.tool("search_papers")
async def search_papers(query: str, mode: str = "hybrid") -> list:
    """Search the paper library."""
    ...

@app.tool("get_paper_details")
async def get_paper_details(paper_id: str) -> dict:
    """Get full paper details including scores."""
    ...

@app.tool("score_paper")
async def score_paper(paper_id: str) -> dict:
    """Trigger AI scoring for a paper."""
    ...

@app.tool("import_paper_by_doi")
async def import_paper(doi: str) -> dict:
    """Import a paper by DOI."""
    ...

# Resources for context
@app.resource("papers")
async def list_papers() -> list:
    """List recent papers in the library."""
    ...
```

**Authentication:** Uses API key from Task 25.1 via `X-API-Key` header.

**MCP Tools exposed:**
- `search_papers` - Search with filters
- `get_paper_details` - Full paper info
- `score_paper` - Trigger scoring
- `import_paper_by_doi` - Import paper
- `list_projects` - List KanBan projects
- `move_paper_stage` - Move paper in pipeline

**Deployment:** Can run as standalone MCP server or embedded in main API.

---

### Task 25.2: Webhook Configuration

**Models:**
```python
class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    url: Mapped[str]
    events: Mapped[list]           # ["paper.created", "paper.scored", "submission.created", ...]
    secret: Mapped[str]            # HMAC signing secret
    is_active: Mapped[bool]
    last_triggered_at: Mapped[datetime | None]
    failure_count: Mapped[int]
    created_at: Mapped[datetime]
```

**Endpoints:**
```
GET    /api/v1/developer/webhooks           - List webhooks
POST   /api/v1/developer/webhooks           - Create webhook
PATCH  /api/v1/developer/webhooks/{id}      - Update webhook
POST   /api/v1/developer/webhooks/{id}/test - Send test event
DELETE /api/v1/developer/webhooks/{id}      - Delete webhook
```

**Webhook dispatch:** Fire-and-forget via arq job, HMAC signature, retry with exponential backoff (3 attempts), auto-disable after 10 consecutive failures.

---

### Task 25.3: Repository Source Management

**Models:**
```python
class RepositorySource(Base):
    __tablename__ = "repository_sources"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    name: Mapped[str]              # e.g., "OpenAlex - Biotech"
    provider: Mapped[str]          # openalex, pubmed, arxiv, crossref
    config: Mapped[dict]           # Provider-specific settings (query, filters)
    schedule: Mapped[str | None]   # cron expression for auto-sync
    is_active: Mapped[bool]
    last_sync_at: Mapped[datetime | None]
    last_sync_result: Mapped[dict | None]
    created_at: Mapped[datetime]
```

**Endpoints:**
```
GET    /api/v1/repositories/                - List sources
POST   /api/v1/repositories/                - Add source
PATCH  /api/v1/repositories/{id}            - Update source
POST   /api/v1/repositories/{id}/sync       - Trigger manual sync
GET    /api/v1/repositories/{id}/status     - Sync status
DELETE /api/v1/repositories/{id}            - Remove source
```

---

### Task 25.4: Developer Settings Frontend Page

**File: frontend/src/pages/DeveloperSettingsPage.tsx**
- **API Keys tab**: List keys, generate new, revoke existing. Show key only once on creation.
- **Webhooks tab**: Configure webhook URLs, select events, test delivery.
- **Repositories tab**: Configure data sources with sync schedules, trigger manual sync.

**File: frontend/src/hooks/useDeveloper.ts**

**Migration:** `alembic revision --autogenerate -m "add_api_keys_webhooks_repositories"`

---

## Sprint 26: UX Polish & Keyboard Navigation

### Goal
Add power-user features: command palette, keyboard shortcuts, notification inbox, search enhancements, and mobile responsiveness.

### User Stories
- **KB1**: Command palette (Cmd+K / Ctrl+K)
- **KB2**: Keyboard shortcuts for common actions
- **KB3**: Accessibility / screen reader support
- **S3**: Search result preview panel
- **N3**: Click alerts to navigate to items
- **K3, GA2**: Celebration animations
- **UX1** (NEW): Mobile-responsive dashboard and key pages

### Duration
2 weeks

### Priority Order
1. **Command Palette** (HIGH) - Power-user productivity boost
2. **Notification Center** (HIGH) - User engagement
3. **Mobile Responsiveness** (HIGH) - Accessibility for on-the-go usage
4. **Keyboard Shortcuts** (MEDIUM) - Power-user efficiency
5. **Search Preview Panel** (MEDIUM) - Faster paper evaluation
6. **Celebration Animations** (LOW) - Delight factor

---

### Task 26.1: Command Palette

**File: frontend/src/components/CommandPalette.tsx**
- Global shortcut: `Cmd+K` / `Ctrl+K`
- Search across: pages, papers, projects, authors, groups, settings
- Recent items section
- Action shortcuts (e.g., "New project", "Import paper")
- Keyboard navigation: arrow keys, enter to select, escape to close
- Use cmdk library or build custom with Radix Dialog

**Integration:** Mount in App.tsx as a global component.

---

### Task 26.2: Global Keyboard Shortcuts

**File: frontend/src/hooks/useKeyboardShortcuts.ts**
```typescript
const SHORTCUTS = {
  "g d": "Navigate to Dashboard",
  "g p": "Navigate to Papers",
  "g k": "Navigate to Projects (KanBan)",
  "g s": "Navigate to Search",
  "g a": "Navigate to Analytics",
  "g t": "Navigate to Transfer",
  "n p": "New Paper Import",
  "n j": "New Project",
  "/": "Focus search",
  "?": "Show keyboard shortcuts help",
};
```

**File: frontend/src/components/KeyboardShortcutsDialog.tsx**
- Shows all available shortcuts in a modal
- Triggered by `?` key or from help menu

---

### Task 26.3: Notification Center / Alert Inbox

**File: frontend/src/components/NotificationCenter.tsx**
- Dropdown in Navbar (bell icon with unread count badge)
- Alert timeline: chronological list of triggered alerts
- Each alert shows: type icon, title, timestamp, score badge (if paper alert)
- Click to navigate to the relevant item
- Mark as read/unread
- "View all" link to dedicated alerts page

**File: frontend/src/pages/NotificationsPage.tsx**
- Full-page view of all notifications/alerts
- Filter by type, importance flags
- Bulk mark as read

---

### Task 26.4: Search Result Preview Panel

Update **frontend/src/pages/SearchPage.tsx**:
- Split layout: results list on left, preview panel on right
- Clicking a result shows full details in preview without navigating away
- Preview panel shows: full abstract, scores, authors, actions
- Keyboard navigation: up/down to move through results

---

### Task 26.5: Celebration Animations

**File: frontend/src/components/CelebrationOverlay.tsx**
- Confetti animation (use canvas-confetti or react-confetti)
- Trigger conditions: complete KanBan batch, earn badge, high-score paper, complete onboarding
- Brief, non-blocking overlay

---

### Task 26.6: Mobile Responsiveness

**Priority pages to make mobile-friendly:**
1. **Dashboard** - Stack cards vertically, collapsible quick actions
2. **Papers List** - Card view instead of table on mobile
3. **Paper Detail** - Full-width scores, collapsible sections
4. **Search** - Full-width search bar, stacked filters
5. **Sidebar** - Bottom navigation on mobile, hamburger menu

**Implementation approach:**
- TailwindCSS responsive utilities (`sm:`, `md:`, `lg:`)
- `useMobileBreakpoint()` hook for conditional rendering
- Touch-friendly targets (min 44px tap area)
- Swipe gestures for KanBan on touch devices

**File: frontend/src/hooks/useMobileBreakpoint.ts**
```typescript
export function useMobileBreakpoint() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  // ... resize listener
  return isMobile;
}
```

---

## Sprint 27: Analytics & Reporting Expansion

### Goal
Add advanced analytics views: innovation funnel, benchmarks, scheduled reports, and peer comparisons.

### User Stories
- **A2**: Innovation funnel visualization
- **A4**: Scheduled/recurring reports
- **A5**: Benchmark comparisons
- **S4**: Peer comparison charts

### Duration
2 weeks

---

### Task 27.1: Innovation Funnel Tab

**Update frontend/src/pages/AnalyticsPage.tsx** - Add "Innovation Funnel" tab:
- Funnel visualization: Papers Imported -> Screened -> Scored -> In Pipeline -> Contacted -> Transferred
- Show conversion rates between stages
- Filter by time period and project

**Backend endpoint:**
```
GET /api/v1/analytics/funnel?project_id=...&start_date=...&end_date=...
```

---

### Task 27.2: Benchmark Comparisons Tab

**Update frontend/src/pages/AnalyticsPage.tsx** - Add "Benchmarks" tab:
- Compare organization metrics against aggregated anonymized averages
- Metrics: papers per month, scoring velocity, pipeline conversion rate
- Bar charts showing org vs. benchmark

**Backend endpoint:**
```
GET /api/v1/analytics/benchmarks
```

---

### Task 27.3: Scheduled Reports

**Models:**
```python
class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    created_by_id: Mapped[UUID]
    name: Mapped[str]
    report_type: Mapped[str]       # dashboard_summary, paper_trends, team_activity
    schedule: Mapped[str]          # cron expression
    recipients: Mapped[list]       # email addresses
    filters: Mapped[dict]
    format: Mapped[str]            # pdf, csv
    is_active: Mapped[bool]
    last_sent_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
```

**Endpoints:**
```
GET    /api/v1/reports/scheduled           - List scheduled reports
POST   /api/v1/reports/scheduled           - Create scheduled report
PATCH  /api/v1/reports/scheduled/{id}      - Update report config
DELETE /api/v1/reports/scheduled/{id}      - Delete scheduled report
POST   /api/v1/reports/scheduled/{id}/run  - Run report immediately
```

**Background job:** `jobs/reports.py` - arq cron job that checks for due reports and generates/emails them.

---

### Task 27.4: Peer Comparison Charts

**Update frontend/src/pages/SearchPage.tsx:**
- "Compare" button to select 2-5 papers for side-by-side comparison
- Radar chart overlay of selected papers' scores
- Table comparison of key metrics

---

# Phase 8: Enterprise Readiness (Sprints 28-30)

---

## Sprint 28: Compliance, Governance & Data Retention

### Goal
Enterprise compliance features: enhanced audit logging, data retention policies, compliance dashboard, and SOC2 preparation.

### User Stories
- **C1**: Audit logs for compliance reporting
- **C2**: GDPR data processing transparency
- **C3** (NEW): SOC2 Type II preparation checklist

### Duration
2 weeks

### Priority Order
1. **Enhanced Audit Logging** (HIGH) - Compliance foundation
2. **Data Retention Policies** (HIGH) - GDPR/regulatory requirement
3. **Compliance Dashboard** (MEDIUM) - Admin visibility
4. **SOC2 Preparation** (MEDIUM) - Enterprise readiness

---

### Task 28.1: Enhanced Audit Logging

Expand audit coverage comprehensively:
- All authentication events (login, logout, password change, token refresh)
- Paper lifecycle events (import, score, stage change, delete)
- Transfer stage changes and messages
- Settings modifications (org settings, model config, repository sources)
- Data exports (who exported what, when)
- API key usage (create, revoke, authenticate via API key)

**New endpoints:**
```
GET    /api/v1/compliance/audit-logs            - Search/filter audit logs (admin)
GET    /api/v1/compliance/audit-logs/export      - Export audit logs as CSV
GET    /api/v1/compliance/audit-logs/summary     - Aggregated audit statistics
```

---

### Task 28.2: Data Retention Policies

**Models:**
```python
class RetentionPolicy(Base):
    __tablename__ = "retention_policies"

    id: Mapped[UUID]
    organization_id: Mapped[UUID]
    entity_type: Mapped[str]       # papers, audit_logs, conversations, submissions
    retention_days: Mapped[int]
    action: Mapped[str]            # archive, anonymize, delete
    is_active: Mapped[bool]
    last_applied_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
```

**Endpoints:**
```
GET    /api/v1/compliance/retention             - List policies
POST   /api/v1/compliance/retention             - Create policy (admin)
PATCH  /api/v1/compliance/retention/{id}        - Update policy
DELETE /api/v1/compliance/retention/{id}        - Remove policy
POST   /api/v1/compliance/retention/apply       - Apply now (admin, dry-run option)
```

**Background job:** `jobs/retention.py` - arq cron job that applies retention policies nightly.

---

### Task 28.3: Compliance Dashboard Frontend

**File: frontend/src/pages/CompliancePage.tsx**
- **Audit Logs tab**: Searchable/filterable log viewer with pagination
- **Data Retention tab**: Configure retention policies per entity type
- **Data Processing tab**: Show where data is processed (hosting info from model settings), GDPR transparency
- **Export tab**: Export audit logs, generate compliance reports

**Sidebar navigation:** Add "Compliance" under admin section

**Migration:** `alembic revision --autogenerate -m "add_retention_policies"`

---

### Task 28.4: SOC2 Type II Preparation

**Compliance checklist implementation:**

**File: paper_scraper/modules/compliance/soc2.py**
```python
SOC2_CONTROLS = {
    "CC1": {
        "name": "Control Environment",
        "controls": [
            {"id": "CC1.1", "desc": "Organizational structure documented", "status": "implemented"},
            {"id": "CC1.2", "desc": "Code of conduct established", "status": "pending"},
        ]
    },
    "CC6": {
        "name": "Logical and Physical Access",
        "controls": [
            {"id": "CC6.1", "desc": "Unique user identification", "status": "implemented"},
            {"id": "CC6.2", "desc": "Access authorization documented", "status": "implemented"},
            {"id": "CC6.3", "desc": "Access removal on termination", "status": "implemented"},
        ]
    },
    # ... more control categories
}
```

**Frontend: Compliance Dashboard SOC2 tab**
- Visual checklist of SOC2 control categories
- Implementation status (Implemented, In Progress, Pending)
- Evidence links for each control
- Export as PDF for auditor review

**Backend endpoint:**
```
GET /api/v1/compliance/soc2/status     - SOC2 control status
GET /api/v1/compliance/soc2/evidence   - Control evidence links
POST /api/v1/compliance/soc2/export    - Generate auditor report
```

---

## Sprint 29: Internationalization & Platform Features

### Goal
Add multi-language support, organization branding, and additional data source integrations.

### User Stories
- **U3**: Language selection
- **O2**: Organization branding
- **P5**: Related patents display (EPO OPS)

### Duration
2 weeks

---

### Task 29.1: i18n Framework Setup

**Install:**
```bash
cd frontend && npm install react-i18next i18next i18next-browser-languagedetector
```

**Directory: frontend/src/locales/**
```
locales/
├── en/translation.json
├── de/translation.json
└── i18n.ts
```

**Implementation:**
1. Configure i18next with language detection
2. Extract all user-facing strings to translation files (EN + DE to start)
3. Add `useTranslation()` hook to components
4. Language selector in UserSettingsPage

**Priority pages for translation:** Navigation, Dashboard, Login/Register, Common UI

---

### Task 29.2: Organization Branding

**Update `organizations` table:**
- Add `branding` JSONB column: `{ logo_url, primary_color, accent_color, favicon_url }`

**Endpoints:**
```
PATCH  /api/v1/auth/organization/branding   - Update branding (admin)
POST   /api/v1/auth/organization/logo       - Upload logo to MinIO
```

**Frontend:** Apply org colors to theme CSS variables dynamically, show org logo in navbar.

---

### Task 29.3: EPO OPS Client for Patent Data

**File: paper_scraper/modules/papers/clients/epo_ops.py**
- Patent search and retrieval from EPO Open Patent Services
- Add "Related Patents" section to PaperDetailPage
- Show patent title, number, abstract, applicant, link to Espacenet

---

### Task 29.4: Semantic Scholar Client

**File: paper_scraper/modules/papers/clients/semantic_scholar.py**
- Paper search, metadata, citation graph
- Add as ingestion source (`POST /api/v1/papers/ingest/semantic-scholar`)
- Add citation graph data to PaperDetailPage

---

## Sprint 30: Technical Debt & Quality ✅

### Goal
Resolve accumulated technical debt, improve test coverage, and ensure production readiness.

### Resolves
- **TD-001**: Standardize transaction management
- **TD-002**: Add `created_by_id` to Paper model
- **TD-003**: Implement `avg_time_per_stage` calculation
- **TD-005**: Migrate tests to PostgreSQL (testcontainers)
- **TD-007**: Fix Redis-dependent test failures
- **TD-011**: Badge stats query optimization
- **TD-012**: Organization-level custom badges
- **TD-013**: Search activity tracking
- **TD-014**: Pagination for badge/knowledge endpoints

### Duration
2 weeks

---

### Task 30.1: Transaction Management Standardization (TD-001) [x]

Audit all service modules and standardize:
- [x] **FastAPI context**: Use `flush()` (auto-committed by `get_db()`)
- [x] **Background jobs**: Use explicit `commit()` with `get_async_session()`
- [x] Document pattern in CLAUDE.md

---

### Task 30.2: Paper Created-By Tracking (TD-002) [x]

**Migration:** Add `created_by_id` column to `papers` table (FK to `users.id`, nullable for legacy).
- [x] Set automatically during paper import
- [x] Update `analytics/service.py` to use actual `created_by_id`

---

### Task 30.3: Pipeline Stage Time Calculation (TD-003) [x]

**Update `projects/service.py`:**
- [x] Calculate `avg_time_per_stage` from `paper_project_status` stage change timestamps
- [x] Track stage entry/exit times in stage history

---

### Task 30.4: PostgreSQL Test Infrastructure (TD-005) [x]

**Migrate from SQLite to PostgreSQL for tests:**
```bash
pip install testcontainers[postgres]
```

- [x] Added testcontainers-postgres to dev dependencies
- [x] Created PostgreSQL test conftest with pgvector support
- [x] SQLite fallback maintained for CI without Docker

---

### Task 30.5: Fix Redis Test Issues (TD-007) [x]

- [x] Added fakeredis for mocking Redis in tests
- [x] Token blacklist tests use fakeredis instead of live Redis

---

### Task 30.6: Remaining Technical Debt [x]

- [x] **TD-011**: Optimize badge stats - single SELECT with 8 scalar subqueries (was 7 sequential COUNTs)
- [x] **TD-012**: Organization-scoped custom badges with composite unique constraint (name+org_id)
- [x] **TD-013**: SearchActivity model + tracking in search service + GDPR retention handler
- [x] **TD-014**: Pagination for knowledge list endpoints (page/page_size Query params)

**Review-driven fixes applied:**
- [x] Badge.name: global unique → composite unique(name, organization_id)
- [x] UserBadge: added unique(user_id, badge_id) constraint
- [x] check_and_award_badges(): tenant-isolated badge query (system + org-specific only)
- [x] papers_imported stat: scoped to user via created_by_id (not org-wide)
- [x] SearchActivity: removed redundant single-column indexes (composite indexes sufficient)
- [x] Removed no-op .correlate() calls from scalar subqueries
- [x] Added SEARCH_ACTIVITIES to RetentionEntityType + _apply_to_search_activities handler

---

### Task 30.7: Test Coverage Push [x]

- [x] Badge service tests (stats, award, list, seed)
- [x] SearchActivity model and tracking tests
- [x] Knowledge pagination tests

---

### Task 30.8: Performance & Documentation [x]

- [x] Badge stats query: 7 round-trips → 1 (scalar subquery optimization)
- [x] SearchActivity indexes: composite-only strategy for efficient range queries
- [x] Implementation plan updated with completion status

---

## Cross-Sprint Technical Debt Reference

All items below have been assigned to specific sprints. This table serves as a quick-reference index.

### Backend Technical Debt

| ID | Area | Priority | Assigned Sprint | Description |
|----|------|----------|-----------------|-------------|
| **TD-001** | Transaction management | LOW | Sprint 30 | Standardize `flush()` vs `commit()` patterns |
| **TD-002** | Analytics `created_by_id` | MEDIUM | Sprint 30 | Add `created_by_id` column to Papers table |
| **TD-003** | Pipeline stage stats | LOW | Sprint 30 | Implement `avg_time_per_stage` calculation |
| **TD-004** | Submission file storage | HIGH | **Sprint 20** | Persist uploads to MinIO/S3 |
| **TD-005** | Test infrastructure | MEDIUM | Sprint 30 | Migrate tests to PostgreSQL (testcontainers) |
| **TD-006** | Transfer migration | HIGH | **Sprint 20** | Create Alembic migration for transfer module |
| **TD-007** | Token blacklist in tests | LOW | Sprint 30 | Fix Redis-dependent test failures |
| **TD-008** | Transfer resource storage | MEDIUM | **Sprint 20** | Implement file storage for transfer resources |
| **TD-009** | Badge auto-award engine | MEDIUM | Sprint 24 | Event-driven badge awarding via arq |
| **TD-010** | Knowledge AI integration | MEDIUM | Sprint 24 | Inject knowledge sources into scoring prompts |
| **TD-011** | Badge stats optimization | LOW | Sprint 30 | Replace 7 sequential COUNT queries with CTE |
| **TD-012** | Custom org badges | LOW | Sprint 30 | Organization-level custom badge definitions |
| **TD-013** | Search activity tracking | LOW | Sprint 30 | Track searches for badge criteria |
| **TD-014** | Pagination gaps | LOW | Sprint 30 | Add pagination to badge/knowledge endpoints |

### AI/Scoring Enhancements

| ID | Area | Priority | Assigned Sprint | Description |
|----|------|----------|-----------------|-------------|
| **AI-001** | Group member suggestions | HIGH | Sprint 24 | Embedding-based similarity for `suggest_members()` |
| **AI-002** | Submission similar papers | MEDIUM | Sprint 24 | pgvector similar papers for submission analysis |
| **AI-003** | Team Readiness dimension | MEDIUM | Sprint 23 | 6th scoring dimension using author metrics |
| **AI-004** | Transfer next-steps AI | MEDIUM | Sprint 24 | Enhanced conversation-aware AI suggestions |
| **AI-005** | Knowledge-enhanced scoring | LOW | Sprint 24 | Knowledge sources in scoring prompts |

### Security Enhancements

| ID | Area | Priority | Assigned Sprint | Description |
|----|------|----------|-----------------|-------------|
| **SEC-F1** | Granular RBAC | HIGH | Sprint 22 | Per-module role-based permission checks |
| **SEC-F2** | CSV injection protection | MEDIUM | Sprint 22 | Sanitize CSV exports |
| **SEC-F3** | Audit logging coverage | MEDIUM | Sprint 22 | Audit events for all Phase 4 modules |

---

## Feature Complete Checklist

After Sprint 30, verify:

### Core Features (Phases 1-3)
- [x] Paper ingestion (DOI, OpenAlex, PubMed, arXiv, PDF)
- [x] 6-dimension AI scoring (includes Team Readiness)
- [x] KanBan project management with drag-and-drop
- [x] Full-text + semantic search
- [x] Author intelligence + CRM
- [x] Alert system + saved searches

### Lovable Parity - Backend (Phase 4)
- [x] Researcher groups (backend)
- [x] Technology transfer conversations (backend)
- [x] Research submission portal (backend)
- [x] Badge/gamification system (backend)
- [x] Knowledge management (backend)

### Stabilization & Frontend (Phase 5)
- [x] Transfer module Alembic migration (TD-006)
- [x] File storage for submissions/transfer (TD-004, TD-008)
- [x] Frontend pages: Groups, Transfer, Submissions, Badges, Knowledge
- [x] TanStack Query hooks for all new modules

### Security & AI (Phase 6)
- [x] Granular RBAC permissions system (core/permissions.py)
- [x] Audit logging for all modules
- [x] CSV injection protection (core/csv_utils.py)
- [x] 6-dimension scoring (Team Readiness)
- [x] Innovation Radar chart component
- [x] Model configuration + usage tracking
- [x] Model Settings UI
- [x] Badge auto-award engine (jobs/badges.py)
- [ ] Embedding-based group suggestions (AI-001) - prompt exists, needs pgvector integration
- [ ] Knowledge-enhanced scoring (AI-005/TD-010) - needs scoring orchestrator integration

### Platform & DX (Phase 7)
- [ ] API key management
- [ ] Webhook integrations
- [ ] Repository source management
- [ ] Developer Settings page
- [ ] Command palette (Cmd+K)
- [ ] Global keyboard shortcuts
- [ ] Notification center / alert inbox
- [ ] Search result preview panel
- [ ] Celebration animations
- [ ] Innovation funnel analytics
- [ ] Benchmark comparisons
- [ ] Scheduled reports
- [ ] Peer comparison charts

### Enterprise Readiness (Phase 8)
- [ ] Enhanced compliance dashboard
- [ ] Data retention policies
- [ ] Internationalization (EN, DE)
- [ ] Organization branding
- [ ] EPO OPS patent integration
- [ ] Semantic Scholar integration
- [x] Transaction management standardized
- [ ] Test infrastructure on PostgreSQL
- [ ] Test coverage >80%
- [ ] Performance targets met
