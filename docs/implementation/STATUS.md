# PaperScraper v2.0 Implementation Status

[← Back to INDEX](../INDEX.md)

Last updated: 2026-02-20

## Current State
- Target architecture: v2.0 streamlined monolith with contract-first API and hardened browser auth.
- Rollout model: big-bang cutover with maintenance window.
- Canonical architecture docs:
  - [../../01_TECHNISCHE_ARCHITEKTUR.md](../../01_TECHNISCHE_ARCHITEKTUR.md)
  - [../../04_ARCHITECTURE_DECISIONS.md](../../04_ARCHITECTURE_DECISIONS.md)
  - [../../05_IMPLEMENTATION_PLAN.md](../../05_IMPLEMENTATION_PLAN.md)

## v2.0 Workstream Summary
- Contract sync: backend OpenAPI export + frontend generated API artifacts + CI freshness checks.
- Auth/security: cookie-session auth transport, CSRF enforcement, SSRF protections, user-aware rate-limit keying.
- Ingestion: source ingestion endpoints consolidated under ingestion module and unified async job path.
- Storage/uploads: shared storage abstraction usage + centralized upload validation/sanitization.
- Secrets: encrypted model key envelope format (`enc:v1`) with migration path for legacy stored values.
- Frontend architecture: centralized route registry used by router wiring, command palette, keyboard shortcuts, and prefetch.
- **Data architecture (ADR-032)**: Three-tier split — PostgreSQL (relational), Qdrant (vector search), Typesense (full-text search). All pgvector columns dropped; `SyncService` provides dual-write orchestration. Migration: `qdrant_typesense_v1`.

## Quality Snapshot
- Backend regression baseline suite: passes (`835 passed, 3 skipped, 2 xpassed`).
- Frontend tests: passing.
- Frontend build/typecheck: passing.
- Repository-wide strict lint/type closure is still in progress (legacy backlog outside v2-touched areas remains).

## Historical Sprint/Phase Records
For prior sprint-by-sprint narratives, see the archived phase documents in this folder:
- `PHASE_01_FOUNDATION.md` ... `PHASE_10_FOUNDATIONS.md`
