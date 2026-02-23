# Stage 1 MVP Scope (Local 10x Loop)

## Stage 1 Goal

Prove the core value proposition with the smallest possible product surface:

**Subscribe -> Ingest -> Score -> Review -> Act**

This stage is local-first and optimized for speed of validation, not enterprise completeness.

## Stage 1 Decisions (Locked)

1. Four screens only: Feed, Object Detail, Entity Detail, Pipeline Board
2. Single source only: OpenAlex
3. Real scoring only: BYOK LLM calls (no mock-first strategy)
4. Manual pipeline only: no trigger automation
5. Single-workspace dev mode: no multi-user auth in Stage 1
6. Separate v2 workspace: no in-place migration in current app

## In Scope

### Workflow

1. Create stream
2. Trigger ingestion
3. Ingest and deduplicate OpenAlex objects
4. Resolve and link entities (authors, organizations)
5. Score objects on user-defined dimensions
6. Fold scores to entities
7. Add/move objects in a manual pipeline board

### Product Surface (Only 4 Screens)

1. `Feed`
   - Scored object list
   - Fast filters/sort (date, source, dimension values)
2. `Object Detail`
   - Object metadata
   - Dimension scores and explanations
   - Linked entities
3. `Entity Detail`
   - Aggregated entity scores
   - Related objects
4. `Pipeline Board`
   - Manual card placement and movement across stages

### API Interfaces (Stage 1)

1. `streams.list/create/update/delete/trigger`
2. `objects.feed/detail`
3. `entities.detail`
4. `dimensions.list/create/update/delete`
5. `scores.backfillDimension`
6. `pipelines.list/create/update/delete/getBoard/addCard/moveCard/removeCard`
7. `apiKeys.upsert/revoke/listProviders`

### Minimal Data Model (Stage 1)

1. `research_objects`
2. `entities`
3. `object_entities`
4. `dimensions`
5. `object_scores`
6. `entity_scores`
7. `pipelines`
8. `pipeline_stages`
9. `object_pipeline_cards`
10. `streams`
11. `stream_runs`
12. `api_keys`

## Explicitly Out of Scope (Stage 1)

1. Auth/team/roles
2. Multitenancy and RLS
3. External plugin/webhook system
4. Processor/action plugins
5. Automated triggers
6. Trend radar and BERTrend
7. Chat/query interface
8. Hybrid semantic search (vector+BM25)
9. Advanced admin/compliance modules
10. Additional source adapters beyond OpenAlex

## Performance Targets (Local)

1. Time to first scored result after manual stream trigger: `< 60s`
2. Feed query p95 with sort/filter: `< 200ms` database time
3. Scoring success rate: `> 95%` (excluding provider outages)
4. UX reliability: no blank/error-only states on primary screens

## Acceptance Tests (Stage 1 Exit Gate)

1. Create stream and trigger run -> objects appear in DB
2. Create dimension -> scores generated for new and existing objects
3. Same author across objects resolves to one entity
4. Entity aggregate score changes after object score changes
5. Add object to pipeline and move across stages
6. End-to-end local flow from empty workspace to first actionable card

## Stage Progression Rule

Stage 2 starts only when all Stage 1 acceptance tests pass and local performance targets are met.
