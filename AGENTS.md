# PaperScraper Codex Agent Contract

This document defines strict, repository-specific rules for Codex-based agents.

## Scope and Precedence
- This file applies to all Codex-based agents working in this repository.
- Repository policy in this file and `CLAUDE.md` takes precedence over default assistant behavior.
- Linter-enforced architecture rules are hard constraints. Violations are merge blockers.

## Non-Negotiables
- `PSA001`: Do not add source ingestion endpoints to `paper_scraper/modules/papers/router.py`.
- `PSA002`: Source run endpoints belong only in `paper_scraper/modules/ingestion/router.py`.
- `PSA003`: Use shared storage abstraction only; no direct `boto3`/`minio` usage outside `paper_scraper/core/storage.py`.
- `PSA004`: Routers must call public service APIs only; never call private methods.
- `PSA005`: Do not introduce legacy secret formats (`plain:`). Use encrypted secret path (`enc:v1:`).
- `PSF001`: Do not hardcode `/api/v1/...` literals in frontend app code.
- `PSF002`: Do not use `fetch`/`axios` directly outside `frontend/src/api/http/`.
- `PSF003`: In `frontend/src/api/domains/`, do not import DTOs from `frontend/src/types/index.ts`.
- `PSF004`: Infra navigation must use `frontend/src/config/routes.ts`; no hardcoded route literals.
- `PSF005`: Hook query declarations must use `frontend/src/config/queryKeys.ts`.
- `PSF006`: Never persist auth tokens in browser local/session storage.
- `PSF007`: Do not introduce new `ResearchGroup` domain naming.
- `PSD001`/`PSD002`/`PSD003`: Keep agent policy docs present and up to date.
- `PSN001`: In v2 workspace, no ad hoc network calls outside API/adapter/provider boundaries.
- `PSN002`: In v2 workspace, routers must call engine APIs only (no direct DB/raw SQL).
- `PSN003`: In v2 workspace, engines must not directly import other engines.
- `PSN004`: In v2 workspace, dependencies must not be unused or single-use unless allowlisted.
- `PSN005`: In v2 workspace, shared components must be reused; single-use shared components are forbidden.
- `PSN006`: In v2 workspace, helper/util files must be reused or removed.
- `PSN007`: In v2 workspace, file-size limits enforce compact modules.
- `PSN008`: In v2 workspace, unsafe execution/security primitives are forbidden.
- `PSN009`: In v2 workspace, performance guardrails are enforced (`SELECT *` forbidden; workers need concurrency/retries).
- `PSN010`: In v2 workspace, function sprawl is forbidden (max functions/file).

## Mandatory Workflow
1. Run strict architecture lint:
   - `npm run lint:agents`
2. Run quality checks for touched areas:
   - Backend: `ruff check .`, `ruff format --check .`, relevant `pytest` tests
   - Frontend: `npm --prefix frontend run lint`, relevant frontend tests/build checks
3. Do not mark work complete while lint blockers remain.

## Forbidden Patterns
- Hardcoded frontend API base/endpoint strings like `"/api/v1/..."`.
- Direct `fetch`/`axios` calls in pages/components/hooks outside `frontend/src/api/http/`.
- Router calls like `service._internal_method(...)`.
- Reintroducing compatibility alias naming (`ResearchGroup`) in new code.
- In v2 workspace, creating single-use shared components or helper files.
- In v2 workspace, adding dependencies with only one usage site (unless allowlisted).
- In v2 workspace, direct router-to-database access and cross-engine imports.
- In v2 workspace, `SELECT *`, missing worker concurrency settings, or missing retry policy.
- Inline lint suppressions or hidden bypass comments.
- Browser auth token storage in `localStorage`/`sessionStorage`.

## Exception Process
- Inline suppressions are not allowed.
- The only valid exception path is:
  - `/Users/bastianburger/Repos/PaperScraper/.agent-lint-allowlist.yaml`
- Each exception entry must include:
  - `rule_id`
  - `path`
  - `match`
  - `reason`
  - `owner`
  - `expires_on` (ISO date)
- Expired or incomplete entries fail the strict linter.
