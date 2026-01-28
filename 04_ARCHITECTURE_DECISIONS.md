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

---

## Nächste Schritte

Siehe `05_IMPLEMENTATION_PLAN.md` für den detaillierten Implementierungsplan mit Sprints und Meilensteinen.
