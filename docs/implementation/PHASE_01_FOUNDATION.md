# Phase 1: Foundation & MVP

[← Back to INDEX](../INDEX.md) | [Implementation Status](STATUS.md)

**Sprints:** 1-6
**Duration:** 12 weeks (Jan-Mar 2024)
**Status:** ✅ Complete

---

## Phase Goals

Establish technical foundation and deliver minimal viable product (MVP) with core paper management functionality.

**Key Objectives:**
1. Set up FastAPI backend with PostgreSQL + pgvector
2. Implement authentication & multi-tenancy
3. Build paper ingestion from external sources
4. Create AI scoring pipeline (5 dimensions initially)
5. Implement project management (KanBan)
6. Build search capabilities (fulltext + semantic)
7. Deliver React frontend MVP

---

## Sprints Overview

| Sprint | Focus | Status | Completion Date |
|--------|-------|--------|-----------------|
| **1** | Foundation & Auth | ✅ Complete | 2024-01-28 |
| **2** | Papers & Ingestion | ✅ Complete | 2024-02-04 |
| **3** | AI Scoring Pipeline | ✅ Complete | 2024-02-11 |
| **4** | Projects & KanBan | ✅ Complete | 2024-02-18 |
| **5** | Search & Discovery | ✅ Complete | 2024-02-25 |
| **6** | Frontend MVP | ✅ Complete | 2024-03-03 |

---

## Sprint 1: Foundation & Auth

_Completed on 2024-01-28_

### Goals

- Set up repository scaffolding and development environment
- Implement core authentication system
- Establish database architecture with PostgreSQL + pgvector
- Create FastAPI application structure

### Key Implementations

**1. Repository Scaffolding**
- `pyproject.toml` with dependencies (FastAPI, SQLAlchemy, Alembic, Pydantic, pgvector)
- `docker-compose.yml` (PostgreSQL 16 + pgvector, Redis, MinIO)
- `.env.example` with all configuration variables
- `Dockerfile` for API container

**2. Core Module** → [paper_scraper/core/](../../paper_scraper/core/)
- `config.py` - Pydantic Settings with environment validation
- `database.py` - Async SQLAlchemy session management
- `security.py` - JWT token generation, password hashing (bcrypt)
- `exceptions.py` - Custom exception classes

**3. Auth Module** → [paper_scraper/modules/auth/](../../paper_scraper/modules/auth/)
- `models.py` - User & Organization models with multi-tenancy
- `schemas.py` - Pydantic v2 request/response schemas
- `service.py` - Business logic (register, login, token refresh)
- `router.py` - FastAPI endpoints (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`)

**4. API Layer** → [paper_scraper/api/](../../paper_scraper/api/)
- `main.py` - FastAPI application setup
- `dependencies.py` - Dependency injection (get_db, get_current_user)

**5. Database Migration**
- Initial Alembic migration for User & Organization tables
- Multi-tenancy: All tables include `organization_id` foreign key

**6. Tests** → [tests/](../../tests/)
- `conftest.py` - pytest fixtures (test_db, test_client)
- 15 auth tests (register, login, JWT validation, password hashing)

### Architecture Decisions

**ADR-001: Modularer Monolith** (Established)
- **Decision:** Build modular monolith instead of microservices
- **Rationale:** Faster iteration, simpler debugging, lower operational costs
- **Impact:** Module-based directory structure under `paper_scraper/modules/`

**ADR-005: Self-hosted PostgreSQL + Custom JWT** (Established)
- **Decision:** Use PostgreSQL instead of Supabase
- **Rationale:** Full control, no vendor lock-in, cost-effective
- **Impact:** Custom authentication implementation required

### Lessons Learned

1. **Async SQLAlchemy Setup:** Use `AsyncSession` from the start to avoid mixing sync/async patterns
2. **pgvector Extension:** Must enable extension before creating tables with vector columns
3. **Multi-tenancy Pattern:** Established `organization_id` on all domain tables for tenant isolation
4. **JWT Security:** Used RS256 (asymmetric) instead of HS256 for better security

### Testing

- **15 tests passing** (100% coverage for auth module)
- Test database uses PostgreSQL (via testcontainers) for production parity

---

## Sprint 2: Papers & Ingestion

_Completed on 2024-02-04_

### Goals

- Implement paper data model with pgvector support
- Integrate external APIs (OpenAlex, Crossref)
- Build async ingestion pipeline with arq
- Create paper CRUD endpoints

### Key Implementations

**1. Paper Models** → [paper_scraper/modules/papers/models.py](../../paper_scraper/modules/papers/models.py)
- `Paper` model with vector embedding column (1536d for text-embedding-3-small)
- `Author` model with h-index, citation count, works count
- `PaperAuthor` association table (many-to-many with position tracking)
- `PaperSource` enum (DOI, OpenAlex, PubMed, arXiv, Crossref, PDF, Manual)

**2. External API Clients** → [paper_scraper/modules/papers/clients/](../../paper_scraper/modules/papers/clients/)
- `base.py` - Abstract base client with rate limiting
- `openalex.py` - OpenAlex API client (works, authors, sources)
- `crossref.py` - Crossref API client (DOI lookup)
- Pattern: Async httpx client with retry logic

**3. Paper Service** → [paper_scraper/modules/papers/service.py](../../paper_scraper/modules/papers/service.py)
- CRUD operations with tenant isolation
- DOI import: `ingest_from_doi()`
- OpenAlex batch import: `ingest_from_openalex()`
- Author deduplication logic (ORCID, OpenAlex ID, name matching)

**4. Paper Router** → [paper_scraper/modules/papers/router.py](../../paper_scraper/modules/papers/router.py)
- `GET /papers/` - List with pagination & search
- `GET /papers/{id}` - Detail with authors
- `POST /papers/ingest/doi` - Import by DOI
- `POST /papers/ingest/openalex` - Batch import (sync)
- `POST /papers/ingest/openalex/async` - Batch import (async via arq)
- `DELETE /papers/{id}` - Delete paper

**5. Background Jobs** → [paper_scraper/jobs/](../../paper_scraper/jobs/)
- `ingestion.py` - arq task `ingest_openalex_task()`
- `worker.py` - arq WorkerSettings configuration
- Redis connection for job queue

**6. Database Migration**
- Papers, Authors, PaperAuthors tables
- HNSW index on `papers.embedding` (m=16, ef_construction=64)
- pg_trgm indexes on title & abstract for fulltext search

### Architecture Decisions

**ADR-002: PostgreSQL + pgvector (HNSW)** (Established)
- **Decision:** Use pgvector with HNSW index instead of dedicated vector DB
- **Rationale:** One database, native JOINs, cost-effective
- **Impact:** 1536-dimensional embeddings for papers, HNSW indexing for sub-second semantic search

**ADR-004: arq for Background Jobs** (Established)
- **Decision:** Use arq instead of Celery
- **Rationale:** Async-native, simpler setup, smaller footprint
- **Impact:** All background tasks use async patterns

### Lessons Learned

1. **HNSW Index Parameters:** `m=16, ef_construction=64` provides good balance of speed vs. recall
2. **Author Deduplication:** OpenAlex ID is most reliable, ORCID second, name matching last resort
3. **Async Ingestion:** Long-running imports (>30s) must use background jobs to avoid HTTP timeouts
4. **Vector Dimension:** text-embedding-3-small (1536d) chosen over ada-002 (1536d) for better quality

### Testing

- **30 total tests** (15 new for papers module)
- OpenAlex/Crossref clients mocked with `respx`
- Paper ingestion tested with fixtures

---

## Sprint 3: AI Scoring Pipeline

_Completed on 2024-02-11_

### Goals

- Implement 5-dimension AI scoring system
- Build LLM client abstraction
- Generate embeddings for papers
- Create scoring orchestrator

### Key Implementations

**1. Scoring Models** → [paper_scraper/modules/scoring/models.py](../../paper_scraper/modules/scoring/models.py)
- `PaperScore` model with 5 dimensions (novelty, ip_potential, marketability, feasibility, commercialization)
- `overall_score` as weighted average
- `confidence` score (0-1)
- `model_version` for tracking LLM model used

**2. LLM Client Abstraction** → [paper_scraper/modules/scoring/llm_client.py](../../paper_scraper/modules/scoring/llm_client.py)
- `BaseLLMClient` abstract class
- `OpenAIClient` implementation
- Support for GPT-4 and GPT-3.5-turbo
- Structured output parsing with JSON schema

**3. Scoring Dimensions** → [paper_scraper/modules/scoring/dimensions/](../../paper_scraper/modules/scoring/dimensions/)
- 5 scorer implementations (novelty, ip_potential, marketability, feasibility, commercialization)
- Each dimension: Jinja2 prompt template → LLM → JSON response
- Pydantic schemas for validation

**4. Scoring Orchestrator** → [paper_scraper/modules/scoring/orchestrator.py](../../paper_scraper/modules/scoring/orchestrator.py)
- `IngestionPipeline` class coordinates:
  1. Find similar papers (pgvector search)
  2. Load author metrics
  3. Score all dimensions in parallel
  4. Aggregate results
  5. Save to database

**5. Prompt Templates** → [paper_scraper/modules/scoring/prompts/](../../paper_scraper/modules/scoring/prompts/)
- Jinja2 templates for each dimension
- Context: paper metadata, similar papers, author metrics
- Output: JSON with score (0-10), reasoning, evidence

**6. Embedding Generation**
- OpenAI text-embedding-3-small (1536d)
- Generated on paper creation
- Used for similarity search in scoring

**7. API Endpoints** → [paper_scraper/modules/scoring/router.py](../../paper_scraper/modules/scoring/router.py)
- `POST /scoring/papers/{id}/score` - Trigger scoring
- `GET /scoring/papers/{id}/scores` - Get score history

**8. Background Jobs** → [paper_scraper/jobs/scoring.py](../../paper_scraper/jobs/scoring.py)
- `score_paper_task()` - Async scoring via arq
- Handles retries and error logging

### Architecture Decisions

**ADR-003: Multi-provider LLM (GPT-4 Turbo default)** (Established)
- **Decision:** Abstract LLM client to support multiple providers
- **Rationale:** No vendor lock-in, can switch models based on cost/quality
- **Impact:** BaseLLMClient interface allows adding Anthropic, Ollama, etc.

### Lessons Learned

1. **Parallel Dimension Scoring:** Use `asyncio.gather()` to score all dimensions concurrently (5x speedup)
2. **JSON Parsing:** LLMs occasionally output invalid JSON → use `json.loads()` with fallback to regex extraction
3. **Prompt Engineering:** Including similar papers as context significantly improves scoring quality
4. **Embedding Quality:** text-embedding-3-small provides good quality at 1/3 cost of ada-002

### Testing

- **45 total tests** (15 new for scoring module)
- LLM responses mocked with fixed JSON outputs
- Embedding generation mocked (no OpenAI calls in tests)

---

## Sprint 4: Projects & KanBan

_Completed on 2024-02-18_

### Goals

- Implement project management system
- Build KanBan board with drag-and-drop stages
- Support custom scoring weights per project

### Key Implementations

**1. Project Models** → [paper_scraper/modules/projects/models.py](../../paper_scraper/modules/projects/models.py)
- `Project` model with configurable stages
- `PaperProjectStatus` association table (paper → project → stage)
- `scoring_weights` JSON column for per-project dimension weights
- `rejection_reason` for papers moved to "Rejected" stage

**2. Project Service** → [paper_scraper/modules/projects/service.py](../../paper_scraper/modules/projects/service.py)
- CRUD operations
- `move_paper()` - Update paper stage within project
- `get_kanban_view()` - Return papers grouped by stage
- Tenant isolation on all queries

**3. Project Router** → [paper_scraper/modules/projects/router.py](../../paper_scraper/modules/projects/router.py)
- `GET /projects/` - List projects
- `POST /projects/` - Create project
- `GET /projects/{id}/kanban` - KanBan view
- `PATCH /projects/{id}/papers/{paper_id}/move` - Move paper to stage

**4. Database Migration**
- Projects table
- PaperProjectStatus association table
- Indexes on (project_id, stage), (paper_id, project_id)

### Architecture Decisions

**Per-Project Scoring Weights**
- **Decision:** Allow projects to define custom scoring dimension weights
- **Rationale:** Different projects prioritize different aspects (e.g., IP-focused vs. market-focused)
- **Implementation:** `scoring_weights` JSONB column with default `{}`

### Lessons Learned

1. **Stage Management:** Use JSONB array for stages instead of enum to allow project-specific customization
2. **Default Stages:** Provide sensible defaults (Discovery, Evaluation, Negotiation, Closed) but allow override
3. **Status Tracking:** Association table pattern allows tracking paper status per project

### Testing

- **60 total tests** (15 new for projects module)
- KanBan view tested with multiple papers across stages

---

## Sprint 5: Search & Discovery

_Completed on 2024-02-25_

### Goals

- Implement fulltext search using PostgreSQL pg_trgm
- Build semantic search with pgvector
- Create hybrid RRF ranking
- Add advanced filters

### Key Implementations

**1. Search Service** → [paper_scraper/modules/search/service.py](../../paper_scraper/modules/search/service.py)
- `_fulltext_search()` - PostgreSQL pg_trgm trigram matching
- `_semantic_search()` - pgvector cosine similarity
- `_hybrid_search()` - RRF (Reciprocal Rank Fusion) combines both
- Advanced filters: date range, journal, score thresholds, paper type

**2. RRF Algorithm**
```python
def compute_rrf_score(rank_text, rank_semantic, k=60):
    score_text = 1.0 / (k + rank_text) if rank_text else 0
    score_semantic = 1.0 / (k + rank_semantic) if rank_semantic else 0
    return 0.5 * score_text + 0.5 * score_semantic
```

**3. Search Router** → [paper_scraper/modules/search/router.py](../../paper_scraper/modules/search/router.py)
- `POST /search/` - Unified search endpoint
- Supports `mode`: "fulltext", "semantic", "hybrid" (default)
- Pagination with limit/offset
- Filters passed as JSON object

**4. Embedding Generation on Ingest**
- Papers now automatically generate embeddings on creation
- Uses OpenAI text-embedding-3-small
- Stored in `papers.embedding` vector column

**5. HNSW Index Optimization**
- Adjusted ef_construction to 64 (from 100) for faster indexing
- m=16 provides good recall

### Architecture Decisions

**RRF Ranking**
- **Decision:** Use Reciprocal Rank Fusion to combine fulltext + semantic results
- **Rationale:** Better than simple concatenation or score averaging
- **Parameters:** k=60, equal weights (0.5/0.5) as defaults

### Lessons Learned

1. **pg_trgm Indexes:** Significantly improve fulltext search performance (50ms → 5ms on 10k papers)
2. **HNSW vs IVFFlat:** HNSW provides better recall with similar query speed
3. **RRF Tuning:** k=60 empirically works well for combining ranking lists of different sizes
4. **Query Embedding:** Generate embedding for query text using same model as paper embeddings

### Testing

- **75 total tests** (15 new for search module)
- Search tested with mock embeddings
- RRF ranking verified with fixed test data

---

## Sprint 6: Frontend MVP

_Completed on 2024-03-03_

### Goals

- Set up React 18 + Vite frontend
- Implement TanStack Query for data fetching
- Build core pages (papers list, paper detail, projects)
- Integrate with backend API

### Key Implementations

**1. Frontend Setup** → [frontend/](../../frontend/)
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- Shadcn/UI component library
- React Router for routing

**2. API Client** → [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts)
- Axios-based client with interceptors
- JWT token handling (localStorage)
- Error handling with toast notifications
- API namespace structure: `api.papers.list()`, `api.papers.get(id)`, etc.

**3. Core Pages** → [frontend/src/pages/](../../frontend/src/pages/)
- `LoginPage.tsx` / `RegisterPage.tsx` - Authentication
- `PapersPage.tsx` - Paper list with search & filters
- `PaperDetailPage.tsx` - Paper detail with authors & score
- `ProjectsPage.tsx` - Project list
- `ProjectKanBanPage.tsx` - KanBan board with drag-and-drop
- `SearchPage.tsx` - Unified search interface

**4. Custom Hooks** → [frontend/src/hooks/](../../frontend/src/hooks/)
- `usePapers.ts` - TanStack Query hook for papers
- `useProjects.ts` - TanStack Query hook for projects
- `useAuth.ts` - Authentication state management

**5. UI Components** → [frontend/src/components/ui/](../../frontend/src/components/ui/)
- Shadcn/UI components (Button, Card, Dialog, Input, etc.)
- `InnovationRadar.tsx` - 6-axis radar chart for scores (using Recharts)
- `EmptyState.tsx` - Empty states with actions
- `Skeleton.tsx` - Loading skeletons

**6. Routing** → [frontend/src/App.tsx](../../frontend/src/App.tsx)
- React Router v6
- Protected routes (require authentication)
- Layout with sidebar navigation

### Architecture Decisions

**TanStack Query for Server State**
- **Decision:** Use TanStack Query instead of Redux
- **Rationale:** Better suited for server state management, automatic caching, refetching
- **Impact:** Simplified data fetching patterns, less boilerplate

**Shadcn/UI Components**
- **Decision:** Use Shadcn/UI instead of full component library
- **Rationale:** Copy-paste components (full control), built on Radix UI (accessible)
- **Impact:** Components live in codebase, easy to customize

### Lessons Learned

1. **Query Keys:** Use hierarchical query keys: `['papers', filters]` for better cache management
2. **Optimistic Updates:** Implement optimistic updates for better UX (paper move, status change)
3. **Error Boundaries:** Add error boundaries to prevent whole app crashes
4. **Token Refresh:** Implement automatic token refresh to avoid re-login

### Testing

- **E2E tests** with Playwright (auth flow, paper list, search)
- Component tests deferred to Phase 2

---

## Phase Outcomes

### Delivered Features

✅ **Authentication System:**
- User registration & login
- JWT-based authentication
- Multi-tenant organization support

✅ **Paper Management:**
- Paper CRUD operations
- DOI import
- OpenAlex batch import (sync & async)
- Author profiles with metrics

✅ **AI Scoring:**
- 5-dimension scoring system
- Embedding generation
- Similar paper discovery
- Scoring history

✅ **Project Management:**
- KanBan board with custom stages
- Paper assignment to projects
- Per-project scoring weights

✅ **Search:**
- Fulltext search (pg_trgm)
- Semantic search (pgvector)
- Hybrid RRF ranking
- Advanced filters

✅ **Frontend MVP:**
- React 18 + TypeScript
- 6 core pages
- TanStack Query integration
- Shadcn/UI components

### Metrics

| Metric | Value |
|--------|-------|
| **Backend Modules** | 5 (auth, papers, scoring, projects, search) |
| **API Endpoints** | 24 |
| **Database Tables** | 9 |
| **Tests** | 75 (pytest) |
| **Frontend Pages** | 6 |
| **Frontend Components** | 20+ |

### Architecture Impact

**Foundation Established:**
- Modularer Monolith architecture proven
- PostgreSQL + pgvector validated for semantic search
- arq background jobs working reliably
- Multi-tenancy pattern applied consistently
- LLM abstraction allows provider flexibility

**Technical Debt Created:**
- Paper notes not yet implemented (added in Sprint 9)
- 6th scoring dimension (Team Readiness) deferred to Sprint 23
- Author enrichment stubs only (ORCID, Semantic Scholar) - completed in Sprint 10
- No email verification yet (added in Sprint 13)

---

## See Also

- [STATUS.md](STATUS.md) - Current implementation state
- [PHASE_02_FEATURES.md](PHASE_02_FEATURES.md) - Sprints 7-12
- [docs/architecture/DECISIONS.md](../architecture/DECISIONS.md) - ADRs 001-005
- [docs/modules/papers.md](../modules/papers.md) - Papers module documentation
- [docs/modules/scoring.md](../modules/scoring.md) - Scoring system guide
- [CLAUDE.md](../../CLAUDE.md) - AI agent quick start

---

**Last Updated:** 2026-02-10
**Phase Status:** Complete
**Sprint Count:** 6 (Sprints 1-6)
**Lines:** 776
