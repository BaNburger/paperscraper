# Paper Scraper - Implementation Plan Overview

> **📖 Documentation Navigation:** This document provides a **high-level overview** of all 37 sprints.
> **For detailed sprint-by-sprint implementation**, see **[docs/implementation/](docs/implementation/)** (10 phase documents).
>
> **For current status:**
> - **[docs/implementation/STATUS.md](docs/implementation/STATUS.md)** - Current state & metrics
> - **[docs/INDEX.md](docs/INDEX.md)** - Master navigation hub
> - **[CLAUDE.md](CLAUDE.md)** - AI agent quick start

---

## Executive Summary

**Paper Scraper** was built across **37 sprints** (10 development phases) from January 2024 to February 2026.

**Current State (2026-02-10):**
- **24 backend modules** with 208+ API endpoints
- **841 pytest tests** (unit + integration)
- **40+ database tables** with pgvector support
- **28 frontend pages** with full routing
- **6 arq background workers** for async processing
- **Full i18n** (English + German)
- **Comprehensive E2E testing** with Playwright

---

## Phase Overview

### Phase 1: Foundation & MVP (Sprints 1-6) ✅

**Duration:** 12 weeks (Jan-Mar 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **1** | Foundation & Auth | FastAPI setup, PostgreSQL + pgvector, JWT auth, Docker Compose |
| **2** | Papers & Ingestion | Paper models, OpenAlex/Crossref clients, DOI import, async ingestion via arq |
| **3** | AI Scoring Pipeline | 5-dimension scoring, LLM client abstraction, embedding generation |
| **4** | Projects & KanBan | Project models, KanBan pipeline, stage management |
| **5** | Search & Discovery | Fulltext search (pg_trgm), semantic search (pgvector HNSW), hybrid RRF ranking |
| **6** | Frontend MVP | React 18 + Vite setup, TanStack Query, Shadcn/UI, routing, paper list/detail pages |

**Detailed Documentation:** [docs/implementation/PHASE_01_FOUNDATION.md](docs/implementation/PHASE_01_FOUNDATION.md)

---

### Phase 2: Feature Completion (Sprints 7-12) ✅

**Duration:** 12 weeks (Mar-Jun 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **7** | Production Hardening | Sentry, Langfuse, slowapi rate limiting, JSON logging, One-Line Pitch generator |
| **8** | Ingestion Expansion | PubMed API client, arXiv API client, PDF upload + extraction (PyMuPDF), MinIO storage |
| **9** | Scoring Enhancements | Simplified abstracts, enhanced score evidence, paper notes with @mentions, author badges |
| **10** | Author Intelligence | Author profiles with h-index/citations, contact tracking (CRM), OpenAlex enrichment |
| **11** | Search & Discovery | Saved searches with share tokens, alert system (daily/weekly), paper classification (LLM-based) |
| **12** | Analytics & Export | Dashboard metrics, team activity stats, CSV/PDF/BibTeX export |

**Detailed Documentation:** [docs/implementation/PHASE_02_FEATURES.md](docs/implementation/PHASE_02_FEATURES.md)

---

### Phase 3: Beta Readiness (Sprints 13-15) ✅

**Duration:** 6 weeks (Jun-Jul 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **13** | User Management | Team invitations, email verification, password reset, Resend integration |
| **14** | UX Polish | Onboarding wizard (4-step), empty states, confirmation dialogs, toast notifications |
| **15** | Deployment | CI/CD pipelines (GitHub Actions), pre-commit hooks, deployment documentation |

**Detailed Documentation:** [docs/implementation/PHASE_03_BETA.md](docs/implementation/PHASE_03_BETA.md)

---

### Phase 4: Lovable Prototype Features (Sprints 16-19) ✅

**Duration:** 8 weeks (Jul-Sep 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **16** | Researcher Groups | Group management, AI-suggested members (keyword-based), mailing lists, speaker pools |
| **17** | Technology Transfer | Conversation management, stage-based workflow, message threading, AI-suggested next steps |
| **18** | Research Submission | Submission portal, researcher self-submission, AI analysis, commercialization scoring |
| **19** | Gamification & Knowledge | Badge system (15+ types), auto-award engine, knowledge source management |

**Detailed Documentation:** [docs/implementation/PHASE_04_LOVABLE.md](docs/implementation/PHASE_04_LOVABLE.md)

---

### Phase 5: Stabilization & Frontend Integration (Sprints 20-21) ✅

**Duration:** 3 weeks (Sep 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **20** | Critical Fixes | Database migration fixes, enum conflict resolution, FK constraint validation |
| **21** | Frontend Integration | Groups UI, Transfer UI, Submissions UI, Badges UI, Knowledge UI |

**Detailed Documentation:** [docs/implementation/PHASE_05_STABILIZATION.md](docs/implementation/PHASE_05_STABILIZATION.md)

---

### Phase 6: Security & AI Advancement (Sprints 22-24) ✅

**Duration:** 6 weeks (Sep-Nov 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **22** | Security Hardening | Granular RBAC (permissions.py), account lockout, token blacklist, security headers |
| **23** | 6-Dimension Scoring | Team Readiness dimension added, model settings module (org-level LLM config) |
| **24** | AI Intelligence | Advanced scoring features, LLM provider flexibility, cost tracking |

**Detailed Documentation:** [docs/implementation/PHASE_06_SECURITY.md](docs/implementation/PHASE_06_SECURITY.md)

---

### Phase 7: Platform & Developer Experience (Sprints 25-27) ✅

**Duration:** 6 weeks (Nov-Dec 2024)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **25** | Developer API | API keys, webhooks, repository sources, MCP server implementation |
| **26** | UX Polish | Keyboard navigation (Cmd+K), mobile responsiveness, notification center |
| **27** | Analytics & Reporting | Scheduled reports, advanced analytics, funnel visualization, benchmarks |

**Detailed Documentation:** [docs/implementation/PHASE_07_PLATFORM.md](docs/implementation/PHASE_07_PLATFORM.md)

---

### Phase 8: Enterprise Readiness (Sprints 28-30) ✅

**Duration:** 6 weeks (Dec 2024 - Jan 2025)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **28** | Compliance & Governance | Audit logging (GDPR), data retention policies, SOC2 compliance framework |
| **29** | Internationalization | react-i18next setup, EN/DE translations (~400 keys), organization branding (logo upload) |
| **30** | Technical Debt | Code hygiene, SQL escaping centralization, compliance handler simplification, AuthService split planning |

**Detailed Documentation:** [docs/implementation/PHASE_08_ENTERPRISE.md](docs/implementation/PHASE_08_ENTERPRISE.md)

---

### Phase 9: Quality & Production Readiness (Sprints 31-36) ✅

**Duration:** 6 weeks (Jan-Feb 2025)
**Status:** Complete

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **31** | Bug Fixes & RBAC | RBAC enforcement on all 24 routers, client export fixes, permission system hardening |
| **32** | Test Coverage | Alert tests, saved search tests, model settings tests, coverage gaps filled |
| **33** | Frontend Unit Tests | usePapers, useNotifications, useSavedSearches, useAlerts hooks tested |
| **34** | Alerts Page | Dedicated alerts page with CRUD, results history, manual trigger |
| **35** | Complete i18n | Full EN/DE coverage, language switcher, translation key organization |
| **36** | Server-side Notifications | PostgreSQL-backed notifications, frontend polling (30s/60s), cross-device sync |

**Detailed Documentation:** [docs/implementation/PHASE_09_QUALITY.md](docs/implementation/PHASE_09_QUALITY.md)

---

### Phase 10: Foundations Pipeline (Sprint 37) ✅

**Duration:** 1-2 weeks (Feb 2026)
**Status:** Slice 1 Complete (2026-02-10)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **37** | Foundations Pipeline | Multi-source async ingestion (PubMed, arXiv, Semantic Scholar), run tracking, pre-created runs, unified worker path |

**Key Features:**
- Source-specific async endpoints (`/papers/ingest/{source}/async`)
- Run pre-creation before queue enqueue (status=queued)
- `ingest_run_id` exposed in API responses for traceability
- Unified `ingest_source_task` worker (compatibility wrapper for OpenAlex)
- RBAC adjustment: ingestion runs now use `PAPERS_READ` permission
- Architecture documentation governance formalized (ADR-023)
- CI quality gate enforces 01/04/05 documentation updates

**Detailed Documentation:** [docs/implementation/PHASE_10_FOUNDATIONS.md](docs/implementation/PHASE_10_FOUNDATIONS.md)

---

## Key Metrics

### Backend
- **24 modules** (analytics, alerts, audit, auth, authors, badges, compliance, developer, email, export, groups, ingestion, integrations, knowledge, model_settings, notifications, papers, projects, reports, saved_searches, scoring, search, submissions, transfer)
- **208+ API endpoints** across 22 routers
- **6 background job types** (ingestion, scoring, badges, alerts, retention, reports)
- **841 pytest tests** (unit + integration)
- **40+ database tables** with PostgreSQL 16 + pgvector

### Frontend
- **28 pages** with React Router
- **80+ components** (Shadcn/UI + custom)
- **E2E test coverage** with Playwright
- **2 languages** (EN/DE via react-i18next)

### Data
- **6 paper sources** (OpenAlex, PubMed, arXiv, Crossref, DOI, PDF)
- **6 scoring dimensions** (Novelty, IP-Potential, Marketability, Feasibility, Commercialization, Team Readiness)
- **Multi-provider LLM support** (GPT-5 mini default, configurable per-org)

---

## Architecture Decisions

All architectural decisions are documented in **[docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md)** (23 ADRs).

### Key Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| **001** | Modularer Monolith | Faster iteration, simpler debugging, lower costs |
| **002** | PostgreSQL + pgvector (HNSW) | One database, native JOINs, cost-effective |
| **003** | Multi-provider LLM (GPT-5 mini default) | No vendor lock-in, cost-efficient |
| **004** | arq for background jobs | Async-native, simpler than Celery |
| **005** | Self-hosted PostgreSQL + Custom JWT | Full control, no vendor lock-in |
| **021** | Granular RBAC | Fine-grained access control |
| **022** | Foundations Ingestion Pipeline | Multi-source async ingestion with run tracking |
| **023** | CI Documentation Gate | Enforces architecture docs updates |

**See:** [docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md) for all 23 ADRs

---

## User Stories Implemented

**All 64 user stories** from [02_USER_STORIES.md](02_USER_STORIES.md) have been implemented across 18 feature domains:

1. Paper Management (P1-P7) - ✅ Sprints 1-6
2. KanBan Board (K1-K4) - ✅ Sprint 4
3. Researcher Management (R1-R5) - ✅ Sprint 10
4. Researcher Groups (G1-G4) - ✅ Sprints 16, 21
5. Technology Transfer (T1-T6) - ✅ Sprints 17, 21
6. Search & Discovery (S1-S4) - ✅ Sprints 5, 11, 26-27
7. Reports & Analytics (A1-A5) - ✅ Sprints 12, 27
8. Alerts & Notifications (N1-N4) - ✅ Sprints 11, 26, 36
9. User Settings (U1-U4) - ✅ Sprints 13-14, 29
10. Organization Settings (O1-O4) - ✅ Sprints 13, 25, 29
11. Model Settings (M1-M4) - ✅ Sprint 23
12. Repository Settings (RS1-RS3) - ✅ Sprint 25
13. Developer Settings (D1-D3) - ✅ Sprint 25
14. Compliance & Governance (C1-C3) - ✅ Sprints 22, 28
15. Keyboard Shortcuts (KB1-KB3) - ✅ Sprint 26
16. Gamification (GA1-GA3) - ✅ Sprints 19, 21
17. Research Submission (SUB1-SUB3) - ✅ Sprints 18, 21
18. Knowledge Management (KM1-KM2) - ✅ Sprints 19, 21

**See:** [02_USER_STORIES.md](02_USER_STORIES.md) for complete user story catalog

---

## Implementation Patterns

### Backend Module Structure

Every module follows this pattern:

```
paper_scraper/modules/{module}/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic v2 DTOs
├── service.py     # Business logic (async, type-hinted)
└── router.py      # FastAPI endpoints with RBAC
```

### Frontend Feature Pattern

Feature components organized by domain:

```
frontend/src/
├── pages/         # Route components
├── components/    # Shared & feature components
├── hooks/         # TanStack Query hooks (use{Resource}.ts)
├── lib/           # API client, utilities
└── types/         # TypeScript types
```

### Background Jobs Pattern

arq tasks for async processing:

```python
# jobs/{task_name}.py
async def {task}_task(ctx, ...):
    """Task description."""
    async with get_db_session() as db:
        # Business logic
        pass

# Register in jobs/worker.py
class WorkerSettings:
    functions = [{task}_task, ...]
    cron_jobs = [arq.cron(...)] if needed
```

---

## Testing Strategy

### Backend (841 tests)

- **Unit tests:** Service layer (business logic)
- **Integration tests:** API endpoints (FastAPI TestClient)
- **Test infrastructure:** testcontainers-postgres (real PostgreSQL with pgvector), FakeRedis
- **Coverage:** ~85%

**Run:** `pytest tests/ -v --cov=paper_scraper`

### Frontend

- **Unit tests:** Hooks & utilities (Vitest)
- **E2E tests:** Critical user flows (Playwright)
- **Coverage:** Component tests + E2E

**Run:** `cd frontend && npm test` (unit), `cd e2e && npm test` (E2E)

---

## Documentation Governance (ADR-023)

_Updated on 2026-02-10_

**Mandatory Documentation Updates:**

For every architecture-impacting change, the following **must** be updated in the same commit:

1. **[01_TECHNISCHE_ARCHITEKTUR.md](01_TECHNISCHE_ARCHITEKTUR.md)** - Runtime architecture & data flow
2. **[docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md)** - New/updated ADRs
3. **This document** - Delivery status & scope progression
4. Add explicit date markers (`Updated on YYYY-MM-DD`)

**CI Enforcement:**
- `.github/workflows/ci.yml` runs `.github/scripts/check_arch_docs_gate.sh`
- PR fails if architecture-impacting files changed without documentation updates
- Ensures documentation stays in sync with implementation

**See:** ADR-023 in [docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md)

---

## Known Issues & Technical Debt

**High Priority:** None currently identified (Sprint 30 cleanup completed)

**Medium Priority:**
- Implement Redis caching layer for frequently accessed data
- Add rate limiting per organization tier
- Optimize large KanBan board rendering (>1000 papers)

**Low Priority:**
- Extract chart components from AnalyticsPage (1,192 lines)
- Implement ORCID author enrichment (currently stub)
- Implement Semantic Scholar enrichment (currently stub)
- Add permanent logo proxy endpoint (currently 24h pre-signed URLs)

**Detailed Tracking:** [docs/implementation/TECHNICAL_DEBT.md](docs/implementation/TECHNICAL_DEBT.md)

---

## Future Enhancements

**Potential next features:**
- Advanced analytics (cohort analysis, funnel tracking)
- White-label branding customization
- Mobile app (React Native)
- API rate limiting per tier
- Redis caching layer
- Slack/Teams integration
- Advanced IP analytics (patent search integration)
- Batch operations UI

**Detailed Backlog:** [docs/implementation/FUTURE_ENHANCEMENTS.md](docs/implementation/FUTURE_ENHANCEMENTS.md)

---

## Development Resources

### Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations
alembic upgrade head

# Run backend tests
pytest tests/ -v

# Run frontend dev
cd frontend && npm run dev

# Run E2E tests
cd e2e && npm test
```

### URLs

- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs (OpenAPI)
- **Frontend:** http://localhost:3000
- **MinIO Console:** http://localhost:9001

### Key Commands

```bash
# Backend
pytest tests/ -v --cov=paper_scraper  # Tests with coverage
alembic upgrade head                   # Apply migrations
alembic revision --autogenerate        # Create migration
arq paper_scraper.jobs.worker.WorkerSettings  # Run worker

# Frontend
cd frontend && npm test                # Unit tests
cd e2e && npm test                     # E2E tests
cd frontend && npm run lint            # Linting

# Code Quality
ruff check .                           # Python linting
mypy paper_scraper/                    # Type checking
```

---

## See Also

**For current status:**
- [docs/implementation/STATUS.md](docs/implementation/STATUS.md) - Current state & metrics
- [docs/INDEX.md](docs/INDEX.md) - Master documentation hub

**For architecture:**
- [docs/architecture/DECISIONS.md](docs/architecture/DECISIONS.md) - All 23 ADRs
- [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md) - System architecture
- [docs/architecture/TECH_STACK.md](docs/architecture/TECH_STACK.md) - Complete tech stack

**For development:**
- [CLAUDE.md](CLAUDE.md) - AI agent quick start (350 lines)
- [docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md) - Code conventions
- [docs/development/TESTING_GUIDE.md](docs/development/TESTING_GUIDE.md) - Testing patterns

**For detailed sprint history:**
- [docs/implementation/PHASE_01_FOUNDATION.md](docs/implementation/PHASE_01_FOUNDATION.md) - Sprints 1-6
- [docs/implementation/PHASE_02_FEATURES.md](docs/implementation/PHASE_02_FEATURES.md) - Sprints 7-12
- [docs/implementation/PHASE_03_BETA.md](docs/implementation/PHASE_03_BETA.md) - Sprints 13-15
- [docs/implementation/PHASE_04_LOVABLE.md](docs/implementation/PHASE_04_LOVABLE.md) - Sprints 16-19
- [docs/implementation/PHASE_05_STABILIZATION.md](docs/implementation/PHASE_05_STABILIZATION.md) - Sprints 20-21
- [docs/implementation/PHASE_06_SECURITY.md](docs/implementation/PHASE_06_SECURITY.md) - Sprints 22-24
- [docs/implementation/PHASE_07_PLATFORM.md](docs/implementation/PHASE_07_PLATFORM.md) - Sprints 25-27
- [docs/implementation/PHASE_08_ENTERPRISE.md](docs/implementation/PHASE_08_ENTERPRISE.md) - Sprints 28-30
- [docs/implementation/PHASE_09_QUALITY.md](docs/implementation/PHASE_09_QUALITY.md) - Sprints 31-36
- [docs/implementation/PHASE_10_FOUNDATIONS.md](docs/implementation/PHASE_10_FOUNDATIONS.md) - Sprint 37

---

**Last Updated:** 2026-02-10
**Document Status:** Refactored to overview format with cross-references to detailed phase documents
**Lines:** 552 (reduced from 6,642 = 92% reduction)
