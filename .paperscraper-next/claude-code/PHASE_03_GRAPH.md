# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 3: Graph Engine

## Goal
Entity resolution (authors + organizations), relationship inference, embedding generation.

## Sprint 5: Entity Resolution

### Resolve Entities Worker

Triggered by `resolve-entities` events from ingestion:

```typescript
// apps/jobs/src/workers/graph.ts
export const graphWorker = new Worker('graph', async (job) => {
  const { objectId, workspaceId, entities } = job.data;

  const resolvedEntityIds: string[] = [];

  for (const entity of entities) {
    const entityId = await resolveEntity(db, workspaceId, entity);
    resolvedEntityIds.push(entityId);

    // Link object to entity
    await db.objectEntity.upsert({
      where: {
        objectId_entityId_role: {
          objectId,
          entityId,
          role: entity.role,
        },
      },
      update: { position: entity.metadata?.position as number | undefined },
      create: {
        objectId,
        entityId,
        role: entity.role,
        position: entity.metadata?.position as number | undefined,
      },
    });
  }

  // Infer relationships between resolved entities
  await inferRelationships(db, objectId, resolvedEntityIds);

  // Queue embedding generation
  await embeddingQueue.add('embed-object', { objectId, workspaceId });

  return { entitiesResolved: resolvedEntityIds.length };
}, { connection: redis, concurrency: 10 });
```

### Entity Resolution Function

See `../engineering/ENGINES.md` section 2 for the full `resolveEntity()` implementation.

Key implementation notes:
- **Jaro-Winkler** for name similarity: `import { jaroWinkler } from 'string-similarity-js'`
- **Confidence threshold**: 0.85 for auto-merge, below that create new entity
- **Metadata merging**: on match, merge new metadata without overwriting existing (ORCID, affiliation, etc.)
- **Idempotency**: if the exact same entity is resolved again, return existing ID

### Relationship Inference

```typescript
// Co-authorship: all person entities on the same object are collaborators
// Affiliation: person entities with matching institution metadata → member_of
// See ../engineering/ENGINES.md for full implementation
```

## Sprint 6: Embeddings

### Embedding Worker

```typescript
// apps/jobs/src/workers/embedding.ts
import { embed } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';

export const embeddingWorker = new Worker('embedding', async (job) => {
  const { objectId, workspaceId } = job.data;

  // Load object
  const object = await db.researchObject.findUniqueOrThrow({
    where: { id: objectId },
  });

  // Load workspace API key
  const apiKey = await loadDecryptedApiKey(workspaceId, 'openai');
  if (!apiKey) {
    job.log('No API key configured, skipping embedding');
    return;
  }

  // Generate embedding
  const model = createOpenAI({ apiKey });
  const { embedding } = await embed({
    model: model.embedding('text-embedding-3-small'),
    value: `${object.title}\n\n${object.content || ''}`,
  });

  // Store via raw SQL (Prisma can't handle vector type)
  await db.$executeRaw`
    UPDATE "ResearchObject"
    SET embedding = ${embedding}::vector
    WHERE id = ${objectId}
  `;

  // Queue scoring if dimensions exist
  const dimensions = await db.dimension.findMany({
    where: { workspaceId, appliesTo: { has: 'object' } },
  });

  for (const dim of dimensions) {
    await scoringQueue.add('score-object', {
      objectId,
      dimensionId: dim.id,
      workspaceId,
    });
  }
}, { connection: redis, concurrency: 20 });
```

### Vector Store Abstraction

```typescript
// packages/shared/src/vector-store.ts
export interface VectorStore {
  upsert(id: string, embedding: number[], metadata?: Record<string, unknown>): Promise<void>;
  search(query: number[], filter: VectorFilter, limit: number): Promise<VectorResult[]>;
  delete(id: string): Promise<void>;
}

// apps/api/src/engines/query/pg-vector-store.ts
export class PgVectorStore implements VectorStore {
  constructor(private db: PrismaClient) {}

  async search(query: number[], filter: VectorFilter, limit: number) {
    // Use tenantQuery() wrapper — never db.$queryRaw directly
    return tenantQuery(this.db, filter.workspaceId, Prisma.sql`
      SELECT id, 1 - (embedding <=> ${query}::vector) as score
      FROM "ResearchObject"
      WHERE "workspaceId" = ${filter.workspaceId}
        ${filter.type ? Prisma.sql`AND type = ${filter.type}` : Prisma.empty}
      ORDER BY embedding <=> ${query}::vector
      LIMIT ${limit}
    `);
  }

  // ... upsert, delete implementations
}
```

### Verification Checklist
- [ ] Papers ingested → authors automatically resolved to Entity records
- [ ] Same author across papers resolved to single Entity (ORCID match)
- [ ] Co-authorship relationships created in entity_relations
- [ ] Embeddings generated and stored in pgvector column
- [ ] Vector similarity search returns relevant results
- [ ] Scoring jobs queued after embedding generation
