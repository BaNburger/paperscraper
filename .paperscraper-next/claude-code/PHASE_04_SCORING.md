# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 4: Scoring Engine

## Goal
User-defined dimensions with custom prompts, LLM scoring with structured output, fold-up aggregation from objects to entities.

## Sprint 7: Dimensions + Object Scoring

### Dimension CRUD

```typescript
// apps/api/src/routers/dimensions.ts
export const dimensionsRouter = router({
  list: protectedProcedure.query(async ({ ctx }) => {
    return ctx.db.dimension.findMany({
      where: { workspaceId: ctx.workspaceId },
      orderBy: { createdAt: 'desc' },
    });
  }),

  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1).max(100),
      description: z.string().optional(),
      prompt: z.string().min(10),  // LLM prompt template
      appliesTo: z.array(z.enum(['object', 'entity'])).default(['object']),
      config: z.object({
        minScore: z.number().default(0),
        maxScore: z.number().default(10),
        provider: z.string().optional(), // override workspace default
      }).default({}),
    }))
    .mutation(async ({ ctx, input }) => {
      const dimension = await ctx.db.dimension.create({
        data: { ...input, workspaceId: ctx.workspaceId },
      });

      // Backfill: queue scoring for all existing objects
      const objects = await ctx.db.researchObject.findMany({
        where: { workspaceId: ctx.workspaceId, embedding: { not: null } },
        select: { id: true },
      });

      for (const obj of objects) {
        await scoringQueue.add('score-object', {
          objectId: obj.id,
          dimensionId: dimension.id,
          workspaceId: ctx.workspaceId,
        }, { priority: 10 }); // Lower priority than new ingestions
      }

      return dimension;
    }),
});
```

### Scoring Worker

Full implementation in `../engineering/ENGINES.md` section 3.

Key points:
- Use Vercel AI SDK `generateObject()` for structured output (Zod schema → guaranteed JSON)
- Prompt template rendering with `{{placeholders}}`
- Prompt caching: dimension prompt is reused across all objects (90% token discount)
- BYOK: decrypt workspace API key at runtime, pass to AI SDK

### Prompt Template Rendering

```typescript
// apps/api/src/engines/scoring/template.ts
export function renderTemplate(
  template: string,
  context: Record<string, unknown>,
): string {
  return template.replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (_, path) => {
    const value = path.split('.').reduce(
      (obj: any, key: string) => obj?.[key],
      context,
    );
    return value != null ? String(value) : '';
  });
}
```

### BYOK Key Management

```typescript
// apps/api/src/engines/scoring/keys.ts
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

const ENCRYPTION_KEY = Buffer.from(process.env.ENCRYPTION_KEY!, 'hex'); // 32 bytes

export async function encryptApiKey(plainKey: string): Promise<string> {
  const iv = randomBytes(16);
  const cipher = createCipheriv('aes-256-cbc', ENCRYPTION_KEY, iv);
  const encrypted = Buffer.concat([cipher.update(plainKey), cipher.final()]);
  return `enc:v1:${iv.toString('hex')}:${encrypted.toString('hex')}`;
}

export async function decryptApiKey(encryptedKey: string): Promise<string> {
  const [, , ivHex, dataHex] = encryptedKey.split(':');
  const decipher = createDecipheriv('aes-256-cbc', ENCRYPTION_KEY, Buffer.from(ivHex, 'hex'));
  const decrypted = Buffer.concat([decipher.update(Buffer.from(dataHex, 'hex')), decipher.final()]);
  return decrypted.toString();
}
```

## Sprint 8: Fold-Up Aggregation

### Fold-Up Worker

Full implementation in `../engineering/ENGINES.md` section 3.

Key: exponential recency weighting:
```typescript
const weight = Math.exp(-ageInDays / 365); // Half-life ~1 year
```

### BullMQ Job Chain

```
score-object job completes
  → emits score.created
  → fold-entity job per related author
    → fold-entity job completes
    → emits scores.folded
    → check-triggers job
```

Configure with BullMQ flow producer for dependency tracking:

```typescript
// apps/jobs/src/flows/scoring-flow.ts
import { FlowProducer } from 'bullmq';

const flowProducer = new FlowProducer({ connection: redis });

export async function queueScoringFlow(
  objectId: string,
  dimensionId: string,
  workspaceId: string,
  relatedEntityIds: string[],
) {
  await flowProducer.add({
    name: 'check-triggers',
    queueName: 'triggers',
    data: { workspaceId },
    children: relatedEntityIds.map(entityId => ({
      name: 'fold-entity',
      queueName: 'fold-up',
      data: { entityId, dimensionId, workspaceId },
      children: [{
        name: 'score-object',
        queueName: 'scoring',
        data: { objectId, dimensionId, workspaceId },
      }],
    })),
  });
}
```

### Verification Checklist
- [ ] Create dimension with custom prompt
- [ ] Existing objects queued for backfill scoring
- [ ] New objects auto-scored on all dimensions
- [ ] Scores stored with value + explanation
- [ ] Author entity scores = weighted average of their papers
- [ ] Organization entity scores = average of their members
- [ ] Trigger check runs after fold-up completes
- [ ] BYOK: scoring uses workspace's encrypted API key
