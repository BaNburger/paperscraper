# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 6: Pipeline Engine

## Goal
Kanban board with drag-and-drop, user-defined stages, automated triggers.

## Sprint 12: Pipeline CRUD + Board

### Pipeline tRPC Routes

```typescript
export const pipelinesRouter = router({
  list: protectedProcedure.query(/* list all pipelines */),
  create: protectedProcedure.input(createPipelineSchema).mutation(/* ... */),
  getBoard: protectedProcedure.input(z.object({ id: z.string() })).query(async ({ ctx, input }) => {
    const pipeline = await ctx.db.pipeline.findFirstOrThrow({
      where: { id: input.id, workspaceId: ctx.workspaceId },
    });

    const cards = await ctx.db.pipelineCard.findMany({
      where: { pipelineId: pipeline.id },
      orderBy: { position: 'asc' },
    });

    // Hydrate cards with object/entity data + scores
    const hydratedCards = await hydrateCards(cards, ctx.db);

    // Group by stage
    const stages = (pipeline.stages as Stage[]).map(stage => ({
      ...stage,
      cards: hydratedCards.filter(c => c.stage === stage.name),
    }));

    return { pipeline, stages };
  }),

  addCard: protectedProcedure
    .input(z.object({
      pipelineId: z.string(),
      targetType: z.enum(['object', 'entity']),
      targetId: z.string(),
      stage: z.string(),
    }))
    .mutation(/* upsert card */),

  moveCard: protectedProcedure
    .input(z.object({
      cardId: z.string(),
      stage: z.string(),
      position: z.number(),
    }))
    .mutation(/* update card stage + position */),

  removeCard: protectedProcedure
    .input(z.object({ cardId: z.string() }))
    .mutation(/* delete card */),
});
```

### Kanban Board Component

Use `@dnd-kit` for drag-and-drop (lightweight, accessible, works on mobile):

```typescript
// apps/web/src/components/kanban-board.tsx
import { DndContext, DragOverlay, closestCorners } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';

export function KanbanBoard({ pipelineId }: { pipelineId: string }) {
  const { data: board } = trpc.pipelines.getBoard.useQuery({ id: pipelineId });
  const moveCard = trpc.pipelines.moveCard.useMutation({
    onSuccess: () => queryClient.invalidateQueries(['pipelines', pipelineId]),
  });

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;

    moveCard.mutate({
      cardId: active.id as string,
      stage: over.data.current?.stage,
      position: over.data.current?.position ?? 0,
    });
  }

  return (
    <DndContext collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto p-4">
        {board?.stages.map(stage => (
          <KanbanColumn key={stage.name} stage={stage} />
        ))}
      </div>
    </DndContext>
  );
}
```

### Card Component

Each card shows a compact view of the object/entity:
- Title (truncated)
- Type badge (paper/patent/person/org)
- Top 3 score badges
- Assignee avatar (if set)
- Click → navigate to detail page

## Sprint 13: Triggers

### Trigger Definition

Triggers are stored as JSON in the pipeline record:

```typescript
interface TriggerRule {
  dimensionId: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq';
  threshold: number;
  targetStage: string;  // which stage the card enters
}
```

### Trigger UI

On the pipeline settings form:
- "Add trigger" button
- Dimension dropdown (from workspace dimensions)
- Operator dropdown (>, >=, <, =)
- Threshold number input
- Target stage dropdown (from pipeline stages)
- Multiple triggers allowed (OR logic: any trigger fires → card created)

### Trigger Evaluation Worker

See `../engineering/ENGINES.md` section 4 for full implementation.

Triggered by `scores.folded` events (after fold-up completes).

### Verification Checklist
- [ ] Create pipeline with custom stages
- [ ] Drag cards between stages (persists)
- [ ] Add card from object/entity detail page
- [ ] Configure trigger: dimension > threshold → stage
- [ ] Paper scored above threshold → card auto-created
- [ ] In-app notification on auto-card creation
- [ ] Mobile: pipeline board scrolls horizontally
