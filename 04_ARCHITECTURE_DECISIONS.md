# Paper Scraper - Architecture Decision Records (ADRs)

## Übersicht

Dieses Dokument enthält alle wichtigen Architekturentscheidungen für Paper Scraper im ADR-Format. Jede Entscheidung ist nachvollziehbar dokumentiert mit Kontext, Alternativen und Konsequenzen.

---

## ADR-001: Monolith-First Architektur

### Status
**Akzeptiert** - 2024-01

### Kontext
Die ursprüngliche Notion-Dokumentation beschreibt eine komplexe Microservices-Architektur mit Kubernetes, separaten Services für Document Processing, Scoring Engine, Knowledge Graph, etc. Diese Architektur wäre für ein Startup mit 2 Gründern nicht wartbar.

### Entscheidung
Wir starten mit einem **modularen Monolith** (FastAPI Backend) und migrieren erst zu Microservices wenn:
- Team > 5 Entwickler
- Klare Service-Boundaries durch Traffic-Patterns identifiziert
- Skalierungsengpässe in spezifischen Modulen

### Alternativen betrachtet

| Option | Vorteile | Nachteile |
|--------|----------|-----------|
| **Microservices von Anfang an** | Skalierbar, Team-unabhängig | Overhead, Komplexität, DevOps-Last |
| **Serverless (Lambda/Functions)** | Pay-per-use, Auto-scaling | Cold starts, State-Management schwer |
| **Modularer Monolith** ✓ | Einfach, schnell, refactorbar | Skalierung begrenzt |

### Konsequenzen
- (+) Schnellere Entwicklung in früher Phase
- (+) Einfacheres Debugging und Deployment
- (+) Niedrigere Infrastruktur-Kosten
- (-) Muss später refactored werden bei Erfolg
- (-) Keine unabhängige Skalierung von Komponenten

### Migrations-Trigger
- Response-Zeit > 2s konsistent für Scoring
- >100 concurrent Users
- Team > 5 Entwickler

---

## ADR-002: PostgreSQL + pgvector statt separater Vector-DB

### Status
**Akzeptiert** - 2024-01

### Kontext
Für semantische Suche benötigen wir Vector-Embeddings. Die Optionen sind:
1. Dedizierte Vector-DB (Pinecone, Weaviate, Qdrant)
2. PostgreSQL Extension (pgvector)
3. In-Memory (FAISS)

### Entscheidung
Wir verwenden **PostgreSQL mit pgvector Extension** als einzige Datenbank für sowohl relationale als auch Vektor-Daten.

### Begründung

| Kriterium | Pinecone | Weaviate | pgvector |
|-----------|----------|----------|----------|
| Setup-Komplexität | Mittel | Hoch | Niedrig |
| Kosten | $$$ | $$ | $ |
| Skalierung | Sehr gut | Gut | Gut bis 10M |
| Joins mit relational | Unmöglich | Schwer | Native |
| Maintenance | Managed | Self-hosted | Mit Postgres |

### Konsequenzen
- (+) Eine Datenbank zu managen
- (+) Native JOINs zwischen Papers und Embeddings
- (+) Transaktionale Konsistenz
- (+) Kosteneffizient
- (-) Weniger Features als dedizierte Vector-DBs
- (-) Bei >10M Dokumenten evtl. Skalierungsprobleme

### Performance-Maßnahmen
```sql
-- HNSW Index für bessere Performance (auto-tuning, kein Training nötig)
CREATE INDEX ON papers USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Regelmäßiges VACUUM für Performance
SELECT cron.schedule('vector-maintenance', '0 3 * * *', 'VACUUM ANALYZE papers');
```

**Hinweis:** HNSW wurde gegenüber IVFFlat bevorzugt wegen:
- Kein periodisches Re-Training nötig
- Bessere Suchqualität bei gleicher Geschwindigkeit
- Selbst-optimierend bei wachsenden Datenmengen

### Fallback-Plan
Bei Performance-Problemen: Pinecone für Embeddings, Sync via Background-Job.

---

## ADR-003: Flexible LLM-Provider mit GPT-5 mini Default (Updated)

### Status
**Akzeptiert** - 2024-01 (Updated: 2026-01)

### Kontext
Für das 5-dimensionale Scoring benötigen wir leistungsfähige LLMs. Optionen:
- OpenAI (GPT-4, GPT-5 mini)
- Anthropic (Claude)
- Azure OpenAI
- Open-Source (Llama, Mistral via Ollama)
- Multi-Provider

### Entscheidung
**Provider-agnostische Architektur** mit **GPT-5 mini als Default** (kosteneffizient, gute Qualität).

### Begründung

| Provider | Qualität | Kosten | Latenz | Verfügbarkeit |
|----------|----------|--------|--------|---------------|
| **GPT-5 mini** | ★★★★☆ | $ | ~1s | 99.9% |
| GPT-4-turbo | ★★★★★ | $$$ | ~3s | 99.9% |
| Claude 3.5 Sonnet | ★★★★★ | $$ | ~2s | 99.5% |
| Azure OpenAI | ★★★★☆ | $$ | ~2s | 99.9% |
| Ollama (local) | ★★★☆☆ | Free | Variabel | Self-hosted |

### Implementierung
```python
# core/config.py - Provider-agnostic Configuration
LLM_PROVIDER: str = "openai"  # openai, anthropic, azure, ollama
LLM_MODEL: str = "gpt-5-mini"  # Can be overridden per-organization
LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"
LLM_TEMPERATURE: float = 0.3
LLM_MAX_TOKENS: int = 4096

# Provider-Abstraktion ermöglicht einfachen Wechsel
class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        pass

# Factory mit konfigurierbarem Default
def get_llm_client(provider: str = None, model: str = None) -> LLMClient:
    provider = provider or settings.LLM_PROVIDER
    clients = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "azure": AzureOpenAIClient,
        "ollama": OllamaClient
    }
    return clients[provider](model=model)
```

### Per-Organization Override
Organisationen können ihr bevorzugtes LLM-Modell in den Settings konfigurieren:
```python
organization.settings = {
    "llm_model": "gpt-4-turbo",  # Override default
    "scoring_weights": {...}
}
```

### Konsequenzen
- (+) Flexibilität bei Provider-Wahl
- (+) Kosteneffizient mit GPT-5 mini als Default
- (+) Kein Vendor Lock-in
- (+) Per-Organization anpassbar
- (-) Abstraktionsschicht zu warten
- (-) Unterschiedliche Qualität je nach Provider

### Kosten-Projektion (GPT-5 mini)
- ~1500 Token/Paper für vollständiges Scoring
- Bei 1000 Papers/Monat: ~$15/Monat
- Skaliert linear, Caching reduziert Re-Scoring

---

## ADR-004: arq für Background Jobs (Updated)

### Status
**Akzeptiert** - 2024-01 (Updated: 2026-01)

### Kontext
Batch-Ingestion und Scoring können nicht synchron in HTTP-Requests laufen. Optionen:
- Celery + Redis
- RQ (Redis Queue)
- Dramatiq
- arq (async)
- AWS Lambda/Cloud Functions

### Entscheidung
**arq mit Redis** als async-native Job Queue.

### Begründung

| Option | Async-native | Ecosystem | Monitoring | Learning Curve |
|--------|--------------|-----------|------------|----------------|
| Celery | Nein (wrapper) | ★★★★★ | Flower | Mittel |
| RQ | Nein | ★★★☆☆ | rq-dashboard | Niedrig |
| Dramatiq | Ja | ★★★☆☆ | APM | Mittel |
| **arq** | **Ja** | ★★☆☆☆ | Custom | **Niedrig** |

**arq gewählt** wegen:
- Native async/await Support (passt zum async FastAPI/SQLAlchemy Stack)
- Einfachere Setup (kein separater Beat-Prozess)
- Built-in Job Scheduling
- Direkte Redis-Integration
- Geringerer Overhead als Celery

### Task-Struktur
```python
# jobs/worker.py
import arq
from uuid import UUID

async def ingest_papers_task(ctx, source: str, query: str, project_id: UUID):
    """Batch-Import von OpenAlex/PubMed/arXiv"""
    async with get_db_session() as db:
        await ingestion_service.ingest(db, source, query, project_id)

async def score_paper_task(ctx, paper_id: UUID):
    """Score a single paper"""
    async with get_db_session() as db:
        await scoring_service.score_paper(db, paper_id)

async def generate_embeddings_task(ctx, paper_ids: list[UUID]):
    """Generate embeddings for papers"""
    async with get_db_session() as db:
        await embedding_service.generate_batch(db, paper_ids)

class WorkerSettings:
    functions = [ingest_papers_task, score_paper_task, generate_embeddings_task]
    redis_settings = arq.RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 600  # 10 minutes
```

### Konsequenzen
- (+) Native async/await - passt perfekt zum Stack
- (+) Einfacheres Setup als Celery
- (+) Built-in Scheduling (kein separater Beat-Prozess)
- (+) Geringerer Memory-Footprint
- (-) Kleineres Ecosystem als Celery
- (-) Weniger Monitoring-Tools (Custom-Lösung nötig)

---

## ADR-005: Self-hosted PostgreSQL + Custom JWT Auth (Updated)

### Status
**Akzeptiert** - 2026-01

### Kontext
Für die Datenbank und Authentifizierung gab es zwei Optionen:
1. Supabase (Managed PostgreSQL + Auth + Realtime)
2. Self-hosted PostgreSQL + Custom JWT

### Entscheidung
**Self-hosted PostgreSQL + pgvector** mit **Custom JWT Authentication**.

### Begründung

| Kriterium | Supabase | Self-hosted + Custom JWT |
|-----------|----------|--------------------------|
| Kontrolle | Begrenzt | Voll |
| Kosten (Skalierung) | $$$ | $ |
| Vendor Lock-in | Ja | Nein |
| Auth-Flexibilität | Begrenzt | Voll |
| DevOps-Aufwand | Niedrig | Mittel |
| On-Premise Option | Nein | Ja |

**Self-hosted gewählt** wegen:
- Volle Kontrolle über Datenbank-Konfiguration
- Keine Vendor-Abhängigkeit
- Flexibilität für Custom Auth-Flows
- Bessere Kosten bei Skalierung
- Option für On-Premise Deployment (Enterprise-Kunden)

### Implementation

**Database:**
- PostgreSQL 16 mit pgvector Extension
- Docker-basiert für lokale Entwicklung
- Managed PostgreSQL (z.B. AWS RDS, DigitalOcean) für Production

**Authentication:**
```python
# Custom JWT mit Access + Refresh Tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Token-Struktur
{
    "sub": "user_uuid",
    "org_id": "organization_uuid",
    "role": "admin|manager|member|viewer",
    "type": "access|refresh",
    "exp": timestamp
}
```

### Konsequenzen
- (+) Volle Kontrolle über alle Aspekte
- (+) Keine Vendor-Abhängigkeit
- (+) Flexibilität für Custom Requirements
- (+) Kosteneffizienter bei Skalierung
- (-) Mehr initialer Setup-Aufwand
- (-) Backups und Maintenance selbst managen
- (-) Auth-Logik selbst implementieren und warten

---

## ADR-006: Frontend Framework - React + Vite

### Status
**Akzeptiert** - 2024-01

### Kontext
Für das Frontend gibt es mehrere Optionen:
- React (Vite oder CRA)
- Next.js
- Vue.js
- Svelte

### Entscheidung
**React 18 + Vite + TypeScript + TailwindCSS + Shadcn/UI**

### Begründung

| Framework | Performance | DX | Ecosystem | SSR |
|-----------|-------------|-----|-----------|-----|
| React + Vite | ★★★★★ | ★★★★★ | ★★★★★ | Nein |
| Next.js | ★★★★☆ | ★★★★☆ | ★★★★★ | Ja |
| Vue 3 | ★★★★★ | ★★★★☆ | ★★★★☆ | Optional |
| Svelte | ★★★★★ | ★★★★★ | ★★★☆☆ | Optional |

React + Vite gewählt weil:
- Größtes Ecosystem
- Keine SSR nötig (B2B SaaS, kein SEO-kritisch)
- Schnellste DX mit Vite
- Shadcn/UI für konsistente Komponenten

### Stack-Details
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "@tanstack/react-query": "^5.0.0",  // Server State
    "react-router-dom": "^6.20.0",       // Routing
    "zustand": "^4.4.0",                 // Client State
    "zod": "^3.22.0",                    // Validation
    "tailwindcss": "^3.3.0",
    "@shadcn/ui": "latest"
  }
}
```

### Konsequenzen
- (+) Schnelle Entwicklung
- (+) Hot Module Replacement
- (+) Große Community
- (-) Kein SSR (aber nicht nötig)
- (-) Bundle-Size beachten

---

## ADR-007: Multi-Tenancy Strategie

### Status
**Akzeptiert** - 2024-01

### Kontext
Paper Scraper ist Multi-Tenant (mehrere Organisationen). Optionen:
1. Separate Datenbanken pro Tenant
2. Separate Schemas pro Tenant
3. Shared Tables mit Tenant-ID

### Entscheidung
**Shared Tables mit organization_id** als Foreign Key und Row-Level Security.

### Begründung

| Strategie | Isolation | Kosten | Komplexität | Skalierung |
|-----------|-----------|--------|-------------|------------|
| Separate DBs | ★★★★★ | $$$$ | Hoch | Schwer |
| Separate Schemas | ★★★★☆ | $$$ | Mittel | Mittel |
| Shared Tables | ★★★☆☆ | $ | Niedrig | Einfach |

Für ein SaaS mit <1000 Tenants ist Shared Tables optimal.

### Implementierung
```python
# Middleware setzt organization_id
class TenantMiddleware:
    async def __call__(self, request, call_next):
        org_id = extract_org_from_jwt(request)
        request.state.organization_id = org_id
        return await call_next(request)

# Alle Queries filtern automatisch
class TenantMixin:
    organization_id: UUID

    @classmethod
    async def query(cls, db: Session, **filters):
        org_id = get_current_org_id()
        return db.query(cls).filter(
            cls.organization_id == org_id,
            **filters
        )
```

### Konsequenzen
- (+) Einfachste Implementierung
- (+) Niedrigste Kosten
- (+) Einfache Queries
- (-) Weniger Isolation (mitigiert durch RLS)
- (-) Noisy Neighbor möglich (mitigiert durch Rate Limits)

---

## ADR-008: Prompt-Management mit Langfuse

### Status
**Akzeptiert** - 2024-01

### Kontext
LLM-Prompts müssen:
- Versioniert werden
- Getestet werden können
- Monitored werden (Latenz, Kosten, Qualität)

### Entscheidung
**Langfuse** als Prompt-Management und LLM-Observability Platform.

### Features genutzt
- Prompt-Versioning
- A/B-Testing von Prompts
- Cost Tracking pro Organization
- Latency Monitoring
- User Feedback Collection

### Integration
```python
from langfuse import Langfuse

langfuse = Langfuse()

@langfuse.observe()
async def score_novelty(paper: Paper) -> NoveltyResult:
    prompt = langfuse.get_prompt("novelty-scoring", version="2.1")

    trace = langfuse.trace(
        name="novelty-scoring",
        metadata={"paper_id": str(paper.id)}
    )

    result = await llm_client.complete(
        prompt.compile(paper=paper),
        trace=trace
    )

    trace.score(name="confidence", value=result.confidence)
    return result
```

### Konsequenzen
- (+) Professionelles Prompt-Management
- (+) Cost Visibility
- (+) Debugging von LLM-Issues
- (+) Basis für Prompt-Verbesserung
- (-) Zusätzliche Dependency
- (-) Kosten ($29/Monat Start)

---

## ADR-009: API-Versionierung

### Status
**Akzeptiert** - 2024-01

### Kontext
APIs müssen versioniert werden für:
- Breaking Changes
- Deprecation
- Multiple Client-Versionen

### Entscheidung
**URL-basierte Versionierung** mit `/api/v1/...`

### Begründung

| Methode | Beispiel | Vorteile | Nachteile |
|---------|----------|----------|-----------|
| URL-Path | `/api/v1/papers` | Klar, einfach | URL-Pollution |
| Header | `Accept: application/vnd.api.v1+json` | Sauber | Versteckt |
| Query | `/papers?version=1` | Flexibel | Unüblich |

### Implementierung
```python
# api/v1/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

@router.get("/papers")
async def list_papers():
    pass

# api/v2/router.py (zukünftig)
router_v2 = APIRouter(prefix="/api/v2")
```

### Deprecation Policy
- Neue Versionen mindestens 6 Monate parallel
- Deprecation-Header in Responses
- Migration-Guide in Docs

---

## ADR-010: Caching-Strategie

### Status
**Akzeptiert** - 2024-01

### Kontext
Performance-kritische Daten sollten gecacht werden:
- Paper-Embeddings
- Score-Ergebnisse
- User-Sessions
- API-Responses

### Entscheidung
**Redis** für Session/Cache mit folgender Strategie:

### Cache-Layers

| Layer | TTL | Invalidation |
|-------|-----|--------------|
| Session Cache | 24h | Logout/Token-Expire |
| Paper Score Cache | 7d | Re-Scoring |
| Embedding Cache | 30d | Nie (deterministic) |
| API Response Cache | 5min | Cache-Control Header |

### Implementierung
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/papers/{paper_id}")
@cache(expire=300)  # 5 Minuten
async def get_paper(paper_id: UUID):
    return await paper_service.get_paper(paper_id)

# Manuelle Invalidierung
async def invalidate_paper_cache(paper_id: UUID):
    await FastAPICache.clear(namespace=f"paper:{paper_id}")
```

### Konsequenzen
- (+) Schnellere Responses
- (+) Weniger DB-Load
- (+) Weniger LLM-Kosten (Score-Cache)
- (-) Komplexität bei Invalidierung
- (-) Stale Data möglich

---

## ADR-011: Production Hardening Stack

### Status
**Implementiert** - 2026-01 (Sprint 7)

### Kontext
Für Production-Readiness werden folgende Aspekte benötigt:
- Error Tracking und Alerting
- LLM Call Observability
- Rate Limiting zum Schutz vor Missbrauch
- Structured Logging für Debugging

### Entscheidung
**Sentry + Langfuse + slowapi + JSON Logging**

### Implementierung

**Error Tracking (Sentry):**
```python
# api/main.py
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1,
    )
```

**LLM Observability (Langfuse):**
```python
# modules/scoring/llm_client.py
from langfuse.decorators import observe

@observe(as_type="generation", name="openai-completion")
async def complete(self, prompt: str, ...) -> str:
    # Automatic tracking of: prompt, model, latency, tokens, cost
```

**Rate Limiting (slowapi):**
```python
# api/middleware.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
)

# Stricter limit for expensive operations
@limiter.limit(f"{settings.RATE_LIMIT_SCORING_PER_MINUTE}/minute")
async def score_paper(...): ...
```

**Structured Logging:**
```python
# core/logging.py
class JSONFormatter(logging.Formatter):
    def format(self, record) -> str:
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            ...
        })
```

### Konsequenzen
- (+) Vollständige Observability für Production
- (+) Schutz vor API-Missbrauch
- (+) Debugging-freundliche Logs
- (+) LLM-Kosten-Tracking via Langfuse
- (-) Zusätzliche externe Dependencies
- (-) Kosten für Sentry und Langfuse (kostenlose Tiers verfügbar)

---

## ADR-012: One-Line Pitch Generator

### Status
**Implementiert** - 2026-01 (Sprint 7)

### Kontext
TTOs und VCs benötigen schnell erfassbare Paper-Beschreibungen für Screening. Abstracts sind zu lang und technisch.

### Entscheidung
**AI-generierte One-Line Pitches** (max 15 Wörter) pro Paper.

### Implementierung
```python
# modules/scoring/pitch_generator.py
class PitchGenerator:
    async def generate(self, title: str, abstract: str, keywords: list) -> str:
        prompt = self.template.render(title=title, abstract=abstract, keywords=keywords)
        pitch = await self.llm.complete(prompt=prompt, temperature=0.7)
        return pitch.strip()[:15_words]
```

**Prompt-Design:**
- Fokus auf Business Value (nicht technische Details)
- Active Voice, compelling Language
- No Jargon (accessible to business audiences)

**API Endpoint:**
```
POST /api/v1/papers/{paper_id}/generate-pitch
Response: { "one_line_pitch": "..." }
```

### Konsequenzen
- (+) Schnelleres Paper-Screening
- (+) Business-freundliche Kommunikation
- (+) Konsistente Pitch-Qualität
- (-) LLM-Kosten pro Generation
- (-) Qualität abhängig von Abstract-Qualität

---

## ADR-013: Ingestion Expansion (PubMed, arXiv, PDF)

### Status
**Implementiert** - 2026-01 (Sprint 8)

### Kontext
Nutzer benötigen Zugang zu mehr Paper-Quellen als nur OpenAlex/DOI. Besonders für Life Sciences (PubMed), Preprints (arXiv) und manuelle Uploads (PDF).

### Entscheidung
**Multi-Source Ingestion Pipeline** mit einheitlichem Client-Interface und PDF-Verarbeitung.

### Implementierung

**API Clients (Abstract Base Class Pattern):**
```python
# modules/papers/clients/base.py
class BaseAPIClient(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int) -> list[dict]: ...
    @abstractmethod
    async def get_by_id(self, identifier: str) -> dict | None: ...
    @abstractmethod
    def normalize(self, raw_data: dict) -> dict: ...

# Implementierungen:
# - PubMedClient (E-utilities API, XML parsing)
# - ArxivClient (Atom API, rate limiting 1 req/3s)
```

**PDF Processing:**
```python
# modules/papers/pdf_service.py
class PDFService:
    def __init__(self):
        self.minio = Minio(...)  # S3-compatible storage

    async def upload_and_extract(self, file_content, filename, org_id):
        # 1. Upload to MinIO
        # 2. Extract text via PyMuPDF (fitz)
        # 3. Extract title (largest font on page 1)
        # 4. Extract abstract (regex patterns)
        return {"title": ..., "abstract": ..., "pdf_path": ...}
```

**API Endpoints:**
```
POST /api/v1/papers/ingest/pubmed   → IngestResult
POST /api/v1/papers/ingest/arxiv    → IngestResult
POST /api/v1/papers/upload/pdf      → PaperResponse (multipart/form-data)
```

**Frontend Import Modal:**
- Tab-basierte UI für alle 5 Quellen (DOI, OpenAlex, PubMed, arXiv, PDF)
- Drag & Drop für PDF Upload
- Category-Filter für arXiv

### Konsequenzen
- (+) Zugang zu 35M+ PubMed Papers (Life Sciences)
- (+) Preprint-Support via arXiv
- (+) Manuelle PDF-Uploads für interne Dokumente
- (+) Einheitliches Client-Interface (erweiterbar)
- (-) PyMuPDF Dependency (~30MB)
- (-) MinIO/S3 Storage erforderlich für PDFs

---

## ADR-014: Sprint 9 - Scoring Enhancements & Paper Notes

### Status
**Implementiert** - 2026-01 (Sprint 9)

### Kontext
Nutzer benötigen besseren Zugang zu komplexen wissenschaftlichen Inhalten und Kollaborationsmöglichkeiten:
1. Vereinfachte Abstracts für nicht-technische Stakeholder
2. Detaillierte Score-Begründungen mit Evidenz
3. Kommentare/Notizen auf Papers mit @mention-Support
4. Bessere Autoren-Visualisierung

### Entscheidung
**AI-Enhanced Paper Understanding + Collaboration Features**

### Implementierung

**1. Simplified Abstract Generator:**
```python
# modules/scoring/prompts/simplified_abstract.jinja2
# Jinja2 Template für LLM-basierte Vereinfachung
# - Ersetzt Fachbegriffe durch einfache Erklärungen
# - Kurze Sätze (max 20 Wörter)
# - Fokus: Was wurde gemacht? Was gefunden? Warum wichtig?
# - Max 150 Wörter

# API: POST /papers/{id}/generate-simplified-abstract
# Frontend: Toggle zwischen Original/Simplified im Paper Detail
```

**2. Enhanced Score Evidence Schema:**
```python
# modules/scoring/schemas.py
class ScoreEvidence(BaseModel):
    factor: str                           # Bewerteter Faktor
    description: str                      # Auswirkung auf Score
    impact: Literal["positive", "negative", "neutral"]
    source: str | None                    # Zitat aus Paper

class DimensionScoreDetail(BaseModel):
    score: float
    confidence: float
    summary: str                          # Kurze Begründung
    key_factors: list[str]                # Hauptfaktoren
    evidence: list[ScoreEvidence]         # Evidenz
    comparison_to_field: str | None       # Vergleich zu ähnlichen Papers

class EnhancedPaperScoreResponse(BaseModel):
    # Detaillierte Scores pro Dimension mit Evidenz
```

**3. Paper Notes/Comments System:**
```python
# modules/papers/notes.py - PaperNote Model
# modules/papers/note_service.py - NoteService mit @mention-Extraktion
# modules/papers/router.py - CRUD Endpoints:
#   GET    /papers/{id}/notes
#   POST   /papers/{id}/notes
#   PUT    /papers/{id}/notes/{note_id}
#   DELETE /papers/{id}/notes/{note_id}

# @mention Format: @{user-uuid}
# Extraktion via Regex, gespeichert in JSON-Array
```

**4. Author Badge Component:**
```typescript
// frontend/src/components/AuthorBadge.tsx
// Zeigt: First Author, Senior Author, Corresponding
// Badges mit unterschiedlichen Farben (blue, purple, green)
```

### Konsequenzen
- (+) Nicht-technische Stakeholder können Papers verstehen
- (+) Transparenz bei AI-Scoring durch Evidenz
- (+) Team-Kollaboration via Notes/Comments
- (+) Bessere Autoren-Visualisierung
- (-) Zusätzlicher LLM-Call für simplified abstract
- (-) Neue Tabelle paper_notes

### Migration
```sql
-- alembic: e5f6g7h8i9j0_sprint9_enhancements
ALTER TABLE papers ADD COLUMN simplified_abstract TEXT;
CREATE TABLE paper_notes (...);
```

---

## ADR-015: Author Intelligence Module (Sprint 10)

### Status
**Akzeptiert** - 2026-01

### Kontext
TTOs und VCs müssen nicht nur Papers evaluieren, sondern auch mit Autoren in Kontakt treten. Bisher gab es keine Möglichkeit, Autoren-Profile anzuzeigen oder Kontakte zu tracken.

### Entscheidung
Wir implementieren ein dediziertes **Authors Module** mit:
1. Author Profile API mit Metriken (h-index, citations, works)
2. Contact Tracking für CRM-ähnliche Funktionalität
3. Author Enrichment aus externen Quellen (OpenAlex, ORCID)
4. Frontend AuthorModal mit Slide-over Panel

### Architektur

**1. Backend Module Structure:**
```
paper_scraper/modules/authors/
├── __init__.py
├── models.py      # AuthorContact mit ContactType, ContactOutcome
├── schemas.py     # AuthorProfile, ContactCreate, EnrichmentResult
├── service.py     # Enrichment, Contact CRUD, Stats
└── router.py      # REST API Endpoints
```

**2. AuthorContact Model:**
```python
class ContactType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    MEETING = "meeting"
    CONFERENCE = "conference"
    OTHER = "other"

class ContactOutcome(str, Enum):
    SUCCESSFUL = "successful"
    NO_RESPONSE = "no_response"
    DECLINED = "declined"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    IN_PROGRESS = "in_progress"

class AuthorContact(Base):
    __tablename__ = "author_contacts"
    id, author_id, organization_id, contacted_by_id
    contact_type, contact_date, subject, notes
    outcome, follow_up_date, paper_id
    created_at, updated_at
```

**3. API Endpoints:**
```
GET    /authors/              # List authors in org
GET    /authors/{id}          # Author profile
GET    /authors/{id}/detail   # Full detail with papers & contacts
POST   /authors/{id}/contacts # Log contact
PATCH  /authors/{id}/contacts/{cid} # Update contact
DELETE /authors/{id}/contacts/{cid} # Delete contact
GET    /authors/{id}/contacts/stats # Contact statistics
POST   /authors/{id}/enrich   # Enrich from OpenAlex/ORCID
```

**4. Frontend AuthorModal:**
```typescript
// components/AuthorModal.tsx - Slide-over panel
// - Author metrics (h-index, citations, works)
// - External links (ORCID, OpenAlex)
// - Contact history with Log Contact form
// - Papers list from library
// - Refresh data from OpenAlex
```

### Konsequenzen
- (+) CRM-Funktionalität für Autoren-Outreach
- (+) Metriken-Tracking für Due Diligence
- (+) Bessere Author-Paper-Verknüpfung
- (-) Neue Tabelle author_contacts
- (-) API-Calls zu OpenAlex für Enrichment

### Migration
```sql
-- alembic: f6g7h8i9j0k1_sprint10_author_contacts
CREATE TYPE contacttype AS ENUM (...);
CREATE TYPE contactoutcome AS ENUM (...);
CREATE TABLE author_contacts (...);
CREATE INDEX ix_author_contacts_org_author ON author_contacts (organization_id, author_id);
```

---

## ADR-016: Search & Discovery Enhancements (Sprint 11)

### Status
**Akzeptiert** - 2026-01

### Kontext
Nutzer führen wiederholt dieselben Suchen durch und verpassen neue relevante Papers. Es fehlt eine Möglichkeit, Suchen zu speichern, zu teilen und Benachrichtigungen für neue Ergebnisse zu erhalten.

### Entscheidung
Wir implementieren drei neue Features:
1. **Saved Searches** - Persistierung von Suchen mit Share-URLs
2. **Alert System** - E-Mail-Benachrichtigungen für neue Suchergebnisse
3. **Paper Classification** - LLM-basierte Kategorisierung (Review, Original Research, etc.)

### Architektur

**1. Saved Searches Module:**
```
paper_scraper/modules/saved_searches/
├── __init__.py
├── models.py      # SavedSearch mit share_token, alert_config
├── schemas.py     # Create, Update, Response schemas
├── service.py     # CRUD, Share-Token-Generierung
└── router.py      # REST API Endpoints
```

**SavedSearch Model:**
```python
class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id, organization_id, created_by_id
    name, description, query, mode, filters
    is_public, share_token (unique)
    alert_enabled, alert_frequency, last_alert_at
    run_count, last_run_at
    created_at, updated_at
```

**2. Alerts Module:**
```
paper_scraper/modules/alerts/
├── __init__.py
├── models.py          # Alert, AlertResult
├── schemas.py         # Request/Response schemas
├── service.py         # CRUD, Alert processing
├── email_service.py   # Resend API integration
└── router.py          # REST API Endpoints
```

**Alert Processing via arq cron:**
```python
# jobs/worker.py
cron_jobs = [
    arq.cron(process_daily_alerts_task, hour=6, minute=0),
    arq.cron(process_weekly_alerts_task, weekday=0, hour=6, minute=0),
]
```

**3. Paper Classification:**
```python
# modules/papers/models.py
class PaperType(str, Enum):
    ORIGINAL_RESEARCH = "original_research"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    METHODOLOGY = "methodology"
    THEORETICAL = "theoretical"
    COMMENTARY = "commentary"
    PREPRINT = "preprint"
    OTHER = "other"

# Paper model erhält: paper_type: PaperType | None
```

**Classification Prompt (Jinja2):**
```
prompts/paper_classification.jinja2
- Classifies based on abstract structure
- Returns JSON: {paper_type, confidence, reasoning, indicators}
```

**4. API Endpoints:**
```
# Saved Searches
GET    /saved-searches/               # List saved searches
POST   /saved-searches/               # Create saved search
GET    /saved-searches/{id}           # Get saved search
PATCH  /saved-searches/{id}           # Update saved search
DELETE /saved-searches/{id}           # Delete saved search
POST   /saved-searches/{id}/share     # Generate share link
DELETE /saved-searches/{id}/share     # Revoke share link
POST   /saved-searches/{id}/run       # Execute saved search
GET    /saved-searches/shared/{token} # Get by share token (public)

# Alerts
GET    /alerts/                       # List alerts
POST   /alerts/                       # Create alert
GET    /alerts/{id}                   # Get alert
PATCH  /alerts/{id}                   # Update alert
DELETE /alerts/{id}                   # Delete alert
GET    /alerts/{id}/results           # Get alert history
POST   /alerts/{id}/test              # Test alert (dry run)
POST   /alerts/{id}/trigger           # Manually trigger alert

# Classification
POST   /scoring/papers/{id}/classify  # Classify single paper
POST   /scoring/classification/batch  # Batch classify
GET    /scoring/classification/unclassified  # List unclassified
```

**5. Email Service (Resend):**
```python
# email_service.py
class EmailService:
    async def send_alert_notification(
        to, alert_name, search_query,
        new_papers_count, papers, view_url
    )
```

**6. Frontend Components:**
```typescript
// pages/SavedSearchesPage.tsx
// hooks/useSavedSearches.ts - React Query hooks
// hooks/useAlerts.ts - React Query hooks
// types/index.ts - SavedSearch, Alert types
```

### Konsequenzen
- (+) Nutzer können Suchen speichern und teilen
- (+) Automatische Benachrichtigungen bei neuen Papers
- (+) Paper-Kategorisierung für besseres Filtern
- (+) Shareable URLs für Collaboration
- (-) Neue DB-Tabellen: saved_searches, alerts, alert_results
- (-) E-Mail-Service-Dependency (Resend)
- (-) Cron-Jobs für Alert-Processing

### Migrations
```sql
-- f6g7h8i9j0k1_add_saved_searches
CREATE TABLE saved_searches (...);
CREATE INDEX ix_saved_searches_share_token UNIQUE;

-- g7h8i9j0k1l2_add_alerts
CREATE TABLE alerts (...);
CREATE TABLE alert_results (...);
CREATE TYPE alertchannel AS ENUM ('EMAIL', 'IN_APP');
CREATE TYPE alertstatus AS ENUM ('PENDING', 'SENT', 'FAILED', 'SKIPPED');

-- h8i9j0k1l2m3_add_paper_classification
ALTER TABLE papers ADD COLUMN paper_type papertype;
CREATE TYPE papertype AS ENUM (...);
```

### Konfiguration
```env
# .env additions
RESEND_API_KEY=re_xxx
EMAIL_FROM_ADDRESS=Paper Scraper <noreply@paperscraper.app>
FRONTEND_URL=http://localhost:3000
```

---

## ADR-017: Analytics & Export Module (Sprint 12)

### Status
**Implementiert** - 2026-01 (Sprint 12)

### Kontext
Nutzer benötigen Einblicke in ihre Paper-Analyse-Aktivitäten und die Möglichkeit, Daten für Berichte und Präsentationen zu exportieren.

### Entscheidung
Wir implementieren ein **Analytics & Export Module** mit:
1. Dashboard-Metriken (Team-Aktivität, Paper-Trends, Scoring-Stats)
2. Multi-Format Export (CSV, PDF, BibTeX)

### Architektur

**1. Analytics Module:**
```python
# modules/analytics/service.py
class AnalyticsService:
    async def get_dashboard_metrics(org_id) -> DashboardMetrics
    async def get_team_activity(org_id) -> TeamActivityResponse
    async def get_paper_analytics(org_id, period) -> PaperAnalyticsResponse

# Response Types:
# - DashboardMetrics: total_papers, scored_papers, avg_score, recent_imports
# - TeamActivityResponse: user_activity, papers_per_user, scoring_per_user
# - PaperAnalyticsResponse: daily_imports, score_distribution, source_breakdown
```

**2. Export Module:**
```python
# modules/export/service.py
class ExportService:
    async def export_csv(papers, options) -> bytes
    async def export_pdf(papers, options) -> bytes
    async def export_bibtex(papers) -> str
```

**3. API Endpoints:**
```
# Analytics
GET /analytics/dashboard    # Dashboard summary
GET /analytics/team         # Team overview
GET /analytics/papers       # Paper trends

# Export
GET /export/csv             # CSV export with filters
GET /export/pdf             # PDF report generation
GET /export/bibtex          # BibTeX bibliography
POST /export/batch          # Batch export multiple formats
```

### Konsequenzen
- (+) Datengetriebene Einblicke für Teams
- (+) Professionelle Berichte via PDF Export
- (+) Standard BibTeX für akademische Integration
- (-) PDF-Generierung erfordert zusätzliche Logik
- (-) Aggregation-Queries können bei großen Datenmengen langsam sein

---

## ADR-018: User Management & Email Infrastructure (Sprint 13)

### Status
**Implementiert** - 2026-01-31 (Sprint 13)

### Kontext
Für Team-Kollaboration benötigen wir:
1. Einladungssystem für neue Team-Mitglieder
2. E-Mail-Verifikation für Account-Sicherheit
3. Passwort-Reset-Funktion
4. Benutzerverwaltung für Admins

### Entscheidung
Wir implementieren ein **vollständiges User Management System** mit Resend als E-Mail-Provider.

### Architektur

**1. Email Service (Resend):**
```python
# modules/email/service.py
class EmailService:
    async def send_verification_email(to, token) -> dict
    async def send_password_reset_email(to, token) -> dict
    async def send_team_invite_email(to, token, inviter_name, org_name) -> dict
    async def send_welcome_email(to, user_name) -> dict

# Professionell gestaltete HTML-E-Mails mit Fallback-Plaintext
```

**2. Security Tokens:**
```python
# core/security.py - Secure Token Generation
def generate_verification_token() -> tuple[str, datetime]  # 24h expiry
def generate_password_reset_token() -> tuple[str, datetime]  # 1h expiry
def generate_invitation_token() -> tuple[str, datetime]  # 7d expiry
def is_token_expired(expires_at: datetime) -> bool
```

**3. User Model Extensions:**
```python
# modules/auth/models.py - Added Fields
class User:
    email_verified: bool = False
    email_verification_token: str | None
    email_verification_token_expires_at: datetime | None
    password_reset_token: str | None
    password_reset_token_expires_at: datetime | None

class TeamInvitation:
    id, organization_id, email, role, token
    created_by_id, status, expires_at
    # status: pending, accepted, declined, expired
```

**4. Auth Router Extensions (14 new endpoints):**
```
# Email Verification
POST /auth/verify-email         # Verify email with token
POST /auth/resend-verification  # Resend verification email

# Password Reset
POST /auth/forgot-password      # Request password reset
POST /auth/reset-password       # Reset with token

# Team Invitations
POST /auth/invite               # Send invitation (admin)
GET  /auth/invitation/{token}   # Get invitation info (public)
POST /auth/accept-invite        # Accept invitation (public)
GET  /auth/invitations          # List pending invitations (admin)
DELETE /auth/invitations/{id}   # Cancel invitation (admin)

# User Management (Admin)
GET  /auth/users                # List organization users
PATCH /auth/users/{id}/role     # Update user role
POST /auth/users/{id}/deactivate   # Deactivate user
POST /auth/users/{id}/reactivate   # Reactivate user
```

**5. Frontend Pages:**
```typescript
// New pages added:
// - ForgotPasswordPage.tsx - Request password reset
// - ResetPasswordPage.tsx - Set new password
// - VerifyEmailPage.tsx - Email verification
// - AcceptInvitePage.tsx - Accept team invitation
// - TeamMembersPage.tsx - User management (admin)

// New UI components:
// - Dialog, DropdownMenu, Select, Table (Shadcn/UI)
```

**6. Configuration:**
```env
# .env additions
RESEND_API_KEY=re_xxx
EMAIL_FROM_ADDRESS=Paper Scraper <noreply@paperscraper.app>
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=1440
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=60
TEAM_INVITATION_TOKEN_EXPIRE_DAYS=7
```

### Migration
```sql
-- i9j0k1l2m3n4_sprint13_user_management

-- Users table extensions
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN email_verification_token_expires_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN password_reset_token_expires_at TIMESTAMPTZ;

-- Index for token lookups
CREATE INDEX ix_users_email_verification_token ON users(email_verification_token);
CREATE INDEX ix_users_password_reset_token ON users(password_reset_token);

-- Team invitations table
CREATE TABLE team_invitations (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'member',
    token VARCHAR(255) UNIQUE NOT NULL,
    created_by_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status invitationstatus NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'declined', 'expired');
```

### Konsequenzen
- (+) Sichere Team-Einladungen mit Token-basierter Authentifizierung
- (+) Professionelle E-Mail-Kommunikation
- (+) Admin-Kontrolle über Benutzerrollen
- (+) Verhindert Email-Enumeration durch konsistente Responses
- (+) 29 Tests für umfassende Coverage
- (-) Externe Abhängigkeit: Resend Email Service
- (-) Token-Management erfordert Expiry-Handling

---

## ADR-019: Server-side Notifications (Sprint 36)

### Status
**Implementiert** - 2026-02

### Kontext
Benachrichtigungen wurden initial nur im Frontend via `localStorage` gespeichert (Sprint 26 Notification Center). Dies hatte Nachteile:
- Keine Synchronisation zwischen Geräten/Browsern
- Verlust bei Browser-Daten-Löschung
- Keine Möglichkeit, Notifications serverseitig zu erstellen (z.B. bei Alert-Triggers)

### Entscheidung
**Server-side Notification Persistence** mit PostgreSQL-backed Notifications-Modul und Frontend-Polling.

### Implementierung

**Backend Module:**
```python
# modules/notifications/models.py
class NotificationType(str, Enum):
    ALERT = "alert"     # Von Alert-System generiert
    BADGE = "badge"     # Von Badge-System generiert
    SYSTEM = "system"   # System-Benachrichtigungen

class Notification(Base):
    __tablename__ = "notifications"
    id, user_id, organization_id, type, title, message,
    is_read, resource_type, resource_id, metadata (JSONB), created_at
```

**API Endpoints:**
```
GET    /notifications/              # Paginated list mit unread_count
GET    /notifications/unread-count  # Nur Badge-Zähler
POST   /notifications/mark-read    # Bulk mark as read
POST   /notifications/mark-all-read
```

**Integration Points:**
- `AlertService._process_single_alert()` erstellt `ALERT`-Notifications
- `check_and_award_badges_task()` erstellt `BADGE`-Notifications

**Frontend Polling:**
```typescript
// useNotifications.ts — TanStack Query mit refetchInterval
const { data } = useQuery({
  queryKey: ['notifications'],
  queryFn: () => notificationsApi.list(limit),
  refetchInterval: 60_000,  // List: alle 60s
})
const { data: unreadData } = useQuery({
  queryKey: ['notifications', 'unread-count'],
  refetchInterval: 30_000,  // Badge: alle 30s
})
```

### Alternativen betrachtet

| Option | Vorteile | Nachteile |
|--------|----------|-----------|
| **WebSocket** | Echtzeit | Komplexität, Connection-Management |
| **Server-Sent Events** | Einfacher als WS | One-directional, Reconnect-Handling |
| **Polling (gewählt)** ✓ | Einfach, robust, stateless | 30-60s Verzögerung, etwas mehr Load |
| **Push Notifications** | Native UX | Browser-Permissions, Service Worker |

### Konsequenzen
- (+) Cross-Device Notification-Sync
- (+) Serverseitige Notification-Erstellung
- (+) Einfache Implementation ohne WebSocket-Infrastruktur
- (+) RBAC-geschützt via `require_permission`
- (-) 30-60s Verzögerung bei neuen Notifications
- (-) Polling-Load (mitigiert durch 30s/60s Intervalle)

---

## ADR-020: Internationalisierung mit react-i18next (Sprint 35)

### Status
**Implementiert** - 2026-02

### Kontext
Die Plattform soll für internationale Teams nutzbar sein. Alle UI-Texte waren bisher hardcoded in Englisch.

### Entscheidung
**react-i18next** als i18n-Framework mit Lazy-loaded Translation-Dateien.

### Implementierung

**Struktur:**
```
frontend/src/locales/
├── en/translation.json    # ~400 Keys
└── de/translation.json    # ~400 Keys
```

**Key-Namespaces:** `common`, `auth`, `dashboard`, `papers`, `projects`, `scoring`, `search`, `groups`, `transfer`, `submissions`, `badges`, `knowledge`, `analytics`, `export`, `alerts`, `notifications`, `settings`, `compliance`, `developer`, `reports`

**Language Selection:** Gespeichert in User-Preferences (`localStorage`), auswählbar in UserSettingsPage.

### Alternativen betrachtet

| Option | Vorteile | Nachteile |
|--------|----------|-----------|
| **react-i18next** ✓ | Standard, Hook-basiert, Lazy-loading | Bundle-Size |
| **react-intl** | ICU Message Format | Komplexere API |
| **lingui** | Extraction-basiert | Kleineres Ecosystem |

### Konsequenzen
- (+) Zwei Sprachen (EN/DE) vollständig unterstützt
- (+) Einfach erweiterbar für weitere Sprachen
- (+) Hook-basiert (`useTranslation`) passt zum React-Pattern
- (-) ~400 Translation-Keys zu pflegen
- (-) Leichte Bundle-Size-Erhöhung

---

## ADR-021: Granulares RBAC mit Permission-Based Access Control (Sprint 22/31)

### Status
**Implementiert** - 2026-02

### Kontext
Das initiale Rollen-System (admin/manager/member/viewer) war zu grobgranular. Bestimmte Operationen (z.B. Scoring, Export, Badge-Management) erforderten feingranulare Berechtigungen.

### Entscheidung
**Permission-based RBAC** mit Rollen-zu-Permission-Mapping in `core/permissions.py`.

### Implementierung

**Permission Enum:**
```python
class Permission(str, Enum):
    PAPERS_READ = "papers:read"
    PAPERS_WRITE = "papers:write"
    PAPERS_DELETE = "papers:delete"
    SCORING_TRIGGER = "scoring:trigger"
    SETTINGS_ADMIN = "settings:admin"
    BADGES_MANAGE = "badges:manage"
    # ... 15+ Permissions
```

**Rollen-Mapping:**
```python
ROLE_PERMISSIONS = {
    "admin": [ALL_PERMISSIONS],
    "manager": [PAPERS_READ, PAPERS_WRITE, SCORING_TRIGGER, ...],
    "member": [PAPERS_READ, PAPERS_WRITE, SCORING_TRIGGER],
    "viewer": [PAPERS_READ],
}
```

**Router-Integration:**
```python
@router.get("/", dependencies=[Depends(require_permission(Permission.PAPERS_READ))])
async def list_papers(...): ...

@router.delete("/{id}", dependencies=[Depends(require_permission(Permission.PAPERS_DELETE))])
async def delete_paper(...): ...
```

### Konsequenzen
- (+) Feingranulare Zugriffskontrolle
- (+) Alle 24 Router-Module geschützt
- (+) Viewer-Rolle kann nur lesen, keine Schreiboperationen
- (+) Admin-Only Operations (User Management, Model Settings, Compliance)
- (-) Mehr Complexity bei Endpoint-Definitionen
- (-) Permission-Matrix muss gepflegt werden

---

## ADR-022: Foundations Ingestion Pipeline Control + Source-specific Async APIs (Sprint 37)

_Updated on 2026-02-10_

### Status
**Implementiert** - 2026-02-10

### Kontext
Die Ingestion war funktional, aber uneinheitlich:
- Async-Ingestion war praktisch OpenAlex-zentriert.
- Es gab keine verlässliche Kopplung zwischen API-Request, Queue-Job und persistiertem Run (`ingest_run_id`).
- Run-Monitoring war über `DEVELOPER_MANAGE` eingeschränkt, obwohl fachliche Nutzer mit Paper-Rechten Ingestion triggern.

Ziel war eine nachvollziehbare, multi-source-fähige Ingestion ohne Plattform-Rewrite.

### Entscheidung
1. **Source-spezifische Async-Endpunkte** statt generischem `/ingest/{source}/async`:
- `/papers/ingest/openalex/async`
- `/papers/ingest/pubmed/async`
- `/papers/ingest/arxiv/async`
- `/papers/ingest/semantic-scholar/async`
2. **Run pre-creation vor Queue-Enqueue**:
- API legt `ingest_runs` mit `status=queued` an und committet vor `enqueue_job`.
- Queue-Job-ID ist deterministisch via `run.id`.
3. **Unified Worker Path**:
- `ingest_source_task` verarbeitet alle unterstützten Quellen über `IngestionPipeline`.
- `ingest_openalex_task` bleibt als Compatibility-Wrapper.
4. **Pipeline execution by existing run**:
- Pipeline akzeptiert `existing_run_id`, validiert `source`, erzwingt `queued -> running`, schreibt Stats/Checkpoint und finalen Status.
5. **RBAC-Anpassung für Run-Read**:
- `GET /ingestion/runs*` nutzt `PAPERS_READ` statt `DEVELOPER_MANAGE`.

### Alternativen betrachtet

| Option | Vorteile | Nachteile |
|--------|----------|-----------|
| **Generischer Async Endpoint** (`/ingest/{source}/async`) | Weniger Routen | Schwächere API-Klarheit, mehr Laufzeitvalidierung |
| **Source-spezifische Endpunkte** ✓ | Klare Contracts, einfache Client-Integration | Mehr Router-Code |
| **Run erst im Worker erzeugen** | API bleibt minimal | Race Conditions, keine direkte Run-ID für Client |
| **Run vor Enqueue erzeugen** ✓ | Verlässliche Nachvollziehbarkeit, deterministische Job-Kopplung | Zusätzlicher DB-Write im Request-Pfad |

### Konsequenzen
- (+) Einheitlicher multi-source Async-Ingestion-Pfad
- (+) `ingest_run_id` direkt im API-Response für Monitoring/Tracing
- (+) Stabilere Fehlerbehandlung: enqueue failure markiert Run explizit als `failed`
- (+) Bessere Nutzerzugänglichkeit von Run-Status via `PAPERS_READ`
- (-) Zusätzliche Komplexität in Papers-Router (Run-Precreation + Error-Handling)
- (-) Erhöhte Bedeutung konsistenter Dokumentation bei Architekturänderungen

### Rollback/Fallback
- Neue Async-Endpunkte sind additiv und können per Router-Flag deaktiviert werden.
- Legacy sync-Ingestion-Endpunkte bleiben unverändert.
- Compatibility-Wrapper (`ingest_openalex_task`) bleibt für bestehende Queue-Producer aktiv.

---

## ADR-023: CI-Enforced Architecture Documentation Gate

_Updated on 2026-02-10_

### Status
**Implementiert** - 2026-02-10

### Kontext
Für Sprint-37 wurde festgelegt, dass Architektur-Änderungen immer mit Updates in
`01_TECHNISCHE_ARCHITEKTUR.md`, `04_ARCHITECTURE_DECISIONS.md` und
`05_IMPLEMENTATION_PLAN.md` geliefert werden müssen.
Ohne technische Durchsetzung war diese Regel jedoch nur prozessual und fehleranfällig.

### Entscheidung
Ein dediziertes CI-Job-Gate (`architecture-docs-gate`) wird in GitHub Actions eingeführt:

1. Der Job führt `.github/scripts/check_arch_docs_gate.sh` aus.
2. Das Script prüft die geänderten Dateien gegen definierte architecture-impacting Pfade.
3. Falls solche Pfade betroffen sind, müssen **alle drei Pflichtdokumente** (`01/04/05`) im gleichen Change enthalten sein.
4. Bei fehlenden Doku-Updates schlägt der CI-Run fehl.

### Alternativen betrachtet

| Option | Vorteile | Nachteile |
|--------|----------|-----------|
| **Manuelle PR-Checklist** | Einfach, keine CI-Komplexität | Nicht verlässlich, leicht übersehbar |
| **CODEOWNERS für Doku-Dateien** | Review-Absicherung | Erzwingt keine tatsächlichen Inhaltsupdates |
| **CI-Gate mit Changed-File-Prüfung** ✓ | Automatisch, nachvollziehbar, skalierbar | Pflege der Pfadliste notwendig |

### Konsequenzen
- (+) Architektur-Dokumentation bleibt synchron zur Implementierung.
- (+) Review-Last sinkt, weil die Mindestanforderung maschinell geprüft wird.
- (-) Zusätzliche CI-Regel kann bei falsch klassifizierten Pfaden blockieren.
- (-) Pfadliste muss bei Modulstrukturänderungen aktualisiert werden.

### Rollback/Fallback
- Temporär kann der `architecture-docs-gate`-Job aus CI entfernt werden.
- Bei False Positives kann die Pfadliste im Script gezielt eingeschränkt werden.

---

## Zusammenfassung der Entscheidungen

| ADR | Entscheidung | Rationale |
|-----|--------------|-----------|
| 001 | Modularer Monolith | Schnelle Iteration, einfaches Debugging |
| 002 | PostgreSQL + pgvector (HNSW) | Eine DB, native JOINs, kosteneffizient |
| 003 | GPT-5 mini (Default) → Multi-Provider | Provider-agnostisch, kosteneffizient |
| 004 | **arq** (async-native) | Native async, einfacher als Celery |
| 005 | **Self-hosted + Custom JWT** | Volle Kontrolle, kein Vendor Lock-in |
| 006 | React + Vite | Bestes DX, größtes Ecosystem |
| 007 | Shared Tables Multi-Tenancy | Einfach, kosteneffizient |
| 008 | Langfuse | Prompt-Management, LLM Observability |
| 009 | URL-Versionierung | Klar, einfach, Standard |
| 010 | Redis Caching | Performance, Kosten-Reduktion |
| 011 | **Production Hardening** | Sentry + Langfuse + slowapi + JSON Logging |
| 012 | **One-Line Pitch Generator** | AI-generierte Business-Pitches für Papers |
| 013 | **Ingestion Expansion** | PubMed, arXiv, PDF Upload Support |
| 014 | **Sprint 9 Enhancements** | Simplified Abstracts, Score Evidence, Notes, Author Badges |
| 015 | **Author Intelligence** | Author Profiles, Contact Tracking, Enrichment |
| 016 | **Search & Discovery** | Saved Searches, Alerts, Paper Classification |
| 017 | **Analytics & Export** | Dashboard Metrics, CSV/PDF/BibTeX Export |
| 018 | **User Management** | Email Verification, Password Reset, Team Invitations |
| 019 | **Server-side Notifications** | PostgreSQL-backed notifications mit Frontend-Polling |
| 020 | **Internationalisierung** | react-i18next mit EN/DE Translation |
| 021 | **Granulares RBAC** | Permission-based Access Control auf allen Routern |
| 022 | **Foundations Ingestion Pipeline** | Multi-Source Async-Ingestion mit pre-created Runs und Run-ID Exposure |
| 023 | **CI Documentation Gate** | Erzwingt 01/04/05-Doku-Updates bei Architektur-Änderungen |

---

## Nächste Schritte

Siehe `05_IMPLEMENTATION_PLAN.md` für den detaillierten Implementierungsplan mit Sprints und Meilensteinen.
