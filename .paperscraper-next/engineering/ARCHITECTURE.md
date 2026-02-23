# Architecture Blueprint (Stage-Aware)

This document is the architecture contract for the two-stage build.

1. Stage 1 = strict local MVP
2. Stage 2 = productization without bloat

## Core Principle

The workflow is the product:

**Subscribe -> Ingest -> Score -> Review -> Act**

Architecture decisions are accepted only if they improve this loop's speed, clarity, or reliability.

## Stage 1 Architecture (Locked)

### Runtime and Stack

1. Runtime: Bun (API and workers)
2. Frontend: TanStack Start
3. API: tRPC only (internal)
4. Queue: BullMQ + Redis
5. Database: PostgreSQL 16 + pgvector available
6. Topology: local-first single workspace

### Stage 1 System Diagram

```
Frontend (TanStack Start)
  ├─ Feed
  ├─ Object Detail
  ├─ Entity Detail
  └─ Pipeline Board
      │
      ▼
API (tRPC on Bun)
  ├─ streams
  ├─ objects
  ├─ entities
  ├─ dimensions
  ├─ pipelines
  └─ apiKeys
      │
      ├─ PostgreSQL (objects, entities, scores, pipelines, streams)
      └─ Redis/BullMQ (ingestion, scoring, fold-up jobs)
```

### Stage 1 Process Flow

1. User triggers stream
2. OpenAlex adapter fetches and normalizes objects
3. Objects are upserted with dedup
4. Entities are resolved and linked
5. Scoring jobs run for active dimensions
6. Entity fold-up recomputes aggregates
7. UI queries invalidated for feed/detail/board refresh

### Stage 1 Hard Constraints

1. No external plugin webhooks
2. No automated triggers
3. No chat/query interface
4. No hybrid semantic search
5. No new top-level screens beyond the four core pages

## Stage 2 Architecture (Controlled Expansion)

Stage 2 is split into waves. Each wave must preserve the Stage 1 workflow mental model.

### Wave 1: Workflow UX Hardening

1. Saved views
2. Keyboard-first operations
3. Faster triage actions

### Wave 2: Platform Foundations

1. Auth and roles
2. Workspace multitenancy
3. PostgreSQL RLS
4. Audit and observability hardening

### Wave 3: Selective Intelligence

1. Basic text search
2. Hybrid vector+BM25 when relevance metrics justify it
3. Optional trigger automation with explainable rule evaluation

### Wave 4: Extensibility and Admin

1. Plugin/webhook surface
2. Enterprise admin/compliance modules
3. Modular, opt-in administrative UI

## ADR Summary

| # | Decision | Stage | Choice | Rationale |
|---|---|---|---|---|
| 1 | Build sequencing | Stage 1/2 | Two-stage execution | Prevents bloat before value validation |
| 2 | Product surface | Stage 1 | 4 screens only | Keeps 10x workflow visible |
| 3 | Runtime | Stage 1 | Bun end-to-end | Fast local iteration and unified runtime |
| 4 | API style | Stage 1 | tRPC only | Tight type coupling for rapid MVP delivery |
| 5 | Data source | Stage 1 | OpenAlex only | One high-value source avoids ingestion sprawl |
| 6 | Pipeline behavior | Stage 1 | Manual only | Avoid hidden automation complexity |
| 7 | Tenancy model | Stage 1 | Single workspace | Remove auth/multi-tenant overhead from MVP |
| 8 | Tenancy hardening | Stage 2 | RLS + roles | Security after core workflow validation |
| 9 | Search depth | Stage 2 | Text first, hybrid later | Complexity added only with measurable gain |
| 10 | Extensibility | Stage 2 | Plugin/webhook system | Delay until demand is proven |

## Anti-Bloat Architecture Rules

1. Any feature must map to one step in the core loop.
2. No new top-level navigation without removing or merging an existing one.
3. Platform/admin additions are forbidden in Stage 1.
4. Any architecture proposal must include:
   - workflow impact
   - screen surface impact
   - operational complexity impact
