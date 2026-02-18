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

## Mandatory Workflow
1. Run strict architecture lint:
   - `npm run lint:agents`
2. Run quality checks for touched areas:
   - Backend: `ruff check .`, `ruff format --check .`, `mypy paper_scraper`, relevant `pytest` tests
   - Frontend: `npm --prefix frontend run lint`, relevant frontend tests/build checks
3. If architecture-impacting files changed, update canonical root docs:
   - `/Users/bastianburger/Repos/PaperScraper/01_TECHNISCHE_ARCHITEKTUR.md`
   - `/Users/bastianburger/Repos/PaperScraper/04_ARCHITECTURE_DECISIONS.md`
   - `/Users/bastianburger/Repos/PaperScraper/05_IMPLEMENTATION_PLAN.md`
4. Do not mark work complete while lint blockers remain.

## Forbidden Patterns
- Hardcoded frontend API base/endpoint strings like `"/api/v1/..."`.
- Direct `fetch`/`axios` calls in pages/components/hooks outside `frontend/src/api/http/`.
- Router calls like `service._internal_method(...)`.
- Reintroducing compatibility alias naming (`ResearchGroup`) in new code.
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

