# Paper Scraper - Claude Code Project Context

## Projekt-Überblick

**Paper Scraper** ist eine AI-powered SaaS-Plattform zur automatisierten Analyse wissenschaftlicher Publikationen. Zielgruppen: Technology Transfer Offices (TTOs), VCs, Corporate Innovation Teams.

### Kernwertversprechen
- **Papers automatisch importieren** aus OpenAlex, PubMed, arXiv, via DOI oder PDF
- **6-dimensionales AI-Scoring**: Novelty, IP-Potential, Marketability, Feasibility, Commercialization, Team Readiness
- **KanBan-Pipeline** für strukturiertes Paper-Management
- **Semantische Suche** zur Entdeckung ähnlicher Forschung
- **Technology Transfer Workflows** für Researcher-Outreach
- **Gamification & Badges** für Team-Engagement

---

## Tech Stack

| Layer | Technologie |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy (async), Pydantic v2 |
| **Database** | PostgreSQL 16 + pgvector (HNSW index) |
| **Queue** | arq (async-native) + Redis |
| **Storage** | MinIO (S3-kompatibel) |
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, Shadcn/UI |
| **AI/LLM** | Flexible Provider (GPT-5 mini default), text-embedding-3-small |
| **Data Sources** | OpenAlex, EPO OPS, arXiv, PubMed, Crossref, Semantic Scholar |
| **Monitoring** | Langfuse (LLM), Sentry (Errors) |

---

## Projektstruktur

```
paper_scraper/
├── paper_scraper/              # Python Backend Package
│   ├── core/
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # SQLAlchemy async session
│   │   ├── security.py         # JWT, password hashing
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── modules/                # 17 Feature-Module
│   │   ├── analytics/          # Team & paper metrics, dashboard
│   │   ├── alerts/             # Search alerts & notifications
│   │   ├── audit/              # Security audit logging (GDPR compliance)
│   │   ├── auth/               # User, Organization, JWT, Team Invitations, GDPR
│   │   ├── authors/            # Author CRM, contacts
│   │   ├── badges/             # Gamification & achievements
│   │   ├── email/              # Transactional emails (Resend)
│   │   ├── export/             # CSV, PDF, BibTeX export
│   │   ├── groups/             # Researcher groups & collaboration
│   │   ├── knowledge/          # Knowledge management
│   │   ├── model_settings/     # LLM model configuration
│   │   ├── papers/             # Paper, Author, Ingestion
│   │   ├── projects/           # KanBan, Pipeline
│   │   ├── saved_searches/     # Saved searches & sharing
│   │   ├── scoring/            # AI Scoring Pipeline (6 dimensions)
│   │   ├── search/             # Fulltext, Semantic
│   │   ├── submissions/        # Research submission portal
│   │   └── transfer/           # Technology transfer conversations
│   │
│   ├── jobs/                   # arq Background Tasks (async-native)
│   │   ├── worker.py           # arq WorkerSettings
│   │   ├── ingestion.py
│   │   └── scoring.py
│   │
│   └── api/
│       ├── main.py             # FastAPI App
│       ├── dependencies.py     # DI
│       └── v1/router.py        # API Routes
│
├── frontend/                   # React Frontend
│   └── src/
│       ├── components/         # Reusable UI
│       ├── features/           # Feature Components
│       ├── hooks/              # Custom Hooks
│       ├── lib/api.ts          # API Client
│       └── pages/              # Route Pages
│
├── tests/                      # pytest Backend-Tests
├── e2e/                        # Playwright E2E Tests
│   ├── tests/                  # Test specs
│   └── playwright.config.ts    # Playwright config
├── .github/workflows/          # CI/CD Pipelines
│   ├── ci.yml                  # Continuous Integration
│   └── deploy.yml              # Deployment
├── alembic/                    # Migrations
├── docker-compose.yml
├── DEPLOYMENT.md               # Deployment Guide
└── pyproject.toml
```

---

## Coding Konventionen

### Python Backend

```python
# ✅ RICHTIG: Async, typed, documented
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

# ❌ FALSCH: Blocking, untyped
def get_paper(db, id):
    return db.query(Paper).filter(Paper.id == id).first()
```

**Regeln:**
- Async/await für alle I/O
- Type hints überall
- Google-Style Docstrings
- Absolute Imports
- Pydantic für alle DTOs

### TypeScript Frontend

```typescript
// ✅ RICHTIG: Typed, hooks, query
const usePapers = (filters: PaperFilters) => {
  return useQuery({
    queryKey: ['papers', filters],
    queryFn: () => api.papers.list(filters),
  });
};

// ❌ FALSCH: any, no query key
const usePapers = () => {
  const [papers, setPapers] = useState<any>([]);
  useEffect(() => { fetch('/papers').then(r => setPapers(r)); }, []);
};
```

**Regeln:**
- TanStack Query für Server State
- Zod für Runtime Validation
- Barrel Exports (index.ts)
- Shadcn/UI Komponenten

---

## Datenmodell (Core)

```sql
-- Organizations & Users
organizations (id, name, type, subscription_tier, settings)
users (id, organization_id, email, hashed_password, role, email_verified,
       email_verification_token, password_reset_token,
       onboarding_completed, onboarding_completed_at)

-- Team Invitations
team_invitations (
  id, organization_id, email, role, token, created_by_id,
  status, expires_at, created_at
)

-- Papers
papers (id, doi, title, abstract, source, embedding vector(1536))
authors (id, orcid, name, affiliations, h_index, citation_count, works_count)
paper_authors (paper_id, author_id, position, is_corresponding)

-- Author Contacts (CRM)
author_contacts (
  id, author_id, organization_id, contacted_by_id,
  contact_type, contact_date, subject, notes,
  outcome, follow_up_date, paper_id
)

-- Scoring
paper_scores (
  paper_id, organization_id,
  novelty, ip_potential, marketability, feasibility, commercialization,
  overall_score, confidence, model_version
)

-- Pipeline
projects (id, organization_id, name, stages, scoring_weights)
paper_project_status (paper_id, project_id, stage, assigned_to, rejection_reason)

-- Saved Searches & Alerts
saved_searches (
  id, organization_id, created_by_id, name, description,
  query, mode, filters, is_public, share_token,
  alert_enabled, alert_frequency, last_alert_at, run_count
)
alerts (
  id, organization_id, user_id, saved_search_id,
  name, channel, frequency, min_results, is_active,
  last_triggered_at, trigger_count
)
alert_results (
  id, alert_id, status, papers_found, new_papers,
  paper_ids, delivered_at, error_message
)

-- Audit Logging (GDPR/Security Compliance)
audit_logs (
  id, user_id, organization_id, action, resource_type,
  resource_id, details, ip_address, user_agent, created_at
)
```

---

## API Struktur

```
/api/v1/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   ├── POST /refresh
│   ├── GET  /me
│   ├── PATCH /me
│   ├── POST /change-password
│   ├── POST /forgot-password      # Initiate password reset
│   ├── POST /reset-password       # Reset with token
│   ├── POST /verify-email         # Verify email address
│   ├── POST /resend-verification  # Resend verification email
│   ├── POST /invite               # Send team invitation (admin)
│   ├── GET  /invitation/{token}   # Get invitation info
│   ├── POST /accept-invite        # Accept team invitation
│   ├── GET  /invitations          # List pending invitations (admin)
│   ├── DELETE /invitations/{id}   # Cancel invitation (admin)
│   ├── GET  /users                # List organization users (admin)
│   ├── PATCH /users/{id}/role     # Update user role (admin)
│   ├── POST /users/{id}/deactivate   # Deactivate user (admin)
│   ├── POST /users/{id}/reactivate   # Reactivate user (admin)
│   ├── POST /onboarding/complete     # Mark onboarding as complete
│   ├── GET  /export-data             # Export user data (GDPR)
│   └── DELETE /delete-account        # Delete account (GDPR)
│
├── /audit
│   ├── GET  /               # List audit logs (admin)
│   ├── GET  /users/{id}     # Get user activity (admin)
│   └── GET  /my-activity    # Get own activity log
│
├── /papers
│   ├── GET  /               # List with filters
│   ├── GET  /{id}           # Detail
│   ├── DELETE /{id}         # Delete paper
│   ├── POST /ingest/doi     # Import by DOI
│   ├── POST /ingest/openalex # OpenAlex batch import
│   ├── POST /ingest/pubmed  # PubMed batch import
│   ├── POST /ingest/arxiv   # arXiv batch import
│   ├── POST /upload/pdf     # PDF file upload
│   ├── POST /{id}/generate-pitch # Generate AI pitch
│   ├── POST /{id}/generate-simplified-abstract # Generate simplified abstract
│   ├── GET  /{id}/notes     # List notes for paper
│   ├── POST /{id}/notes     # Create note on paper
│   ├── PUT  /{id}/notes/{note_id}    # Update note
│   └── DELETE /{id}/notes/{note_id}  # Delete note
│
├── /authors
│   ├── GET  /               # List authors in organization
│   ├── GET  /{id}           # Author profile with metrics
│   ├── GET  /{id}/detail    # Full detail with papers & contacts
│   ├── POST /{id}/contacts  # Log contact with author
│   ├── PATCH /{id}/contacts/{cid}  # Update contact
│   ├── DELETE /{id}/contacts/{cid} # Delete contact
│   ├── GET  /{id}/contacts/stats   # Contact statistics
│   └── POST /{id}/enrich    # Enrich from OpenAlex/ORCID
│
├── /projects
│   ├── GET  /               # List
│   ├── POST /               # Create
│   ├── GET  /{id}/kanban    # KanBan view
│   └── PATCH /{id}/papers/{paper_id}/move
│
├── /scoring
│   ├── POST /papers/{id}/score    # Trigger scoring
│   ├── GET  /papers/{id}/scores   # Get score history
│   ├── POST /papers/{id}/classify # Classify paper type
│   ├── POST /classification/batch # Batch classify
│   └── GET  /classification/unclassified # List unclassified papers
│
├── /search
│   └── POST /               # Unified search
│
├── /saved-searches
│   ├── GET  /               # List saved searches
│   ├── POST /               # Create saved search
│   ├── GET  /{id}           # Get saved search
│   ├── PATCH /{id}          # Update saved search
│   ├── DELETE /{id}         # Delete saved search
│   ├── POST /{id}/share     # Generate share link
│   ├── DELETE /{id}/share   # Revoke share link
│   ├── POST /{id}/run       # Execute saved search
│   └── GET  /shared/{token} # Get by share token (public)
│
├── /alerts
│   ├── GET  /               # List alerts
│   ├── POST /               # Create alert
│   ├── GET  /{id}           # Get alert
│   ├── PATCH /{id}          # Update alert
│   ├── DELETE /{id}         # Delete alert
│   ├── GET  /{id}/results   # Get alert history
│   ├── POST /{id}/test      # Test alert (dry run)
│   └── POST /{id}/trigger   # Manually trigger alert
│
├── /analytics
│   ├── GET  /dashboard      # Dashboard summary metrics
│   ├── GET  /team           # Team overview and activity
│   └── GET  /papers         # Paper import trends & scoring stats
│
├── /export
│   ├── GET  /csv            # Export papers to CSV
│   ├── GET  /bibtex         # Export papers to BibTeX
│   ├── GET  /pdf            # Export papers to PDF report
│   └── POST /batch          # Batch export with format selection
│
├── /groups                  # Researcher Groups
│   ├── GET  /               # List groups
│   ├── POST /               # Create group
│   ├── POST /{id}/members   # Add members
│   └── GET  /{id}/suggestions  # AI-based member suggestions
│
├── /transfer                # Technology Transfer
│   ├── GET  /conversations  # List conversations
│   ├── POST /conversations  # Start conversation
│   ├── POST /{id}/messages  # Send message
│   └── GET  /{id}/next-steps  # AI-suggested next steps
│
├── /submissions             # Research Submissions
│   ├── GET  /               # List submissions
│   ├── POST /               # Submit research
│   └── POST /{id}/analyze   # AI analysis
│
├── /badges                  # Gamification
│   ├── GET  /               # All badges
│   ├── GET  /my-badges      # User's badges
│   └── GET  /leaderboard    # Organization leaderboard
│
├── /knowledge               # Knowledge Management
│   └── [CRUD for knowledge sources]
│
└── /settings/models         # Model Configuration
    ├── GET  /               # List models
    ├── POST /               # Add model
    └── GET  /usage          # Usage stats
```

---

## Scoring Dimensionen

| Dimension | Score | Was wird bewertet? |
|-----------|-------|-------------------|
| **Novelty** | 0-10 | Technologische Neuheit vs. State-of-Art |
| **IP-Potential** | 0-10 | Patentierbarkeit, Prior Art, White Spaces |
| **Marketability** | 0-10 | Marktgröße, Industrien, Trends |
| **Feasibility** | 0-10 | TRL-Level, Time-to-Market, Dev-Kosten |
| **Commercialization** | 0-10 | Empfohlener Pfad, Entry Barriers |
| **Team Readiness** | 0-10 | Autoren Track Record, Industry Experience, Institutional Support |

**Scoring-Pipeline:**
1. Paper → Embedding generieren
2. Ähnliche Papers finden (pgvector)
3. Autoren-Metriken laden (h-index, works_count)
4. Pro Dimension: Prompt → LLM → Parse JSON
5. Aggregieren (gewichteter Durchschnitt)
6. In DB speichern

**Innovation Radar:** 6-Achsen-Radar-Chart visualisiert alle Dimensionen auf PaperDetailPage.

---

## Häufige Tasks

### Neuen API-Endpoint hinzufügen
```bash
1. Schema:    modules/<feature>/schemas.py
2. Service:   modules/<feature>/service.py
3. Router:    modules/<feature>/router.py
4. Register:  api/v1/router.py
5. Test:      tests/api/test_<feature>.py
```

### Neue Scoring-Dimension hinzufügen
```bash
1. Prompt:    scoring/prompts/<dimension>.jinja2
2. Scorer:    scoring/dimensions/<dimension>.py
3. Register:  scoring/orchestrator.py
4. Schema:    modules/scoring/schemas.py erweitern
5. Migration: alembic revision
```

### Background Job hinzufügen
```bash
1. Task:      jobs/<task_name>.py (async function)
2. Register:  jobs/worker.py (WorkerSettings.functions)
3. Schedule:  arq.cron() in WorkerSettings (wenn periodic)
```

---

## Entwicklungsumgebung

```bash
# Starten
docker-compose up -d

# URLs
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
Frontend: http://localhost:3000
MinIO:    http://localhost:9001 (Console)

# Backend Tests
pytest tests/ -v --cov=paper_scraper

# Frontend Unit Tests
cd frontend && npm test

# E2E Tests
cd e2e && npm test

# Migrations
alembic upgrade head
alembic revision --autogenerate -m "Description"

# arq Worker (manuell starten)
arq paper_scraper.jobs.worker.WorkerSettings
```

---

## Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `core/config.py` | Alle Environment Variables |
| `core/security.py` | JWT, Passwort-Hashing, Token-Generierung |
| `core/permissions.py` | Granulares RBAC-System |
| `core/csv_utils.py` | CSV-Export mit Injection-Schutz |
| `core/storage.py` | S3/MinIO Storage Utilities |
| `api/middleware.py` | Rate Limiting, Security Headers |
| `modules/auth/service.py` | Auth-Service mit User Management, GDPR |
| `modules/audit/service.py` | Audit Logging Service |
| `modules/email/service.py` | E-Mail-Service (Resend) |
| `modules/scoring/prompts/` | LLM Prompt Templates (11 Templates) |
| `modules/scoring/llm_client.py` | LLM Provider Abstraktion |
| `modules/scoring/dimensions/` | 6 Scoring-Dimensionen |
| `modules/model_settings/` | Org-Level LLM-Konfiguration |
| `jobs/badges.py` | Badge Auto-Award Engine |
| `frontend/src/lib/api.ts` | API Client (17 Namespaces) |
| `frontend/src/components/ui/` | Shadcn/UI-style Components |
| `frontend/src/components/InnovationRadar.tsx` | 6-Axis Score Visualization |
| `frontend/src/components/Onboarding/` | Onboarding Wizard (4-step) |
| `frontend/vitest.config.ts` | Vitest Unit Test Configuration |
| `e2e/playwright.config.ts` | Playwright E2E Test Configuration |
| `.github/workflows/ci.yml` | CI Pipeline |
| `.github/workflows/deploy.yml` | Deployment Pipeline |
| `DEPLOYMENT.md` | Deployment Guide |
| `docker-compose.yml` | Lokale Services |

### Frontend UI Components (frontend/src/components/ui/)

| Component | Zweck |
|-----------|-------|
| `EmptyState.tsx` | Empty states mit Icon, Titel, Beschreibung, Action |
| `Skeleton.tsx` | Loading skeletons (Card, Table, Kanban, Stats, Avatar) |
| `Toast.tsx` | Toast notifications mit ToastProvider & useToast |
| `ConfirmDialog.tsx` | Bestätigungsdialog (default/destructive Varianten) |
| `ErrorBoundary.tsx` | React Error Boundary mit Fallback UI |

---

## Referenz-Dokumentation

- `01_TECHNISCHE_ARCHITEKTUR.md` - System Design
- `02_USER_STORIES.md` - Priorisierter Backlog
- `03_CLAUDE_CODE_GUIDE.md` - Entwicklungs-Workflow
- `04_ARCHITECTURE_DECISIONS.md` - ADRs
- `05_IMPLEMENTATION_PLAN.md` - Sprint-Plan
- `DEPLOYMENT.md` - Deployment & Operations Guide

---

## Quick Reference

```python
# Tenant-isolierte Query
papers = await db.execute(
    select(Paper).where(Paper.organization_id == org_id)
)

# LLM-Aufruf
result = await llm_client.complete(
    prompt=prompt,
    system="Du bist ein Experte...",
    temperature=0.3
)

# Embedding-Suche
similar = await db.execute(
    select(Paper)
    .order_by(Paper.embedding.cosine_distance(query_embedding))
    .limit(5)
)
```
