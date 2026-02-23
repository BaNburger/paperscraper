# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 7: Query Engine

## Goal
Hybrid search (BM25 + vector), saved views with filters, search UI.

## Sprint 14: Hybrid Search

### Search Function

Full implementation in `../engineering/ENGINES.md` section 5.

Combines:
1. Full-text BM25 ranking (`ts_rank_cd` with PostgreSQL GIN index)
2. Vector semantic similarity (pgvector `<=>` cosine distance)
3. Structured filters (workspace_id, type, date, score thresholds)
4. Combined ranking: `bm25 * 0.3 + vector * 0.7`

### Search tRPC Route

```typescript
export const searchRouter = router({
  query: protectedProcedure
    .input(z.object({
      query: z.string().min(1),
      type: z.string().optional(),
      minYear: z.number().optional(),
      scoreFilters: z.array(z.object({
        dimensionId: z.string(),
        minValue: z.number(),
      })).optional(),
      limit: z.number().default(20),
      offset: z.number().default(0),
    }))
    .query(async ({ ctx, input }) => {
      // Generate query embedding
      const apiKey = await loadDecryptedApiKey(ctx.workspaceId, 'openai');
      const queryEmbedding = await embedText(input.query, apiKey);

      // Run hybrid search
      const results = await hybridSearch(
        ctx.workspaceId,
        input.query,
        queryEmbedding,
        input,
      );

      return results;
    }),
});
```

### Search UI

```
┌─────────────────────────────────────────┐
│ 🔍 Search research objects...            │
├─────────────────────────────────────────┤
│ Filters: [Type ▼] [Year ▼] [Score ▼]   │
├─────────────────────────────────────────┤
│ Results (23 found)                       │
│                                          │
│ ┌──────────────────────────────────────┐│
│ │ Paper Title (relevance: 0.92)        ││
│ │ Matched: abstract, semantic          ││
│ │ [IP: 8.2] [Nov: 7.1]                ││
│ └──────────────────────────────────────┘│
│ ...                                      │
└─────────────────────────────────────────┘
```

Integrate search into the Feed page header — typing in the search bar filters the feed.

## Sprint 15: Views + Filters

### View CRUD

```typescript
export const viewsRouter = router({
  list: protectedProcedure.query(/* list workspace views */),
  create: protectedProcedure.input(createViewSchema).mutation(/* ... */),
  execute: protectedProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ ctx, input }) => {
      const view = await ctx.db.view.findFirstOrThrow({
        where: { id: input.id, workspaceId: ctx.workspaceId },
      });

      return executeView(ctx.db, view);
    }),
});
```

### Filter Builder UI

A composable filter builder (like Notion's filter bar):

```
[+ Add filter]
├─ Type is Paper         [×]
├─ Year >= 2024          [×]
├─ IP Potential >= 7     [×]
└─ Author contains "Smith" [×]

Sort by: [Novelty Score ↓]
Group by: [None]
```

### View Layouts

- **Table** (default): rows with columns for title, type, scores, date
- **Grid**: card layout (like the Feed, but with custom filters applied)

### Verification Checklist
- [ ] Search by text returns BM25-ranked results
- [ ] Search includes semantic matches (not just keyword)
- [ ] Filters narrow results correctly (type, year, score threshold)
- [ ] Save a view with filters → reload → same results
- [ ] Table and grid layouts render correctly
- [ ] Search latency < 200ms for typical queries
- [ ] Empty state when no results match
