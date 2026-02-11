# Paper Scraper - Claude Code Project Context

> **📖 Documentation Navigation:** This is a lean AI agent entry point.
> **For detailed information**, see **[docs/INDEX.md](docs/INDEX.md)** - Master navigation hub

---

## Projekt-Überblick

**Paper Scraper** ist eine AI-powered SaaS-Plattform zur automatisierten Analyse wissenschaftlicher Publikationen.

**Zielgruppen:** Technology Transfer Offices (TTOs), VCs, Corporate Innovation Teams

**Kernwertversprechen:**
- **Papers automatisch importieren** aus OpenAlex, PubMed, arXiv, via DOI oder PDF
- **6-dimensionales AI-Scoring**: Novelty, IP-Potential, Marketability, Feasibility, Commercialization, Team Readiness
- **KanBan-Pipeline** für strukturiertes Paper-Management
- **Semantische Suche** (pgvector HNSW) + Fulltext Search
- **Technology Transfer Workflows** für Researcher-Outreach
- **Gamification & Badges** für Team-Engagement

**Current Status (2026-02-10):**
- **37 Sprints completed** across 10 development phases
- **24 backend modules**, 208+ API endpoints, 841 pytest tests
- **28 frontend pages**, E2E tested with Playwright
- **Full i18n** (EN/DE), server-side notifications, GDPR-compliant

**See:** [docs/implementation/STATUS.md](docs/implementation/STATUS.md) for current state

---

## Tech Stack Summary

| Layer | Technologie |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy (async), Pydantic v2 |
| **Database** | PostgreSQL 16 + pgvector (HNSW index) |
| **Queue** | arq (async-native) + Redis |
| **Storage** | MinIO (S3-compatible) |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, Shadcn/UI |
| **AI/LLM** | Multi-provider (GPT-5 mini default), text-embedding-3-small |
| **Data Sources** | OpenAlex, PubMed, arXiv, Crossref, DOI, PDF |
| **Monitoring** | Langfuse (LLM observability), Sentry (errors) |

**See:** [docs/architecture/TECH_STACK.md](docs/architecture/TECH_STACK.md) for complete details

---

## Projektstruktur (2 Levels)

```
paper_scraper/
├── paper_scraper/              # Python Backend
│   ├── core/                   # Config, Database, Security, Permissions
│   ├── modules/                # 24 Feature Modules (auth, papers, scoring, etc.)
│   ├── jobs/                   # arq Background Tasks (6 workers)
│   └── api/                    # FastAPI App + Routes
├── frontend/                   # React Frontend
│   └── src/                    # Components, Pages, Hooks, API Client
├── tests/                      # 841 pytest tests
├── e2e/                        # Playwright E2E tests
├── alembic/                    # Database migrations
├── docs/                       # 📚 Complete documentation
│   ├── INDEX.md                # Master navigation
│   ├── architecture/           # System design, ADRs, tech stack
│   ├── api/                    # API reference (208+ endpoints)
│   ├── modules/                # 24 module docs
│   ├── features/               # Feature guides (scoring, ingestion, search)
│   ├── development/            # Coding standards, testing, troubleshooting
│   └── implementation/         # Sprint history (10 phases, 37 sprints)
├── .github/workflows/          # CI/CD (tests, deploy, E2E)
└── docker-compose.yml          # PostgreSQL, Redis, MinIO
```

**See:** [docs/modules/MODULES_OVERVIEW.md](docs/modules/MODULES_OVERVIEW.md) for all 24 modules

---

## Essential Coding Patterns

### Python Backend

```python
# ✅ RICHTIG: Async, typed, tenant-isolated
async def get_paper(
    db: AsyncSession,
    paper_id: UUID,
    org_id: UUID,
) -> Paper | None:
    """Retrieve paper with tenant isolation."""
    query = select(Paper).where(
        Paper.id == paper_id,
        Paper.organization_id == org_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

**Regeln:**
- Async/await für alle I/O (kein blocking code!)
- Type hints überall
- Tenant isolation: `organization_id` filter in allen Queries
- Google-Style Docstrings
- Pydantic v2 für alle DTOs

**See:** [docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)

### TypeScript Frontend

```typescript
// ✅ RICHTIG: TanStack Query pattern
const usePapers = (filters: PaperFilters) => {
  return useQuery({
    queryKey: ['papers', filters],
    queryFn: () => api.papers.list(filters),
  });
};
```

**Regeln:**
- TanStack Query für Server State
- Shadcn/UI Components
- Zod für Runtime Validation

**See:** [docs/modules/frontend.md](docs/modules/frontend.md)

---

## Quick Navigation

### For Architecture Questions
- **System Overview:** [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md)
- **Tech Stack:** [docs/architecture/TECH_STACK.md](docs/architecture/TECH_STACK.md)
- **Database Schema:** [docs/architecture/DATA_MODEL.md](docs/architecture/DATA_MODEL.md)
- **ADRs (23 total):** [docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md)

### For API Development
- **Complete API Reference (208+ endpoints):** [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)
- **API Patterns:** [docs/api/API_PATTERNS.md](docs/api/API_PATTERNS.md)

### For Module Development
- **All 24 Modules:** [docs/modules/MODULES_OVERVIEW.md](docs/modules/MODULES_OVERVIEW.md)
- Specific modules: `docs/modules/{module_name}.md` (auth, papers, scoring, etc.)

### For Feature Implementation
- **AI Scoring System:** [docs/features/SCORING_GUIDE.md](docs/features/SCORING_GUIDE.md)
- **Paper Ingestion:** [docs/features/INGESTION_GUIDE.md](docs/features/INGESTION_GUIDE.md)
- **Search (Fulltext + Semantic):** [docs/features/SEARCH_GUIDE.md](docs/features/SEARCH_GUIDE.md)
- **KanBan Pipeline:** [docs/features/PIPELINE_GUIDE.md](docs/features/PIPELINE_GUIDE.md)

### For Implementation History
- **Current Status & Metrics:** [docs/implementation/STATUS.md](docs/implementation/STATUS.md)
- **Sprint-by-Sprint History:**
  - [PHASE_01_FOUNDATION.md](docs/implementation/PHASE_01_FOUNDATION.md) - Sprints 1-6
  - [PHASE_02_FEATURES.md](docs/implementation/PHASE_02_FEATURES.md) - Sprints 7-12
  - [PHASE_03_BETA.md](docs/implementation/PHASE_03_BETA.md) - Sprints 13-15
  - [PHASE_04_LOVABLE.md](docs/implementation/PHASE_04_LOVABLE.md) - Sprints 16-19
  - [PHASE_05_STABILIZATION.md](docs/implementation/PHASE_05_STABILIZATION.md) - Sprints 20-21
  - [PHASE_06_SECURITY.md](docs/implementation/PHASE_06_SECURITY.md) - Sprints 22-24
  - [PHASE_07_PLATFORM.md](docs/implementation/PHASE_07_PLATFORM.md) - Sprints 25-27
  - [PHASE_08_ENTERPRISE.md](docs/implementation/PHASE_08_ENTERPRISE.md) - Sprints 28-30
  - [PHASE_09_QUALITY.md](docs/implementation/PHASE_09_QUALITY.md) - Sprints 31-36
  - [PHASE_10_FOUNDATIONS.md](docs/implementation/PHASE_10_FOUNDATIONS.md) - Sprint 37

### For Development
- **Testing Guide:** [docs/development/TESTING_GUIDE.md](docs/development/TESTING_GUIDE.md)
- **Common Tasks:** [docs/development/COMMON_TASKS.md](docs/development/COMMON_TASKS.md)
- **Troubleshooting:** [docs/development/TROUBLESHOOTING.md](docs/development/TROUBLESHOOTING.md)

---

## Core Data Models (Simplified)

**For complete schema:** [docs/architecture/DATA_MODEL.md](docs/architecture/DATA_MODEL.md)

**Essential tables:**
```sql
-- Multi-tenancy
organizations (id, name, type, subscription_tier, logo_url, settings)
users (id, organization_id, email, role, email_verified)

-- Papers
papers (id, organization_id, doi, title, abstract, source,
        embedding vector(1536), created_at)
authors (id, orcid, name, h_index, citation_count, works_count)
paper_authors (paper_id, author_id, position, is_corresponding)

-- AI Scoring
paper_scores (paper_id, organization_id,
              novelty, ip_potential, marketability, feasibility,
              commercialization, team_readiness, overall_score,
              confidence, model_version)

-- KanBan Pipeline
projects (id, organization_id, name, stages, scoring_weights)
paper_project_status (paper_id, project_id, stage, assigned_to)

-- Search & Alerts
saved_searches (id, query, mode, filters, is_public, share_token)
alerts (id, saved_search_id, frequency, channel, is_active)

-- Technology Transfer
conversations (id, paper_id, researcher_id, stage, transfer_type)
messages (id, conversation_id, content, sender, mentions)

-- Compliance
audit_logs (id, user_id, action, resource_type, ip_address)
retention_policies (id, resource_type, retention_days)

-- Notifications
notifications (id, user_id, type, title, message, is_read)
```

**Total:** 40+ tables with PostgreSQL 16 + pgvector

---

## Scoring System (6 Dimensions)

| Dimension | Score | Bewertet |
|-----------|-------|----------|
| **Novelty** | 0-10 | Technologische Neuheit vs. State-of-Art |
| **IP-Potential** | 0-10 | Patentierbarkeit, Prior Art, White Spaces |
| **Marketability** | 0-10 | Marktgröße, Industrien, Trends |
| **Feasibility** | 0-10 | TRL-Level, Time-to-Market, Development Cost |
| **Commercialization** | 0-10 | Empfohlener Pfad, Entry Barriers |
| **Team Readiness** | 0-10 | Author Track Record, Industry Experience |

**Pipeline:** Paper → Embedding → Similar Papers (pgvector) → Author Metrics → LLM Scoring (6 dimensions) → Innovation Radar

**See:** [docs/features/SCORING_GUIDE.md](docs/features/SCORING_GUIDE.md)

---

## Common Development Tasks

### Add New API Endpoint
```bash
1. Schema:   modules/<module>/schemas.py (Pydantic v2)
2. Service:  modules/<module>/service.py (async, type-hinted)
3. Router:   modules/<module>/router.py (with @require_permission)
4. Tests:    tests/modules/<module>/test_<resource>.py
5. Docs:     Update docs/api/API_REFERENCE.md
```

### Add Scoring Dimension
```bash
1. Prompt:   scoring/prompts/<dimension>.jinja2
2. Scorer:   scoring/dimensions/<dimension>.py
3. Register: scoring/orchestrator.py
4. Schema:   scoring/schemas.py (add field)
5. Migration: alembic revision (add column to paper_scores)
6. Frontend: Update InnovationRadar.tsx
```

### Add Background Job
```bash
1. Create:   jobs/<task_name>.py (async function)
2. Register: jobs/worker.py (WorkerSettings.functions)
3. Schedule: arq.cron() if periodic
4. Test:     tests/jobs/test_<task_name>.py
```

**See:** [docs/development/COMMON_TASKS.md](docs/development/COMMON_TASKS.md)

---

## Development Environment

```bash
# Start all services
docker-compose up -d

# Run migrations
alembic upgrade head

# Backend tests (841 tests, 87% coverage)
pytest tests/ -v --cov=paper_scraper

# Frontend tests
cd frontend && npm test          # Unit tests (85 tests)
cd e2e && npm test              # E2E tests (45 tests)

# URLs
API:      http://localhost:8000
Docs:     http://localhost:8000/docs (OpenAPI)
Frontend: http://localhost:3000
MinIO:    http://localhost:9001
```

**See:** [SETUP.md](SETUP.md) for complete setup instructions

---

## Quick Reference Snippets

```python
# Tenant-isolated query
papers = await db.execute(
    select(Paper).where(Paper.organization_id == org_id)
)

# LLM call with Langfuse tracing
from paper_scraper.modules.scoring.llm_client import get_llm_client
llm = await get_llm_client(org_id)
result = await llm.complete(
    prompt=prompt,
    system="Du bist ein Experte...",
    temperature=0.3
)

# Semantic search (pgvector)
similar = await db.execute(
    select(Paper)
    .where(Paper.organization_id == org_id)
    .order_by(Paper.embedding.cosine_distance(query_embedding))
    .limit(5)
)

# Background job enqueue
from paper_scraper.core.redis import get_redis_pool
redis = await get_redis_pool()
await redis.enqueue_job("score_paper_task", paper_id, org_id)
```

---

## Key Architecture Decisions (ADRs)

**See:** [docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md) for all 23 ADRs

**Highlights:**
- **ADR-001:** Modularer Monolith (not microservices)
- **ADR-002:** PostgreSQL + pgvector (not dedicated vector DB)
- **ADR-003:** Multi-provider LLM (GPT-5 mini default)
- **ADR-004:** arq for background jobs (not Celery)
- **ADR-005:** Self-hosted PostgreSQL + Custom JWT (not Supabase)
- **ADR-021:** Granular RBAC (40+ permissions)
- **ADR-022:** Foundations Ingestion Pipeline (multi-source async)
- **ADR-023:** CI Documentation Gate (enforces doc updates)

---

## Getting Help

**For documentation:**
- Start here: [docs/INDEX.md](docs/INDEX.md)
- Implementation status: [docs/implementation/STATUS.md](docs/implementation/STATUS.md)
- Troubleshooting: [docs/development/TROUBLESHOOTING.md](docs/development/TROUBLESHOOTING.md)

**For deployment:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [SETUP.md](SETUP.md) - Local development setup

**For legacy docs (deprecated but available):**
- [01_TECHNISCHE_ARCHITEKTUR.md](01_TECHNISCHE_ARCHITEKTUR.md) → Use [docs/architecture/](docs/architecture/)
- [02_USER_STORIES.md](02_USER_STORIES.md) → User story catalog (maintained)
- [03_CLAUDE_CODE_GUIDE.md](03_CLAUDE_CODE_GUIDE.md) → Use [docs/development/](docs/development/)
- [05_IMPLEMENTATION_PLAN.md](05_IMPLEMENTATION_PLAN.md) → Use [docs/implementation/](docs/implementation/)

---

**Last Updated:** 2026-02-10
**Document Status:** Refactored to lean AI agent entry point with navigation to detailed docs
**Lines:** 349 (reduced from 588 = 41% reduction)
