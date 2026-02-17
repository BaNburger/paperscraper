# PaperScraper v2.0 - Implementation Plan & Cutover Runbook

## 1. Scope
This runbook defines the v2.0 big-bang execution path for architecture simplification, security hardening and contract synchronization.

In scope:
- Cookie-session auth + CSRF for browser traffic.
- OpenAPI-driven contract generation and CI freshness checks.
- Ingestion control-plane consolidation.
- Shared storage/upload validation.
- Secret encryption hardening + migration.
- Canonical architecture documentation refresh.

Out of scope:
- Backward-compatibility API shims.
- Incremental dual-runtime rollout.

## 2. Cutover Strategy
- Rollout model: scheduled maintenance window.
- Order: backend + workers first, frontend second.
- Data safety: mandatory backup and restore validation before migration.

## 3. Pre-Cutover Checklist

### 3.1 Data safety and migration readiness
- Create full database backup.
- Execute restore rehearsal on staging snapshot.
- Dry-run Alembic migration chain including model-key re-encryption migration.
- Validate legacy model key records are re-encrypted (`enc:v1:`).

### 3.2 Contract and build readiness
- Regenerate backend OpenAPI (`scripts/export_openapi.py`).
- Regenerate frontend API types (`frontend/src/api/generated`).
- Ensure CI freshness checks pass.
- Build frontend with generated artifacts.

### 3.3 Quality gates before maintenance
- Backend tests at/above baseline pass count.
- Frontend lint/typecheck/build/tests pass.
- Smoke scripts prepared for auth, ingestion, uploads, scoring, reports.

## 4. Cutover Execution Steps

### 4.1 Enter maintenance mode
- Block mutating user traffic.
- Keep health endpoints reachable for rollout monitoring.

### 4.2 Backend and worker deployment
- Deploy backend app image.
- Deploy worker image(s) with matching commit.
- Apply Alembic migrations.
- Confirm workers can dequeue and process jobs.

### 4.3 Frontend deployment
- Deploy frontend artifact that uses cookie-session auth and generated API contracts.
- Invalidate cached assets/CDN as needed.

### 4.4 Smoke validation (blocking)
- Auth:
  - login sets cookies
  - refresh works without JS token storage
  - logout clears cookies
  - CSRF rejects missing/invalid header
- Ingestion:
  - create source run under `/api/v1/ingestion/*`
  - run status transitions observable
- Uploads:
  - invalid files rejected consistently
  - valid PDF path stored via shared adapter
- Scoring and reporting:
  - trigger scoring path
  - run a scheduled/manual report path

If any blocking smoke fails: keep maintenance mode on and execute rollback decision.

## 5. Post-Cutover Validation (0-24h)
- Run integrity checks:
  - ingestion run status consistency
  - orphan source record checks
  - decrypt/re-encrypt sanity for model keys
- Monitor:
  - error rates
  - security logs (CSRF failures, auth anomalies)
  - worker queue depth and retry rates
- Exit maintenance mode only after smoke + integrity checks pass.

## 6. Rollback Plan
- Trigger conditions:
  - blocking auth regression
  - data integrity violation
  - sustained worker failure on critical flows
- Rollback actions:
  1. Keep maintenance mode enabled.
  2. Restore DB from pre-cutover backup.
  3. Re-deploy previous backend/worker/frontend artifacts.
  4. Verify core health and login flow before reopening traffic.

## 7. Acceptance Criteria

### 7.1 Functional architecture
- Browser auth is cookie-session based with CSRF enforcement.
- Ingestion routes are consolidated under ingestion module.
- Upload and storage flow uses shared abstractions.
- Secret storage uses encrypted envelope format.

### 7.2 Contract and docs governance
- OpenAPI + generated frontend types are current and CI-enforced.
- Root canonical docs updated:
  - `01_TECHNISCHE_ARCHITEKTUR.md`
  - `04_ARCHITECTURE_DECISIONS.md`
  - `05_IMPLEMENTATION_PLAN.md`
- Docs index/status pages point to root canonical documents.

## 8. Operational Ownership
- Engineering owns migration execution and rollback decision support.
- Product/Operations owns maintenance window communication and go/no-go coordination.
- Security reviews post-cutover logs and validates hardened-path behavior.
