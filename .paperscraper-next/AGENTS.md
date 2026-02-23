# PaperScraper Next Codex Agent Contract

This document defines strict, stage-aware rules for Codex agents working on PaperScraper Next.

## Scope and Precedence
- Applies to `.paperscraper-next` planning artifacts and the future separate v2 workspace code.
- Stage documents (`STAGE_1_LOCAL_MVP.md`, `STAGE_2_PRODUCTIZATION.md`) are source of truth.
- Linter-enforced rules are hard constraints and merge blockers.

## Non-Negotiables
- `PSN001`: No ad hoc network calls outside API/adapter/provider boundaries.
- `PSN002`: Routers must call engine APIs only (no direct DB/raw SQL).
- `PSN003`: Engines must not directly import other engines.
- `PSN004`: No unused/single-use dependencies unless explicitly allowlisted.
- `PSN005`: No single-use shared UI components.
- `PSN006`: No single-use helper/util files.
- `PSN007`: Keep files compact via enforced line caps.
- `PSN008`: No unsafe execution/security primitives.
- `PSN009`: Performance guardrails are mandatory (`SELECT *` forbidden; workers require concurrency/retries).
- `PSN010`: Avoid ad hoc function sprawl (max functions/file enforced).

## Mandatory Workflow
1. Run strict architecture lint:
   - `npm run lint:agents`
2. Run touched-area checks:
   - Backend/infra: `ruff check .`, `ruff format --check .`, relevant tests
   - Frontend: `npm --prefix frontend run lint` (or v2 workspace equivalent), relevant tests
3. Do not mark work complete while lint blockers remain.

## Forbidden Patterns
- New top-level navigation outside the 4-screen Stage 1 MVP surface.
- Stage 1 introduction of plugins, trigger automation, chat, or hybrid semantic search.
- Router-level direct DB access and raw SQL in v2 workspace.
- Shared UI/helper abstractions with only one usage site.
- Inline lint suppressions and hidden bypass comments.

## Exception Process
- Inline suppressions are not allowed.
- Only valid exception path:
  - `/Users/bastianburger/Repos/PaperScraper/.agent-lint-allowlist.yaml`
- Every exception entry must include:
  - `rule_id`
  - `path`
  - `match`
  - `reason`
  - `owner`
  - `expires_on` (ISO date)
- Expired/incomplete entries fail strict linter checks.
