# Paper Scraper - Best Practice Technische Architektur

## Executive Summary

Diese Architektur definiert einen pragmatischen, inkrementellen Ansatz zur Entwicklung von Paper Scraper. Statt einer überdimensionierten Enterprise-Architektur fokussieren wir uns auf eine **MVP-first, Scale-later** Strategie, die mit Claude Code effizient implementiert werden kann.

---

## 1. Architekturprinzipien

### 1.1 Leitprinzipien

| Prinzip | Beschreibung | Rationale |
|---------|--------------|-----------|
| **Monolith-First** | Start mit modularem Monolith, kein Microservices-Overhead | Schnelle Iteration, einfaches Debugging, geringere Komplexität |
| **API-First Design** | Alle Funktionen als REST/GraphQL APIs | Ermöglicht spätere Aufteilung, Frontend-Unabhängigkeit |
| **Composable AI** | LLM-Aufrufe als austauschbare Module | Provider-Wechsel (OpenAI→Claude→lokale Modelle) ohne Refactoring |
| **Data Lake Architecture** | Rohdaten immer erhalten, verarbeitete Daten separat | Ermöglicht Neuberechnung bei Modell-Updates |
| **Feature Flags** | Alle neuen Features togglebar | A/B-Testing, schrittweises Rollout |

### 1.2 Technology Stack Entscheidungen

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  React 18 + TypeScript + Vite + TailwindCSS + Shadcn/UI         │
│  (Alternativ: Next.js für SSR wenn SEO relevant)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                 │
│  FastAPI (Python 3.11+) + Pydantic v2 + async/await             │
│  OpenAPI auto-generation, Type Safety, High Performance         │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   CORE MODULES  │  │   AI PIPELINE   │  │  BACKGROUND     │
│                 │  │                 │  │  JOBS           │
│  • Auth/Users   │  │  • Paper Parser │  │  • arq (async)  │
│  • Papers       │  │  • Scoring      │  │  • Ingestion    │
│  • Projects     │  │  • Embeddings   │  │  • Alerts       │
│  • KanBan       │  │  • RAG          │  │  • Reports      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│  PostgreSQL (Primary) + pgvector + Redis (Cache/Queue)          │
│  S3-kompatibel (MinIO/Cloudflare R2) für PDFs                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Domänenmodell

### 2.1 Core Entities

```
┌────────────────────────────────────────────────────────────────┐
│                        ORGANIZATION                             │
│  id, name, type (university|vc|corporate), subscription_tier   │
└────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│      USER       │  │    PROJECT      │  │   DATA SOURCE   │
│                 │  │                 │  │                 │
│  email, role    │  │  name, filters  │  │  type (pubmed,  │
│  preferences    │  │  scoring_config │  │  arxiv, custom) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PAPER                                    │
│  doi, title, abstract, authors[], affiliations[], pub_date      │
│  source_url, full_text_url, pdf_path, raw_metadata{}            │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PAPER_SCORE   │  │  PAPER_STATUS   │  │    AUTHOR       │
│                 │  │                 │  │                 │
│  novelty: 0-10  │  │  stage (kanban) │  │  orcid, h_index │
│  ip_potential   │  │  assigned_to    │  │  affiliations[] │
│  marketability  │  │  rejection_rsn  │  │  contact_email  │
│  feasibility    │  │  notes[]        │  │  last_contact   │
│  commercializ.  │  │  last_action_at │  │  profile_data{} │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 Scoring-Dimensionen (Details)

```python
class PaperScore(BaseModel):
    """5-Dimensionales Scoring nach Business Plan"""

    # Dimension 1: Technologische Neuheit
    novelty: float  # 0-10
    novelty_explanation: str
    novelty_evidence: list[str]  # Zitate aus Paper

    # Dimension 2: IP-Potential (Patentierbarkeit)
    ip_potential: float  # 0-10
    ip_prior_art_found: bool
    ip_freedom_to_operate: float  # 0-10
    ip_white_spaces: list[str]  # Identifizierte Lücken

    # Dimension 3: Marktrelevanz
    marketability: float  # 0-10
    market_size_estimate: str  # "€10M-50M", etc.
    target_industries: list[str]
    market_signals: list[str]  # News, Trends

    # Dimension 4: Umsetzbarkeit
    feasibility: float  # 0-10
    trl_level: int  # 1-9 (Technology Readiness Level)
    time_to_market_years: float
    estimated_dev_cost: str

    # Dimension 5: Kommerzialisierungspotential
    commercialization: float  # 0-10
    recommended_path: str  # "patent", "license", "spinoff"
    entry_barriers: list[str]

    # Meta
    overall_score: float  # Gewichteter Durchschnitt
    confidence: float  # 0-1, wie sicher ist die Bewertung
    scored_at: datetime
    model_version: str
```

---

## 2.3 External Data Sources (Open APIs)

Die Plattform nutzt primär offene APIs für Daten-Ingestion:

| API | Zweck | Authentifizierung | Rate Limits |
|-----|-------|------------------|-------------|
| **OpenAlex** | Paper/Autor-Metadaten (primär) | Email (polite pool) | 100k/Tag |
| **EPO OPS** | Patentdaten, Prior Art | OAuth 2.0 (Free tier: 4GB/Woche) | 5 req/s |
| **arXiv** | Preprints (STEM) | Keine | 1 req/3s |
| **PubMed/NCBI** | Biomedizinische Literatur | API Key (optional) | 3 req/s (ohne Key) |
| **Crossref** | DOI-Auflösung | Email (polite pool) | Polite: 50 req/s |
| **Semantic Scholar** | Zitationen, Influence | API Key (optional) | 100 req/s |

### Konfiguration

```python
# core/config.py - External API Settings
OPENALEX_EMAIL: str = "noreply@example.com"
OPENALEX_BASE_URL: str = "https://api.openalex.org"

EPO_OPS_KEY: str | None = None
EPO_OPS_SECRET: SecretStr | None = None
EPO_OPS_BASE_URL: str = "https://ops.epo.org/3.2"

ARXIV_BASE_URL: str = "http://export.arxiv.org/api"

PUBMED_API_KEY: str | None = None
PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

CROSSREF_EMAIL: str = "noreply@example.com"
CROSSREF_BASE_URL: str = "https://api.crossref.org"

SEMANTIC_SCHOLAR_API_KEY: str | None = None
SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
```

### Vector Data Strategy

| Datentyp | Dimension | Speicher | Verwendung |
|----------|-----------|----------|------------|
| Paper Embeddings | 1536d (OpenAI) | pgvector | Semantische Suche, Ähnlichkeit |
| Author Embeddings | 768d | pgvector | Expertensuche, Kollaboration |
| Patent Claims | 1536d | pgvector | Prior Art Detection |
| Query Embeddings | Variabel | In-Memory/Redis | Echtzeit-Suche |

---

## 3. Modulare Systemarchitektur

### 3.1 Backend Module

```
paper_scraper/
├── core/                      # Shared utilities
│   ├── config.py             # Pydantic Settings
│   ├── database.py           # SQLAlchemy async session
│   ├── security.py           # Auth, JWT, API Keys
│   └── exceptions.py         # Custom exceptions
│
├── modules/
│   ├── auth/                 # Authentication & Authorization
│   │   ├── models.py         # User, Organization, Role
│   │   ├── schemas.py        # Pydantic DTOs
│   │   ├── service.py        # Business logic
│   │   └── router.py         # FastAPI endpoints
│   │
│   ├── papers/               # Paper Management
│   │   ├── models.py         # Paper, Author, PaperScore
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── router.py
│   │   └── ingestion/        # Data ingestion sub-module
│   │       ├── sources/      # PubMed, arXiv, Semantic Scholar
│   │       ├── parsers/      # PDF, XML, JSON parsers
│   │       └── pipeline.py   # Orchestration
│   │
│   ├── scoring/              # AI Scoring Pipeline
│   │   ├── dimensions/       # Ein Modul pro Dimension
│   │   │   ├── novelty.py
│   │   │   ├── ip_potential.py
│   │   │   ├── marketability.py
│   │   │   ├── feasibility.py
│   │   │   └── commercialization.py
│   │   ├── prompts/          # Prompt Templates (Langfuse-kompatibel)
│   │   ├── llm_client.py     # Abstraction über OpenAI/Claude/etc.
│   │   └── orchestrator.py   # Scoring Pipeline
│   │
│   ├── projects/             # Project/Pipeline Management
│   │   ├── models.py         # Project, Stage, PaperStatus
│   │   ├── kanban.py         # KanBan-specific logic
│   │   └── router.py
│   │
│   ├── search/               # Search & Discovery
│   │   ├── vector_store.py   # pgvector operations
│   │   ├── semantic.py       # Embedding-based search
│   │   ├── filters.py        # Structured filtering
│   │   └── router.py
│   │
│   └── notifications/        # Alerts & Notifications
│       ├── models.py
│       ├── email.py
│       ├── slack.py
│       └── scheduler.py
│
├── jobs/                     # Background Jobs (arq - async-native)
│   ├── worker.py             # arq worker settings
│   ├── ingestion.py          # Scheduled paper ingestion
│   ├── scoring.py            # Batch scoring
│   ├── alerts.py             # Alert processing
│   └── reports.py            # Report generation
│
└── api/                      # API Layer
    ├── main.py               # FastAPI app
    ├── dependencies.py       # Dependency injection
    ├── middleware.py         # Logging, CORS, etc.
    └── v1/                   # API version
        └── router.py         # All route aggregation
```

### 3.2 AI/LLM Abstraction Layer

```python
# scoring/llm_client.py

from abc import ABC, abstractmethod
from typing import AsyncIterator

class LLMClient(ABC):
    """Abstract base for LLM providers"""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str = None
    ) -> AsyncIterator[str]:
        pass

class OpenAIClient(LLMClient):
    """OpenAI implementation (default: GPT-5 mini)"""

    def __init__(self, model: str = None):
        self.client = AsyncOpenAI()
        self.model = model or settings.LLM_MODEL  # Default: gpt-5-mini

    async def complete(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": kwargs.get("system", "")},
                {"role": "user", "content": prompt}
            ],
            temperature=kwargs.get("temperature", settings.LLM_TEMPERATURE),
            max_tokens=kwargs.get("max_tokens", settings.LLM_MAX_TOKENS)
        )
        return response.choices[0].message.content

class AnthropicClient(LLMClient):
    """Anthropic Claude implementation"""
    # Similar implementation

class AzureOpenAIClient(LLMClient):
    """Azure OpenAI implementation"""
    # Similar implementation

class LocalOllamaClient(LLMClient):
    """Local Ollama for development/testing"""
    # Similar implementation

# Factory - provider-agnostic with configurable default
def get_llm_client(provider: str = None, model: str = None) -> LLMClient:
    provider = provider or settings.LLM_PROVIDER
    clients = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "azure": AzureOpenAIClient,
        "ollama": LocalOllamaClient
    }
    return clients[provider](model=model)
```

---

## 4. Datenbank-Schema

### 4.1 PostgreSQL + pgvector

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Fuzzy text search

-- Organizations & Users
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('university', 'vc', 'corporate', 'research_institute')),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Papers Core
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doi VARCHAR(255) UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    publication_date DATE,
    source VARCHAR(50),  -- 'pubmed', 'arxiv', 'semantic_scholar', etc.
    source_id VARCHAR(255),  -- Original ID from source
    source_url TEXT,
    pdf_url TEXT,
    pdf_path TEXT,  -- S3 path
    full_text TEXT,
    raw_metadata JSONB,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for better performance (auto-tuning, no retraining needed)
CREATE INDEX idx_papers_embedding ON papers USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_papers_title_trgm ON papers USING gin (title gin_trgm_ops);
CREATE INDEX idx_papers_abstract_trgm ON papers USING gin (abstract gin_trgm_ops);
CREATE INDEX idx_papers_source ON papers (source, source_id);
CREATE INDEX idx_papers_doi ON papers (doi) WHERE doi IS NOT NULL;

-- Authors
CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orcid VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255),  -- For matching
    email VARCHAR(255),
    affiliations JSONB DEFAULT '[]',
    h_index INTEGER,
    citation_count INTEGER,
    profile_data JSONB DEFAULT '{}',
    last_contact_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paper_authors (
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    author_id UUID REFERENCES authors(id) ON DELETE CASCADE,
    position INTEGER,  -- 1 = first author, -1 = last author
    is_corresponding BOOLEAN DEFAULT false,
    PRIMARY KEY (paper_id, author_id)
);

-- Scoring
CREATE TABLE paper_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id),  -- Custom scoring per org

    -- 5 Dimensions
    novelty DECIMAL(3,1),
    novelty_explanation TEXT,
    novelty_evidence JSONB,

    ip_potential DECIMAL(3,1),
    ip_prior_art_found BOOLEAN,
    ip_freedom_to_operate DECIMAL(3,1),
    ip_white_spaces JSONB,

    marketability DECIMAL(3,1),
    market_size_estimate VARCHAR(50),
    target_industries JSONB,
    market_signals JSONB,

    feasibility DECIMAL(3,1),
    trl_level INTEGER,
    time_to_market_years DECIMAL(3,1),
    estimated_dev_cost VARCHAR(50),

    commercialization DECIMAL(3,1),
    recommended_path VARCHAR(50),
    entry_barriers JSONB,

    -- Aggregates
    overall_score DECIMAL(3,1),
    confidence DECIMAL(3,2),

    -- Meta
    model_version VARCHAR(50),
    prompt_version VARCHAR(50),
    raw_llm_response JSONB,  -- For debugging
    scored_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (paper_id, organization_id)
);

-- Projects & KanBan
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filters JSONB DEFAULT '{}',  -- Saved search filters
    scoring_weights JSONB DEFAULT '{}',  -- Custom dimension weights
    stages JSONB DEFAULT '["inbox", "screening", "evaluation", "outreach", "archived"]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paper_project_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES papers(id),
    project_id UUID REFERENCES projects(id),
    stage VARCHAR(50) DEFAULT 'inbox',
    assigned_to UUID REFERENCES users(id),
    priority INTEGER DEFAULT 0,
    rejection_reason TEXT,
    notes JSONB DEFAULT '[]',
    last_action_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (paper_id, project_id)
);

-- Audit & Activity
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    entity_type VARCHAR(50),
    entity_id UUID,
    action VARCHAR(50),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_log_entity ON activity_log (entity_type, entity_id);
CREATE INDEX idx_activity_log_user ON activity_log (user_id, created_at DESC);
```

---

## 5. API Design

### 5.1 RESTful Endpoints

```yaml
# OpenAPI Specification (Auszug)

openapi: 3.0.3
info:
  title: Paper Scraper API
  version: 1.0.0

paths:
  # Papers
  /api/v1/papers:
    get:
      summary: List papers with filtering
      parameters:
        - name: q
          in: query
          description: Full-text search
        - name: source
          in: query
          description: Filter by source (pubmed, arxiv, etc.)
        - name: min_score
          in: query
          description: Minimum overall score
        - name: dimensions
          in: query
          description: Filter by specific dimension scores (JSON)
        - name: date_from
          in: query
        - name: date_to
          in: query
        - name: limit
          in: query
          default: 20
        - name: offset
          in: query
          default: 0
      responses:
        200:
          description: Paginated paper list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaperListResponse'

    post:
      summary: Ingest papers from URL or DOI
      requestBody:
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/IngestByDOI'
                - $ref: '#/components/schemas/IngestByURL'
                - $ref: '#/components/schemas/IngestByPDF'

  /api/v1/papers/{paper_id}:
    get:
      summary: Get paper details with scores

  /api/v1/papers/{paper_id}/score:
    post:
      summary: Trigger scoring for a paper
      requestBody:
        content:
          application/json:
            schema:
              properties:
                dimensions:
                  type: array
                  items:
                    type: string
                    enum: [novelty, ip_potential, marketability, feasibility, commercialization]
                force_rescore:
                  type: boolean
                  default: false

  /api/v1/papers/search/semantic:
    post:
      summary: Semantic similarity search
      requestBody:
        content:
          application/json:
            schema:
              properties:
                query:
                  type: string
                  description: Natural language query
                top_k:
                  type: integer
                  default: 10

  # Projects & KanBan
  /api/v1/projects:
    get:
      summary: List projects
    post:
      summary: Create project

  /api/v1/projects/{project_id}/papers:
    get:
      summary: Get papers in project (KanBan view)
      parameters:
        - name: stage
          in: query
    post:
      summary: Add paper to project

  /api/v1/projects/{project_id}/papers/{paper_id}/move:
    post:
      summary: Move paper to different stage
      requestBody:
        content:
          application/json:
            schema:
              properties:
                to_stage:
                  type: string
                rejection_reason:
                  type: string
                  description: Required when moving to rejected

  # Analytics
  /api/v1/analytics/dashboard:
    get:
      summary: Dashboard metrics for organization

  /api/v1/analytics/trends:
    get:
      summary: Research trend analysis

components:
  schemas:
    Paper:
      type: object
      properties:
        id:
          type: string
          format: uuid
        doi:
          type: string
        title:
          type: string
        abstract:
          type: string
        authors:
          type: array
          items:
            $ref: '#/components/schemas/Author'
        scores:
          $ref: '#/components/schemas/PaperScore'
        # ... etc

    PaperScore:
      type: object
      properties:
        overall_score:
          type: number
        novelty:
          type: number
        ip_potential:
          type: number
        marketability:
          type: number
        feasibility:
          type: number
        commercialization:
          type: number
        confidence:
          type: number
        one_line_pitch:
          type: string
        simplified_abstract:
          type: string
```

---

## 6. Deployment & Infrastructure

### 6.1 Container-basiertes Deployment

```yaml
# docker-compose.yml (Development)

version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/paperscraper
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - S3_ENDPOINT=http://minio:9000
    depends_on:
      - db
      - redis
      - minio
    volumes:
      - ./paper_scraper:/app/paper_scraper
    command: uvicorn paper_scraper.api.main:app --host 0.0.0.0 --reload

  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/paperscraper
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    command: arq paper_scraper.jobs.worker.WorkerSettings

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=paperscraper
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    environment:
      - MINIO_ROOT_USER=minio
      - MINIO_ROOT_PASSWORD=minio123
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
  minio_data:
```

### 6.2 Production Infrastructure (Cloud-agnostic)

```
┌─────────────────────────────────────────────────────────────────┐
│                      CDN (Cloudflare)                           │
│                   Static Assets + Edge Caching                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Load Balancer (Traefik/nginx)                 │
│                     SSL Termination, Rate Limiting              │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   API Server    │  │   API Server    │  │   API Server    │
│   (Container)   │  │   (Container)   │  │   (Container)   │
│   Auto-scaling  │  │   Auto-scaling  │  │   Auto-scaling  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Redis       │  │  Object Storage │
│   (Managed)     │  │   (Managed)     │  │  (S3/R2/MinIO)  │
│   + pgvector    │  │   Cache+Queue   │  │   PDFs, Exports │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     arq Workers (Auto-scaling)                  │
│              Ingestion | Scoring | Alerts | Reports             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability                   │
│   Grafana + Prometheus | Sentry | Langfuse (LLM Monitoring)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Sicherheit & Compliance

### 7.1 Security Layers

| Layer | Implementation | Details |
|-------|----------------|---------|
| **Authentication** | JWT + API Keys | Short-lived JWTs (15min), Refresh Tokens (7d) |
| **Authorization** | RBAC | Roles: admin, manager, member, viewer |
| **API Security** | Rate Limiting | 100 req/min (free), 1000 req/min (paid) |
| **Data Encryption** | TLS 1.3 + AES-256 | In transit + at rest |
| **Audit Logging** | Activity Log | All data mutations tracked |
| **GDPR Compliance** | Data Export/Delete | User kann alle Daten exportieren/löschen |

### 7.2 Multi-Tenancy

```python
# Tenant Isolation via Row-Level Security

class TenantMiddleware:
    """Inject organization_id into all queries"""

    async def __call__(self, request: Request, call_next):
        # Extract org from JWT
        org_id = get_org_from_token(request)

        # Set in context for SQLAlchemy
        request.state.organization_id = org_id

        response = await call_next(request)
        return response

# In queries
async def get_papers(
    db: AsyncSession,
    org_id: UUID,
    filters: PaperFilters
) -> list[Paper]:
    query = select(Paper).where(
        Paper.organization_id == org_id  # Automatic tenant filter
    )
    # ... add filters
```

---

## 8. Entscheidungsmatrix: Build vs. Buy

| Komponente | Entscheidung | Rationale |
|------------|--------------|-----------|
| **Database** | Self-hosted PostgreSQL + pgvector | Volle Kontrolle, kosteneffizient, keine Vendor-Abhängigkeit |
| **Auth** | Custom JWT Implementation | Kein Vendor Lock-in, vollständige Kontrolle |
| **Job Queue** | arq (async-native) | Async/await nativ, einfacher als Celery für async codebase |
| **LLM** | GPT-5 mini (Default) → Multi-Provider | Provider-agnostisch, kosteneffizient, Abstraktion erlaubt Wechsel |
| **Embeddings** | text-embedding-3-small | Gute Qualität, kosteneffizient |
| **Data Sources** | Open APIs (OpenAlex, EPO OPS, arXiv, etc.) | Kostenlos, umfassende Abdeckung |
| **PDF Parsing** | PyMuPDF + eigene Pipeline | Kontrolle über Qualität, kein Vendor Lock-in |
| **Email** | Resend oder Postmark | Zuverlässig, gute DX |
| **Search** | pgvector (HNSW) + pg_trgm | Kein extra Service, skaliert bis 10M+ Dokumente |
| **Monitoring** | Sentry + Langfuse | Error Tracking + LLM Observability |
| **CI/CD** | GitHub Actions | Kostenlos, gut integriert |

---

## 9. Nächste Schritte

Siehe `02_USER_STORIES.md` für die priorisierten User Stories und `03_CLAUDE_CODE_GUIDE.md` für die Implementierungsanleitung mit Claude Code.
