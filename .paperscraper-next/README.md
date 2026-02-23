# PaperScraper Next

> Two-stage blueprint for rebuilding PaperScraper around the core 10x workflow.

## Why This Exists

The current product has broad feature depth, but the core value proposition is hidden behind stale and fragmented workflows.

PaperScraper Next fixes this by enforcing a strict build order:

1. **Stage 1: Local 10x MVP**
   - Build only the core loop: subscribe -> ingest -> score -> review -> act
   - Bun + TanStack, local-first, single-workspace dev mode
   - Four screens only: Feed, Object Detail, Entity Detail, Pipeline Board
2. **Stage 2: Productization Without Bloat**
   - Expand capabilities only when they strengthen the core loop
   - Add auth/tenancy/admin/extensibility in controlled waves

## Directory Structure

```
.paperscraper-next/
├── README.md
├── pm/
│   ├── VISION.md
│   ├── PERSONAS.md
│   ├── V1_STRENGTHS.md
│   └── MVP_SCOPE.md                  # Stage 1 only
├── engineering/
│   ├── ARCHITECTURE.md               # Stage-aware architecture
│   ├── DATA_MODEL.md                 # Stage 1 minimal schema + Stage 2 additions
│   ├── ENGINES.md                    # Stage 1 engine contracts + Stage 2 extensions
│   └── PLUGIN_SYSTEM.md              # Stage 2 only (not in MVP)
├── claude-code/
│   ├── CLAUDE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── STAGE_1_LOCAL_MVP.md
│   ├── STAGE_2_PRODUCTIZATION.md
│   └── PHASE_*.md                    # Legacy drafts (superseded by stage docs)
└── research/
    └── FRONTIER_METHODS.md
```

## How To Use

1. Read `pm/MVP_SCOPE.md` for strict Stage 1 boundaries.
2. Read `engineering/ARCHITECTURE.md` for the architecture contract.
3. Execute `claude-code/STAGE_1_LOCAL_MVP.md` first.
4. Move to `claude-code/STAGE_2_PRODUCTIZATION.md` only after Stage 1 acceptance tests pass.

## Non-Negotiable Build Order

1. Do not add plugins, chat, automation, or hybrid semantic search during Stage 1.
2. Do not add new top-level navigation beyond the four core MVP screens.
3. Do not start Stage 2 before Stage 1 performance and acceptance criteria are met.
