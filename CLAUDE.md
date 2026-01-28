# Paper Scraper - Claude Code Project Context

## Projekt-Überblick

**Paper Scraper** ist eine AI-powered SaaS-Plattform zur automatisierten Analyse wissenschaftlicher Publikationen. Zielgruppen: Technology Transfer Offices (TTOs), VCs, Corporate Innovation Teams.

### Kernwertversprechen
- **Papers automatisch importieren** aus OpenAlex, PubMed, arXiv, via DOI oder PDF
- **5-dimensionales AI-Scoring**: Novelty, IP-Potential, Marketability, Feasibility, Commercialization
- **KanBan-Pipeline** für strukturiertes Paper-Management
- **Semantische Suche** zur Entdeckung ähnlicher Forschung

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
│   ├── modules/
│   │   ├── auth/               # User, Organization, JWT
│   │   ├── papers/             # Paper, Author, Ingestion
│   │   ├── scoring/            # AI Scoring Pipeline
│   │   ├── projects/           # KanBan, Pipeline
│   │   └── search/             # Fulltext, Semantic
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
├── tests/                      # pytest
├── alembic/                    # Migrations
├── docker-compose.yml
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
users (id, organization_id, email, hashed_password, role)

-- Papers
papers (id, doi, title, abstract, source, embedding vector(1536))
authors (id, orcid, name, affiliations, h_index)
paper_authors (paper_id, author_id, position, is_corresponding)

-- Scoring
paper_scores (
  paper_id, organization_id,
  novelty, ip_potential, marketability, feasibility, commercialization,
  overall_score, confidence, model_version
)

-- Pipeline
projects (id, organization_id, name, stages, scoring_weights)
paper_project_status (paper_id, project_id, stage, assigned_to, rejection_reason)
```

---

## API Struktur

```
/api/v1/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   └── GET  /me
│
├── /papers
│   ├── GET  /               # List with filters
│   ├── GET  /{id}           # Detail
│   ├── POST /ingest/doi     # Import by DOI
│   ├── POST /ingest/pubmed  # Batch import
│   └── POST /{id}/score     # Trigger scoring
│
├── /projects
│   ├── GET  /               # List
│   ├── POST /               # Create
│   ├── GET  /{id}/kanban    # KanBan view
│   └── PATCH /{id}/papers/{paper_id}/move
│
└── /search
    └── POST /               # Unified search
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

**Scoring-Pipeline:**
1. Paper → Embedding generieren
2. Ähnliche Papers finden (pgvector)
3. Pro Dimension: Prompt → LLM → Parse JSON
4. Aggregieren (gewichteter Durchschnitt)
5. In DB speichern

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

# Tests
pytest tests/ -v

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
| `modules/scoring/prompts/` | LLM Prompt Templates |
| `modules/scoring/llm_client.py` | LLM Provider Abstraktion |
| `frontend/src/lib/api.ts` | API Client |
| `docker-compose.yml` | Lokale Services |

---

## Referenz-Dokumentation

- `01_TECHNISCHE_ARCHITEKTUR.md` - System Design
- `02_USER_STORIES.md` - Priorisierter Backlog
- `03_CLAUDE_CODE_GUIDE.md` - Entwicklungs-Workflow
- `04_ARCHITECTURE_DECISIONS.md` - ADRs
- `05_IMPLEMENTATION_PLAN.md` - Sprint-Plan

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
