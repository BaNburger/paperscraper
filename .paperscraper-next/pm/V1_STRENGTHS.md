# V1 Strengths to Preserve

What works in the current PaperScraper and how it maps to v2.

## 1. Performance Patterns → KEEP

| V1 Pattern | V2 Adaptation |
|-----------|---------------|
| Route-based lazy loading | TanStack Start code splitting (built-in) |
| TanStack Query caching (staleTime, keepPreviousData) | Same, via tRPC + TanStack Query integration |
| Prefetch on route hover | TanStack Router preloading (native support) |
| Skeleton loading states | Shadcn/UI Skeleton component |
| Async/await throughout backend | Bun native async (even faster) |
| Tenant-isolated queries | Middleware-enforced workspace_id filter |

## 2. Architecture Discipline → ADAPT

V1 has 13 linter rules (PSA001-PSF007, PSD001-003) that prevent architectural drift. This is exceptional and rare in startups.

**V2 adaptation:** Simpler rules because simpler architecture.

| V1 Rule | V2 Equivalent |
|---------|---------------|
| PSA001-002: Ingestion route isolation | N/A — only 5 engines, no route confusion |
| PSA003: Storage SDK abstraction | Keep — abstract vector store behind interface |
| PSA004: No private service methods in routers | Keep — tRPC procedures call engine methods only |
| PSF001: No literal API paths | Keep — tRPC eliminates this problem entirely |
| PSF002: No direct fetch/axios | Keep — tRPC client only |
| PSF005: Centralized query keys | N/A — tRPC auto-generates query keys |
| PSF006: No browser auth token storage | Keep — Better Auth uses httpOnly cookies |

**New rules for v2:**
- Engines must not import from other engines (communicate via events)
- All JSONB access through typed helpers (no raw JSON.parse in components)
- Plugin contracts validated with Zod at boundaries
- Every database query includes workspace_id (enforced by Prisma middleware)

## 3. Security Model → KEEP AS-IS

V1's security is production-grade. Preserve entirely:

- **HttpOnly cookies + CSRF** → Better Auth provides this natively
- **Encrypted secrets (enc:v1)** → Keep for BYOK API key storage
- **SSRF protections** → Keep for webhook/plugin URL validation
- **Rate limiting** → Upstash rate limiter (managed)
- **Audit trail** → Simplified: fewer event types but same immutable log pattern

## 4. Admin Features → SLIM DOWN

V1 has exceptional admin depth. V2 keeps the essentials, drops the rest:

| V1 Feature | V2 Status | Rationale |
|-----------|-----------|-----------|
| RBAC (15 permissions, 4 roles) | **Simplify** → 3 roles, 8 permissions (see RBAC table below) | Fewer features = fewer permissions needed |
| API key management | **Keep** | External integrations need this |
| Webhook management | **Keep** | Core to plugin system |
| Model/provider config | **Keep** | BYOK is a core feature |
| Audit logs | **Keep** | Enterprise requirement |
| Compliance (GDPR, retention) | **Defer** | Add when enterprise customers demand it |
| Gamification/badges | **Drop** | Doesn't fit the lean CRM model |
| Scheduled reports | **Defer** | Nice-to-have, not MVP |
| Team/department management | **Simplify** → flat team, no departments | Complexity without clear value at start |

### V2 RBAC Model

**3 roles:**

| Role | Description |
|------|-----------|
| `admin` | Full workspace access. Can manage team, API keys, billing. |
| `member` | Full operational access. Can create/edit streams, dimensions, pipelines, move cards. |
| `viewer` | Read-only. Can browse Feed, view details, see pipelines. Cannot modify anything. |

**8 permissions:**

| Permission | Admin | Member | Viewer |
|-----------|:-----:|:------:|:------:|
| `workspace.manage` (settings, API keys, team) | ✓ | | |
| `stream.write` (create, edit, delete, trigger streams) | ✓ | ✓ | |
| `dimension.write` (create, edit, delete dimensions) | ✓ | ✓ | |
| `pipeline.write` (create, edit, delete pipelines) | ✓ | ✓ | |
| `card.write` (add, move, remove cards) | ✓ | ✓ | |
| `view.write` (create, edit saved views) | ✓ | ✓ | |
| `data.read` (browse feed, search, view details) | ✓ | ✓ | ✓ |
| `data.export` (Phase 3: CSV, API export) | ✓ | ✓ | |

Permissions checked via middleware: `requirePermission('stream.write')` wraps tRPC procedures. Stored as `role` field on `User` model — no separate permissions table at MVP.

## 5. Developer Experience → EVOLVE

| V1 Pattern | V2 Evolution |
|-----------|-------------|
| OpenAPI auto-generation + frontend codegen | tRPC eliminates this entirely (types flow automatically) |
| Module template (models/schemas/service/router) | Engine template (simpler: types/service/router in one module) |
| Poetry + npm dual toolchain | pnpm only (full TypeScript) |
| Alembic migrations | Prisma migrations |
| pytest + Vitest + Playwright | Vitest + Playwright (one test runner for TS) |

## 6. Search → UPGRADE

V1's three-tier search (PostgreSQL + Qdrant + Typesense) is overengineered for v2.

**V2:** PostgreSQL only — pgvector HNSW for semantic search + GIN index for full-text + JSONB indexes for metadata. Single database, compound queries in one SELECT. Add hybrid ranking (BM25 + vector + optional ColBERT reranking).

pgvector with HNSW handles 1-10M vectors comfortably on Neon's standard plans. At 10M+ vectors or when p95 search latency exceeds 200ms, evaluate pgvectorscale extension or dedicated vector DB. Abstract behind `VectorStore` interface (see DATA_MODEL.md) for future swap without engine code changes.

## 7. Ingestion Pipeline → SIMPLIFY

V1 has a sophisticated multi-source pipeline with checkpoints and resumable runs. The pattern is sound; the implementation is overbuilt.

**V2:** Same concept, cleaner execution. A Stream is a cron job that calls a Source Adapter (webhook or built-in). Adapter returns normalized objects. Dedup by external_id. Queue for scoring. Done.

No checkpoint tracking (retry the whole batch — idempotency guaranteed by `ON CONFLICT (workspace_id, external_id) DO UPDATE` upsert). No run lifecycle management (just job status in BullMQ). No separate discovery/ingestion/papers modules (one Ingestion Engine).

## 8. KanBan/Pipeline → GENERALIZE

V1's KanBan is paper-specific (PaperProjectStatus model). V2 makes it entity-agnostic.

**V2:** A Pipeline accepts any entity type (object, person, organization). Stages are user-defined. Cards are just pointers to graph entities. This means you can have a "Researcher Recruitment" pipeline tracking authors, or a "Partnership Assessment" pipeline tracking organizations — same UI, same engine.

## 9. i18n → DEFER INFRASTRUCTURE TO PHASE 3

V1 has full EN/DE coverage with no hardcoded strings. **For MVP, write English strings directly in components** (no i18n framework). This saves ~2 days of setup and reduces abstraction for 9 pages.

**Phase 3:** Add `next-intl` or equivalent, extract all strings to translation files, add DE. The extraction is mechanical if strings are clean — no special upfront prep needed.

## 10. Mobile-First Responsive → KEEP

V1's bottom nav (mobile) + collapsible sidebar (desktop) pattern is solid. Shadcn/UI + TailwindCSS makes this even cleaner in v2.

---

## What We're Deliberately Dropping

| V1 Feature | Why It's Cut |
|-----------|-------------|
| 6 hardcoded scoring dimensions | Users define their own |
| Innovation Radar (fixed visualization) | Replaced by generic Trend Radar |
| Technology Transfer CRM (conversations, messages) | Replaced by generic Pipeline + action layer |
| Submissions module | Too specific (TTO-only feature) |
| Knowledge base module | Out of scope |
| Groups (research group management) | Replaced by Organizations in the graph |
| Badges/gamification | Doesn't fit the lean model |
| Export module (CSV, PDF, Zotero) | Defer — add as plugins later |
| Trends module (hardcoded) | Replaced by automated BERTrend detection |
| 19 extra pages | 9 pages cover everything |

**Net result:** Fewer features (9 pages vs. 28), more flexibility (user-defined dimensions/pipelines vs. hardcoded), smaller codebase (~12k LoC vs. estimated 60-80k).
