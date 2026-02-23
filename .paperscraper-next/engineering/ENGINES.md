# Engines Design (Stage 1 MVP + Stage 2 Extensions)

## Core Engine Contract

Stage 1 uses five lean engines aligned to the 10x loop.

1. Ingestion Engine
2. Graph Engine
3. Scoring Engine
4. Pipeline Engine
5. Query Engine (feed/detail queries only)

Engines communicate through BullMQ jobs and persisted database state.

## Stage 1 Event Chain

```
stream.triggered
  -> ingest.stream
    -> object.created
      -> graph.resolve
        -> object.ready
          -> scoring.scoreObject (for each active dimension)
            -> object.score.created
              -> scoring.foldEntity
                -> entity.score.updated
```

No trigger automation jobs in Stage 1.

## Stage 1 Engine Details

## 1) Ingestion Engine

### Responsibility

1. Manage stream lifecycle
2. Fetch from OpenAlex only
3. Normalize and deduplicate objects
4. Emit graph-resolution jobs

### Required Interfaces

1. `streams.list/create/update/delete/trigger`
2. Job handler: `ingest.stream`

### Key Rules

1. OpenAlex is the only supported adapter in Stage 1.
2. Every run is recorded in `stream_runs` with status and stats.
3. Dedup is idempotent via `(externalId, source)` uniqueness.

## 2) Graph Engine

### Responsibility

1. Resolve entities from normalized object payloads
2. Link object/entity relationships
3. Produce stable entity identities across ingestions

### Resolution Order

1. Canonical ID exact match (`orcid`, `openAlexId`)
2. Fuzzy name + affiliation confidence
3. Create new entity when below threshold

### Key Rules

1. Favor false negatives over false positives for merges.
2. Relationship inference is limited to author-affiliation/co-author basics in Stage 1.

## 3) Scoring Engine

### Responsibility

1. Manage dimensions
2. Score objects using BYOK LLM calls
3. Aggregate entity-level scores

### Required Interfaces

1. `dimensions.list/create/update/delete`
2. `scores.backfillDimension`

### Scoring Contract

1. Real LLM scoring only (no fake baseline path)
2. Structured output validation (value + explanation)
3. Failed score writes do not crash pipeline; they are logged and surfaced

### Fold-up Contract

1. Triggered after each `object.score.created`
2. Recompute aggregate per `(entityId, dimensionId)`
3. Store aggregation metadata (paper_count, method)

## 4) Pipeline Engine

### Responsibility

1. Manage pipelines and stages
2. Add/move/remove object cards manually
3. Serve board view grouped by stage

### Required Interfaces

1. `pipelines.list/create/update/delete/getBoard`
2. `pipelines.addCard/moveCard/removeCard`

### Key Rules

1. Manual-only movement in Stage 1.
2. No automatic card creation from triggers.

## 5) Query Engine (Stage 1)

### Responsibility

1. Feed retrieval
2. Object detail hydration
3. Entity detail hydration
4. Fast filter/sort logic

### Key Rules

1. No hybrid semantic query path in Stage 1.
2. Query scope limited to screens needed by the 4-page surface.

## Error Handling Contract (All Stage 1 Engines)

Use clear recoverability categories:

1. Retryable failures
   - transient API/network errors
   - Redis or DB connection blips
2. Permanent failures
   - invalid BYOK key
   - invalid scoring schema output after bounded retries
   - malformed OpenAlex payload

Minimum behavior:

1. BullMQ retries with exponential backoff
2. Dead-letter after retry exhaustion
3. Persist run/job failure state for operator visibility
4. UI must show non-blocking errors instead of blank states

## Stage 2 Extensions (Deferred)

1. Trigger automation engine path (`entity.score.updated -> trigger.evaluate`)
2. Hybrid search retrieval path (text + vector)
3. Plugin invocation path (source/processor/action)
4. Auth-aware, tenant-aware engine guards
5. Audit and compliance event sinks

## Non-Negotiable Guardrails

1. Stage 1 engine code must not depend on Stage 2-only modules.
2. Stage 2 features must be feature-flagged behind explicit wave milestones.
3. Any new engine behavior must cite workflow impact before implementation.
