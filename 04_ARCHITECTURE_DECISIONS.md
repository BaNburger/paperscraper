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

---

## Nächste Schritte

Siehe `05_IMPLEMENTATION_PLAN.md` für den detaillierten Implementierungsplan mit Sprints und Meilensteinen.
