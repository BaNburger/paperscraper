# PaperScraper v2 — Architecture Blueprint

> Knowledge streaming & action platform for research intelligence

---

## Product Vision

A composable platform that turns research streams into actionable intelligence. Users subscribe to data sources, define their own analytical dimensions, and act on insights through customizable pipelines. Same engine for TTOs, VCs, Corporate Innovation, PE, and Venture Builders — differentiated by configuration, not code.

**Core pipeline:** Ingest → Resolve → Store → Score → Fold → Surface → Act

---

## Architecture Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Language & Runtime | **Full TypeScript + Bun** | One language, shared types, single plugin system. AI calls are HTTP — no need for Python ML stack. |
| 2 | API Paradigm | **tRPC (internal) + REST/OpenAPI (external)** | End-to-end type safety for frontend. Generated OpenAPI for plugin authors and integrations. |
| 3 | Database | **PostgreSQL 16 + pgvector (partitioned) + Redis** | Single DB for structured data, JSONB, and vector search. Partitioned by tenant+time for 10M+ docs/year. Redis for BullMQ queues and pub/sub. |
| 4 | Object Model | **Typed core + JSONB metadata** | All objects share: id, type, title, content, source, embedding, timestamps. Type-specific fields in JSONB metadata column. |
| 5 | Pipeline & Queue | **BullMQ on Redis** | Mature TypeScript job queue. Priority queues, retries, rate limiting, job dependencies. Dashboard for observability. |
| 6 | ORM | **Prisma (+ raw queries for vector/JSONB)** | Great DX for structured CRUD. Raw typed queries for pgvector similarity search and complex JSONB operations. |
| 7 | Frontend | **TanStack Start + Shadcn/UI + TanStack Query** | Best-in-class type-safe routing. Lean framework, not locked to Vercel. Shadcn/UI for clean composable components. |
| 8 | Monorepo | **Turborepo** | Packages: @ps/api, @ps/web, @ps/shared, @ps/jobs, @ps/plugins. Remote caching for CI. |
| 9 | Auth | **Better Auth (self-hosted)** | TypeScript-native, users in own DB, no vendor lock. Workspace-scoped multi-tenancy via middleware. |
| 10 | Deployment | **Vercel + Neon (PG) + Upstash (Redis)** | Serverless PG with pgvector + branching. Serverless Redis with BullMQ support. Near-zero DevOps. |
| 11 | Plugins | **Webhook-based** | Plugins are external HTTP endpoints. Language-agnostic, secure, simple. Built-in plugins use same interface internally. |
| 12 | LLM Layer | **Vercel AI SDK, BYOK** | Multi-provider abstraction with per-call API keys. Encrypted key storage per workspace. Structured output with Zod. |
| 13 | Observability | **Langfuse + Sentry** | Langfuse for LLM traces/costs. Sentry for errors/performance. Both open-source, self-hostable. |
| 14 | Testing | **Vitest + Playwright** | Vitest for unit/integration. Playwright for E2E. Test engines and plugin contracts, not every UI variation. |

---

## Tech Stack Summary

```
┌─────────────────────────────────────────────────────────┐
│  Frontend                                               │
│  TanStack Start · Shadcn/UI · TanStack Query · tRPC    │
├─────────────────────────────────────────────────────────┤
│  API Layer                                              │
│  tRPC (internal) · REST/OpenAPI (external consumers)    │
├────────────┬────────────┬────────────┬──────────────────┤
│  Ingestion │  Graph     │  Scoring   │  Actions         │
│  Engine    │  Engine    │  Engine    │  Engine          │
├────────────┴────────────┴────────────┴──────────────────┤
│  Plugin System (webhook-based)                          │
│  Sources · Processors · Enrichers · Actions             │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL 16 + pgvector │ Redis (BullMQ + pub/sub)    │
│  Neon (managed)           │ Upstash (managed)           │
└─────────────────────────────────────────────────────────┘

Runtime: Bun · ORM: Prisma · Auth: Better Auth
LLM: Vercel AI SDK (BYOK) · Observability: Langfuse + Sentry
Monorepo: Turborepo · CI/CD: Vercel · Tests: Vitest + Playwright
```

---

## Core Data Model

### Entity Relationship

```
Workspace
  ├── Streams (subscriptions to data sources)
  │     └── → Objects (normalized research entities)
  │
  ├── Objects (paper, patent, report, news, ...)
  │     ├── → Entities (via object_entities join)
  │     ├── → Scores (per dimension)
  │     └── → Pipeline Cards
  │
  ├── Entities (person, organization)
  │     ├── → Objects (authored/affiliated)
  │     ├── → Entities (member_of, collaborates_with)
  │     ├── → Scores (aggregated from objects)
  │     └── → Pipeline Cards
  │
  ├── Dimensions (user-defined scoring lenses)
  │     └── → Scores
  │
  ├── Pipelines (user-defined workflow stages)
  │     └── → Pipeline Cards
  │
  └── Views (saved queries/filters)
```

### Schema (~12 core tables)

```sql
-- Tenant
workspaces (
  id            UUID PRIMARY KEY,
  name          TEXT NOT NULL,
  settings      JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ DEFAULT now()
);

users (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  email         TEXT UNIQUE NOT NULL,
  role          TEXT DEFAULT 'member',
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- Ingestion
streams (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  source_type   TEXT NOT NULL,          -- 'openalex', 'arxiv', 'pubmed', 'webhook', ...
  config        JSONB NOT NULL,          -- query, filters, API keys, etc.
  schedule      TEXT,                    -- cron expression
  is_active     BOOLEAN DEFAULT true,
  last_run_at   TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- Knowledge Graph
objects (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  type          TEXT NOT NULL,            -- 'paper', 'patent', 'report', 'news', ...
  external_id   TEXT,                     -- DOI, patent number, etc.
  source        TEXT,                     -- which stream/source
  title         TEXT NOT NULL,
  content       TEXT,                     -- abstract, full text, summary
  metadata      JSONB DEFAULT '{}',       -- type-specific fields
  embedding     vector(1536),
  created_at    TIMESTAMPTZ DEFAULT now(),
  ingested_at   TIMESTAMPTZ DEFAULT now(),

  UNIQUE(workspace_id, external_id)
) PARTITION BY RANGE (created_at);        -- Partitioned for scale

entities (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  type          TEXT NOT NULL,            -- 'person', 'organization'
  name          TEXT NOT NULL,
  metadata      JSONB DEFAULT '{}',       -- orcid, h_index, affiliation, etc.
  embedding     vector(1536),
  created_at    TIMESTAMPTZ DEFAULT now()
);

object_entities (
  object_id     UUID REFERENCES objects,
  entity_id     UUID REFERENCES entities,
  role          TEXT NOT NULL,            -- 'author', 'inventor', 'affiliate', ...
  position      INT,                      -- author position
  PRIMARY KEY (object_id, entity_id, role)
);

entity_relations (
  entity_a_id   UUID REFERENCES entities,
  entity_b_id   UUID REFERENCES entities,
  relation_type TEXT NOT NULL,            -- 'member_of', 'collaborates_with', ...
  metadata      JSONB DEFAULT '{}',
  first_seen    TIMESTAMPTZ DEFAULT now(),
  last_seen     TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (entity_a_id, entity_b_id, relation_type)
);

-- Analysis
dimensions (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  name          TEXT NOT NULL,
  description   TEXT,
  prompt        TEXT NOT NULL,            -- LLM prompt template
  applies_to    TEXT[] DEFAULT '{object}', -- 'object', 'entity', 'organization'
  config        JSONB DEFAULT '{}',       -- scale, output format, etc.
  created_at    TIMESTAMPTZ DEFAULT now()
);

scores (
  id            UUID PRIMARY KEY,
  dimension_id  UUID REFERENCES dimensions,
  target_type   TEXT NOT NULL,            -- 'object', 'entity'
  target_id     UUID NOT NULL,
  value         FLOAT NOT NULL,           -- 0-10 or custom scale
  explanation   TEXT,                     -- LLM reasoning
  metadata      JSONB DEFAULT '{}',
  scored_at     TIMESTAMPTZ DEFAULT now(),

  UNIQUE(dimension_id, target_id)
);

-- Pipelines (Action Layer)
pipelines (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  name          TEXT NOT NULL,
  target_type   TEXT NOT NULL,            -- 'object', 'entity'
  stages        JSONB NOT NULL,           -- [{name, order, color, automations}]
  triggers      JSONB DEFAULT '[]',       -- [{dimension_id, operator, threshold, target_stage}]
  created_at    TIMESTAMPTZ DEFAULT now()
);

pipeline_cards (
  id            UUID PRIMARY KEY,
  pipeline_id   UUID REFERENCES pipelines,
  target_type   TEXT NOT NULL,
  target_id     UUID NOT NULL,
  stage         TEXT NOT NULL,
  position      INT DEFAULT 0,
  metadata      JSONB DEFAULT '{}',       -- notes, assignee, due date, etc.
  entered_at    TIMESTAMPTZ DEFAULT now(),

  UNIQUE(pipeline_id, target_id)
);

-- Views
views (
  id            UUID PRIMARY KEY,
  workspace_id  UUID REFERENCES workspaces,
  name          TEXT NOT NULL,
  target_type   TEXT NOT NULL,
  filters       JSONB DEFAULT '{}',
  sort          JSONB DEFAULT '{}',
  group_by      TEXT,
  layout        TEXT DEFAULT 'table',     -- 'table', 'grid', 'radar', 'timeline'
  is_shared     BOOLEAN DEFAULT false,
  created_at    TIMESTAMPTZ DEFAULT now()
);
```

### Key Indexes

```sql
-- Vector search (HNSW for fast approximate nearest neighbor)
CREATE INDEX idx_objects_embedding ON objects
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_entities_embedding ON entities
  USING hnsw (embedding vector_cosine_ops);

-- Tenant isolation (every query scoped by workspace)
CREATE INDEX idx_objects_workspace ON objects (workspace_id, type, created_at DESC);
CREATE INDEX idx_entities_workspace ON entities (workspace_id, type);
CREATE INDEX idx_scores_target ON scores (target_type, target_id);
CREATE INDEX idx_scores_dimension ON scores (dimension_id, value DESC);

-- JSONB metadata queries
CREATE INDEX idx_objects_metadata ON objects USING gin (metadata);
CREATE INDEX idx_entities_metadata ON entities USING gin (metadata);
```

---

## Five Core Engines

### 1. Ingestion Engine

**Responsibility:** Fetch data from sources, normalize into objects, deduplicate, emit events.

```
Stream config → Source Adapter → Raw Data → Normalizer → Object → Event Bus
```

**Plugin contract (webhook):**
```typescript
// Your system sends:
POST {plugin_url}/fetch
{
  stream_id: string;
  config: Record<string, unknown>;   // user-defined source config
  last_run_at: string | null;        // for incremental fetching
}

// Plugin responds:
{
  objects: Array<{
    external_id: string;
    type: string;
    title: string;
    content?: string;
    metadata: Record<string, unknown>;
    entities?: Array<{
      name: string;
      type: 'person' | 'organization';
      role: string;
      metadata?: Record<string, unknown>;
    }>;
  }>;
  cursor?: string;                    // for pagination
  has_more?: boolean;
}
```

**Built-in adapters:** OpenAlex, arXiv, PubMed, Crossref, DOI resolver, PDF extractor.

### 2. Graph Engine

**Responsibility:** Entity resolution, relationship management, change detection.

```
New Object → Extract Entities → Resolve (deduplicate) → Link → Detect Changes → Emit Signals
```

**Key challenges:**
- Entity resolution: "B. Smith, MIT" = same person across papers?
  - Approach: embedding similarity + metadata matching (ORCID, affiliation, co-author graph)
  - Confidence scoring: auto-merge above threshold, flag for review below
- Relationship inference: co-authorship, affiliation, citation networks
- Change detection: researcher moved institutions, new collaboration, publication rate change

### 3. Scoring Engine

**Responsibility:** Apply user-defined dimensions to objects/entities, fold scores up the graph.

```
Dimension + Target → Hydrate Context → Render Prompt → LLM Call → Parse Score → Store → Fold Up
```

**Context hydration per target:**
- Object: similar objects (vector search), author metrics, related entities
- Entity (person): recent objects, co-authors, affiliation, score history
- Entity (org): member list, aggregate object scores, topic distribution

**Fold-up aggregation:**
```
Object scores → Author aggregate (weighted by recency) → Org aggregate → Topic trend
```

Aggregation is event-driven and incremental:
- New object scored → update author's running average → update org's running average
- Materialized views or computed columns for fast reads

**Scoring is async (BullMQ):**
1. Object ingested → `score:object` job queued per dimension
2. Score stored → `fold:entity` job queued per related entity
3. Entity fold complete → `fold:organization` job queued
4. All folds complete → `check:triggers` job evaluates pipeline rules

### 4. Pipeline Engine

**Responsibility:** User-defined workflow stages, triggers, automation.

```
Trigger condition met → Create/move card → Execute automations → Notify
```

**Trigger types:**
- Score threshold: "any object scoring >7 on 'IP Potential' enters 'Review'"
- Graph event: "new object from tracked entity enters 'Inbox'"
- Time-based: "card in 'Review' for >7 days moves to 'Stale'"
- Manual: user drags card between stages

**Automation actions (per stage):**
- Webhook (plugin system)
- Notification (in-app, email)
- Score additional dimensions
- Assign to team member

### 5. Query Engine

**Responsibility:** Structured queries, natural language queries, aggregations, views.

**Structured queries (Views):**
```typescript
// tRPC query
api.views.query({
  target_type: 'object',
  filters: {
    type: 'paper',
    'metadata.year': { gte: 2025 },
    scores: { dimension: 'novelty', value: { gte: 7 } }
  },
  sort: { field: 'scores.novelty', direction: 'desc' },
  include: ['entities', 'scores'],
  limit: 50
})
```

**Natural language queries (Chat):**
- Backed by the full knowledge graph + scores + relationships
- Uses Vercel AI SDK with tool calling to query the database
- "What's the next big thing in transformer models?" →
  1. Find topic cluster via embedding search
  2. Get high-scoring recent objects in cluster
  3. Identify accelerating entities/orgs
  4. Synthesize with citations to specific objects

---

## Monorepo Structure

```
paper-scraper/
├── apps/
│   ├── api/                    # Bun + tRPC server
│   │   ├── src/
│   │   │   ├── engines/        # 5 core engines
│   │   │   │   ├── ingestion/
│   │   │   │   ├── graph/
│   │   │   │   ├── scoring/
│   │   │   │   ├── pipeline/
│   │   │   │   └── query/
│   │   │   ├── routers/        # tRPC route definitions
│   │   │   ├── middleware/      # auth, tenancy, logging
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── web/                    # TanStack Start frontend
│   │   ├── src/
│   │   │   ├── routes/         # file-based routing
│   │   │   ├── components/     # Shadcn/UI based
│   │   │   ├── hooks/
│   │   │   └── lib/
│   │   └── package.json
│   │
│   └── jobs/                   # BullMQ workers
│       ├── src/
│       │   ├── workers/        # scoring, ingestion, fold-up
│       │   └── index.ts
│       └── package.json
│
├── packages/
│   ├── shared/                 # Types, Zod schemas, constants
│   │   ├── src/
│   │   │   ├── types/          # Shared type definitions
│   │   │   ├── schemas/        # Zod validators
│   │   │   └── constants/
│   │   └── package.json
│   │
│   ├── db/                     # Prisma schema + migrations
│   │   ├── prisma/
│   │   │   └── schema.prisma
│   │   └── package.json
│   │
│   └── plugin-sdk/             # Plugin development kit
│       ├── src/
│       │   ├── types.ts        # Webhook contract types
│       │   └── helpers.ts
│       └── package.json
│
├── plugins/                    # Built-in plugins (same webhook interface)
│   ├── openalex/
│   ├── arxiv/
│   ├── pubmed/
│   └── crossref/
│
├── turbo.json
├── package.json
└── docker-compose.yml          # Local dev: PG + Redis
```

---

## Frontend Pages (Minimal Set)

| Page | Purpose | Layout Reference |
|------|---------|-----------------|
| **Feed** | Chronological stream of new objects from subscriptions | Notion-style list/table with filters |
| **Object Detail** | Full object view with metadata, scores (spider chart), related entities | Twenty CRM record detail |
| **Entity Detail** | Person/org profile: score aggregates, objects, relationships, timeline | CRM contact/company page |
| **Pipeline Board** | Kanban board for a pipeline, cards are objects or entities | Trello/Linear board |
| **Radar** | Trend visualization: topics, scores over time, emerging signals | Custom data viz |
| **Chat** | Natural language query interface backed by knowledge graph | AI assistant panel |
| **Streams** | Manage subscriptions: add sources, configure, monitor | Settings-style list |
| **Dimensions** | Create/edit scoring dimensions: name, prompt, scale | Form + preview |
| **Settings** | Workspace config, API keys (BYOK), team, billing | Standard settings |

**Total: ~9 pages.** Current PaperScraper has 28.

---

## Event Flow Example

```
1. Stream "ML papers from TUM" triggers scheduled fetch
2. Ingestion Engine calls OpenAlex adapter → returns 12 new papers
3. Each paper normalized → stored as object → embedding generated
4. Graph Engine resolves authors → links to existing entities → detects new collaboration
5. Scoring Engine queues jobs: 12 papers × 3 user-defined dimensions = 36 scoring jobs
6. BullMQ workers process scores in parallel (Vercel AI SDK + user's BYOK key)
7. Scores stored → fold-up jobs aggregate to authors → then to research groups
8. Trigger check: 2 papers scored >8 on "IP Potential"
9. Pipeline Engine creates cards in "TTO Licensing" pipeline at "Flagged" stage
10. Notification sent to workspace members
11. Frontend updates in real-time via pub/sub
```

**Total latency:** ~10-30 seconds from fetch to fully scored and pipeline-placed.

---

## Vector Search Scaling Strategy

| Scale | Approach | Expected Latency |
|-------|----------|-----------------|
| <1M vectors | Single pgvector table, HNSW index | <50ms |
| 1-10M vectors | Partitioned by workspace + time range | <100ms |
| 10-50M vectors | Partition pruning + partial indexes | <200ms |
| 50M+ vectors | Swap to Qdrant (behind abstract interface) | <50ms |

**Abstract interface (implemented day one):**
```typescript
interface VectorStore {
  upsert(id: string, embedding: number[], metadata: Record<string, unknown>): Promise<void>;
  search(query: number[], filter: VectorFilter, limit: number): Promise<VectorResult[]>;
  delete(id: string): Promise<void>;
}
```

---

## BYOK (Bring Your Own Key) Flow

```
1. User adds API key in Settings → encrypted with workspace-specific key → stored in DB
2. Scoring job picks up workspace config → decrypts key at runtime
3. Vercel AI SDK receives key as parameter → calls user's provider account
4. Langfuse traces the call (cost, latency, tokens) → attributed to workspace
5. Usage dashboard shows the user their LLM costs
```

**Supported providers (via Vercel AI SDK):** OpenAI, Anthropic, Google, Mistral, Groq, Together, Fireworks.

---

## Plugin System

### Contract

Every plugin implements one or more of:

```typescript
// Source plugin (ingestion)
POST /fetch    { config, last_run_at } → { objects[], cursor?, has_more? }

// Processor plugin (scoring/enrichment)
POST /process  { object, context, dimension } → { value: number, explanation: string }

// Action plugin (pipeline automation)
POST /execute  { card, pipeline, stage, trigger } → { success: boolean, result? }
```

### Built-in vs External

Built-in plugins (OpenAlex, arXiv, etc.) use the exact same interface but are co-located in the monorepo. This means:
- Any built-in plugin can be extracted to external without code changes
- Any external plugin pattern can be promoted to built-in
- Testing is uniform: mock the webhook, test the response

### Plugin Registry

Workspaces register plugins by URL + auth:
```typescript
{
  name: "My Custom Source",
  type: "source",
  url: "https://my-plugin.example.com",
  auth: { type: "bearer", token: "encrypted_token" },
  config_schema: { /* JSON Schema for user configuration */ }
}
```

---

## Security Model

- **Workspace isolation:** Every DB query scoped by workspace_id (middleware-enforced)
- **Auth:** Better Auth with session tokens, MFA optional
- **API keys (BYOK):** AES-256 encrypted at rest, decrypted only in worker memory
- **Plugin webhooks:** HMAC-signed payloads, configurable timeout
- **Data residency:** Neon PG regions (EU/US selectable per workspace)
- **Rate limiting:** Per-workspace, per-endpoint (Upstash rate limiter)

---

## Migration Path from v1

This is a ground-up rebuild, not a migration. However:
- Export v1 papers → import as v2 objects (type: 'paper')
- Export v1 scores → import as v2 scores (map 6 dimensions to user-defined)
- Export v1 pipeline states → import as v2 pipeline cards
- Users re-create their specific dimensions, streams, and pipeline configs

---

*Last updated: 2026-02-20*
*Status: Architecture blueprint — pending implementation planning*
