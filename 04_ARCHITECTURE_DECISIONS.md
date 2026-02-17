# PaperScraper v2.0 - Architecture Decisions (ADRs)

Dieses Dokument ist die kanonische ADR-Sammlung für v2.0.

## ADR-024: Big-Bang v2.0 Cutover
- Status: Accepted
- Date: 2026-02-17
- Decision: No backward-compatible runtime shims; one coordinated cutover with maintenance window.
- Rationale: Reduces long-term complexity, avoids dual-path bug surface, accelerates cleanup.
- Consequences:
  - Explicit migration runbook and smoke suite are required.
  - Rollback strategy is backup/restore + redeploy previous release.

## ADR-025: Browser Auth via HttpOnly Cookies + CSRF
- Status: Accepted
- Date: 2026-02-17
- Decision: Browser authentication uses secure HttpOnly access/refresh cookies; mutating cookie-auth requests require CSRF header token.
- Rationale: Eliminates JS token storage exposure, improves XSS resilience, standardizes browser session handling.
- Consequences:
  - Frontend uses `withCredentials` and no localStorage token persistence.
  - Auth endpoints set/refresh/clear cookies.
  - Middleware enforces CSRF for cookie-authenticated mutating routes.

## ADR-026: OpenAPI as Contract Source of Truth
- Status: Accepted
- Date: 2026-02-17
- Decision: OpenAPI schema is exported from backend code and used to generate frontend API types.
- Rationale: Prevents DTO drift, enables compile-time contract verification, simplifies cross-team evolution.
- Consequences:
  - `openapi.json` is generated from backend app.
  - Frontend generated types live under `frontend/src/api/generated`.
  - CI fails on stale schema/codegen artifacts.

## ADR-027: Ingestion Control Plane Consolidation
- Status: Accepted
- Date: 2026-02-17
- Decision: Source ingestion entrypoints and run state authority live in ingestion module only.
- Rationale: Removes duplicated orchestration paths and conflicting status ownership.
- Consequences:
  - Source ingestion endpoints removed from papers router.
  - `/api/v1/ingestion/*` owns run creation, listing, detail and source run execution initiation.
  - Workers use unified typed source-ingestion payloads.

## ADR-028: Shared Storage and Upload Validation
- Status: Accepted
- Date: 2026-02-17
- Decision: Modules must use shared storage abstraction and shared upload validation/sanitization helpers.
- Rationale: Avoids inconsistent key handling, duplicate validation logic, and blocking I/O patterns in async paths.
- Consequences:
  - Direct ad-hoc storage client usage is removed from module services.
  - Upload MIME/magic validation and filename sanitization are centralized.

## ADR-029: Secret Encryption Hardening
- Status: Accepted
- Date: 2026-02-17
- Decision: Replace reversible base64 “encryption” with encrypted envelope format (`enc:v1`) using Fernet key material.
- Rationale: Base64 is encoding, not encryption; sensitive model/provider keys require real cryptographic protection.
- Consequences:
  - Data migration upgrades legacy stored values without data loss.
  - Plain secret compatibility paths are removed from runtime logic.

## ADR-030: Security Hardening Baseline
- Status: Accepted
- Date: 2026-02-17
- Decision: Enforce SSRF protections in remote fetch paths and user-aware rate-limit keying.
- Rationale: Reduces lateral movement and internal network probing risk, improves fair-use enforcement.
- Consequences:
  - Unsafe URL targets and redirects are blocked.
  - Rate limiting keys prefer authenticated user context.

## ADR-031: Root Architecture Docs as Canonical
- Status: Accepted
- Date: 2026-02-17
- Decision: Root files are canonical architecture artifacts:
  - `01_TECHNISCHE_ARCHITEKTUR.md`
  - `04_ARCHITECTURE_DECISIONS.md`
  - `05_IMPLEMENTATION_PLAN.md`
- Rationale: Keeps architecture control documents stable, visible and CI-governed.
- Consequences:
  - `docs/INDEX.md` and `docs/implementation/STATUS.md` reference root canonical docs.
  - Architecture-impacting PRs must keep these root docs in sync.
