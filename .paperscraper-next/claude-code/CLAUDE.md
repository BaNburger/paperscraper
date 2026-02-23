# PaperScraper Next - Agent Instructions

This is the implementation contract for PaperScraper Next.

## Source of Truth

1. `IMPLEMENTATION_PLAN.md`
2. `STAGE_1_LOCAL_MVP.md`
3. `STAGE_2_PRODUCTIZATION.md`

Legacy `PHASE_*.md` files are superseded.

## Mandatory Build Order

1. Complete Stage 1 first
2. Prove Stage 1 acceptance tests and performance targets
3. Start Stage 2 only after Stage 1 exit gate passes

## Stage 1 Non-Negotiables

1. Four screens only: Feed, Object Detail, Entity Detail, Pipeline Board
2. OpenAlex-only ingestion
3. Real BYOK scoring
4. Manual pipeline only
5. Single-workspace local dev mode
6. Bun runtime + TanStack Start + tRPC + BullMQ

## Stage 1 Forbidden Work

1. External plugins/webhooks
2. Automated triggers
3. Chat/query interface
4. Hybrid semantic search
5. Auth/roles/RLS
6. Admin/compliance expansions

## Stage 2 Expansion Order

1. Wave 1: UX hardening
2. Wave 2: auth + tenancy + RLS
3. Wave 3: selective automation/search depth
4. Wave 4: plugins and enterprise admin

## Engineering Rules

1. Keep architecture decisions tied to core loop impact
2. Keep top-level navigation constrained to prevent clutter
3. Add complexity only when metrics demonstrate clear improvement
4. Maintain a permanent Stage 1 gold-path E2E release gate

## Linter-Enforced Lean Rules

Run strict lint before completion:

```bash
npm run lint:agents
```

### PSN Rules (PaperScraper Next)

1. `PSN001`: No ad hoc network calls outside API/adapter/provider boundaries
2. `PSN002`: Routers must not use direct DB/raw SQL access
3. `PSN003`: Engines must not directly import other engines
4. `PSN004`: Dependencies must not be unused or single-use (unless allowlisted)
5. `PSN005`: Shared components must be reused (single-use shared components forbidden)
6. `PSN006`: Helper/util files must be reused or removed
7. `PSN007`: File-size caps keep modules compact and reviewable
8. `PSN008`: Unsafe execution/security primitives are forbidden
9. `PSN009`: Performance guardrails enforced (`SELECT *` forbidden, workers require concurrency/retries)
10. `PSN010`: Function sprawl is forbidden (max functions/file)

### Exception Workflow

Inline suppressions are forbidden.  
Use only `/Users/bastianburger/Repos/PaperScraper/.agent-lint-allowlist.yaml` with:

1. `rule_id`
2. `path`
3. `match`
4. `reason`
5. `owner`
6. `expires_on` (ISO date)
