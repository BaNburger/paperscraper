# Stage 1: Local 10x MVP (Execution Spec)

## Stage Goal

Ship a local-first MVP that proves:

**Subscribe -> Ingest -> Score -> Review -> Act**

## Scope Lock

### In

1. Bun end-to-end runtime
2. TanStack Start frontend
3. tRPC internal API
4. BullMQ jobs + Redis
5. OpenAlex-only ingestion
6. Real BYOK scoring
7. Four screens: Feed, Object Detail, Entity Detail, Pipeline Board
8. Manual pipeline card movement

### Out

1. Auth/team/roles
2. Multitenancy/RLS
3. External plugin/webhook system
4. Trigger automation
5. Chat/query interface
6. Trend radar
7. Hybrid vector+BM25 search
8. Admin/compliance modules

## Sprint Plan

## Sprint 1: Foundation

1. Create separate v2 workspace with Bun + pnpm + turbo
2. Add packages/apps for `api`, `web`, `jobs`, `shared`, `db`
3. Implement Stage 1 minimal schema and migrations
4. Wire local Redis + Postgres in docker compose
5. Add health endpoints for API and workers

Exit checks:

1. API and worker processes boot locally
2. DB migrations apply cleanly
3. Redis queue connectivity works

## Sprint 2: Streams + Ingestion

1. Implement `streams.*` API contract
2. Build OpenAlex adapter and normalization
3. Add `stream_runs` tracking and run status transitions
4. Implement dedup upsert into `research_objects`
5. Emit graph resolution jobs per object

Exit checks:

1. Stream trigger creates a run and ingests objects
2. Re-trigger is idempotent (no duplicates)
3. Failed runs are marked with error context

## Sprint 3: Graph + Scoring

1. Implement entity resolution and `object_entities` linking
2. Implement `dimensions.*` APIs
3. Implement scoring worker using BYOK provider key
4. Persist object scores with explanations
5. Implement fold-up into `entity_scores`
6. Implement `scores.backfillDimension`

Exit checks:

1. Same author across papers resolves consistently
2. New and backfilled scores are persisted correctly
3. Entity aggregates update after object scores

## Sprint 4: Pipeline + 4-Screen Frontend

1. Implement `pipelines.*` API contract
2. Implement manual card operations and ordering
3. Build Feed screen with filter/sort
4. Build Object Detail screen
5. Build Entity Detail screen
6. Build Pipeline Board screen with drag-and-drop movement

Exit checks:

1. All four screens render and function on real data
2. Cards can be added and moved between stages
3. UI errors are recoverable (no blank pages)

## Stage 1 Acceptance Tests (Required)

1. Create stream, trigger run, objects appear
2. Create dimension, scores generated for new and existing objects
3. Same author across objects resolves to one entity
4. Entity aggregate changes when object score changes
5. Add object card to pipeline and move across stages
6. End-to-end local flow from empty workspace to first actionable card

## Local Performance Targets (Required)

1. Time to first scored result after manual trigger: `< 60s`
2. Feed query p95 with filter/sort: `< 200ms` DB time
3. Scoring job success rate: `> 95%` excluding provider outages
4. No blank/error-only states in the 4-screen flow

## Delivery Artifacts

1. Working local environment with seed/demo flow
2. Stage 1 E2E script for golden path
3. Readme section for local runbook and known constraints

## Stage Exit Gate

Stage 2 cannot start until all acceptance tests and performance targets above are satisfied.
