# Stage 2: Productization Without Bloat (Execution Spec)

## Stage Goal

Expand the MVP into a production-capable product while preserving the clear 10x workflow.

## Productization Rule

A feature is accepted only if it makes the core loop faster, clearer, or more reliable.

If it does not, it is deferred.

## Wave Plan (Strict Order)

## Wave 1: UX Hardening and IA Polish

1. Preserve four-screen mental model
2. Add saved views as secondary UI (drawer/panel), not top-level nav
3. Add keyboard-first actions for triage speed
4. Add batch actions and quick pipeline actions

Acceptance:

1. Core tasks require fewer clicks/keystrokes than Stage 1 baseline
2. No additional top-level navigation added

## Wave 2: Platform Foundations

1. Introduce auth and roles
2. Introduce workspaces and tenant scoping
3. Enforce PostgreSQL RLS
4. Add audit logging for mutations
5. Add observability for API/workers/queues

Acceptance:

1. Tenant isolation tests pass (including cross-tenant denial)
2. Workflow UX remains unchanged for existing core tasks

## Wave 3: Selective Intelligence

1. Add basic text search first
2. Add hybrid vector+BM25 only if relevance benchmark justifies complexity
3. Add optional trigger automation with explainable rule logs

Acceptance:

1. Search quality/latency metrics improve against Stage 1 baseline
2. Trigger actions are observable and reversible

## Wave 4: Extensibility and Enterprise Admin

1. Add plugin/webhook system
2. Add enterprise admin/compliance modules as optional sections
3. Keep admin IA out of primary workflow navigation

Acceptance:

1. Plugin failures do not break core workflow
2. Admin features are modular and opt-in

## Anti-Bloat Governance (Mandatory)

1. Every feature proposal includes:
   - workflow impact
   - screen surface impact
   - operational complexity impact
2. No new top-level navigation item without removing or merging another
3. Quarterly workflow clarity audit against real user tasks

## Testing Strategy

1. Keep Stage 1 golden-path E2E as permanent release gate
2. Add Stage 2 tenancy/security test suites
3. Add regression tests ensuring core loop is not degraded by new modules

## Regression-Proofing Rules

1. Do not gate core workflow behind admin setup complexity
2. Do not introduce opaque automation defaults
3. Do not add platform abstractions before concrete reuse exists
