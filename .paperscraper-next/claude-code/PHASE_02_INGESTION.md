# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 2: Ingestion Engine

## Goal
Users can create streams, trigger OpenAlex ingestion, and see research objects stored in the database.

## Sprint 3: Stream Management

### tRPC Routes

```typescript
// apps/api/src/routers/streams.ts
export const streamsRouter = router({
  list: protectedProcedure.query(async ({ ctx }) => {
    return ctx.db.stream.findMany({
      where: { workspaceId: ctx.workspaceId },
      orderBy: { createdAt: 'desc' },
    });
  }),

  create: protectedProcedure
    .input(z.object({
      name: z.string().min(1).max(100),
      sourceType: z.string(), // 'openalex' | 'webhook' | ...
      config: z.record(z.unknown()),
      schedule: z.string().optional(), // cron expression
    }))
    .mutation(async ({ ctx, input }) => {
      const stream = await ctx.db.stream.create({
        data: { ...input, workspaceId: ctx.workspaceId },
      });

      // If scheduled, create BullMQ repeatable job
      if (input.schedule) {
        await ingestionQueue.add('fetch-stream', { streamId: stream.id }, {
          repeat: { pattern: input.schedule },
        });
      }

      return stream;
    }),

  trigger: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      // Verify ownership
      const stream = await ctx.db.stream.findFirstOrThrow({
        where: { id: input.id, workspaceId: ctx.workspaceId },
      });

      // Queue immediate run
      await ingestionQueue.add('fetch-stream', { streamId: stream.id });

      return { status: 'queued' };
    }),
});
```

### Source Adapter Interface

```typescript
// packages/shared/src/types/source-adapter.ts
// (Already defined in engineering/ENGINES.md — copy those types here)
```

### Webhook Dispatcher

For external plugins, the ingestion engine POSTs to the plugin URL:

```typescript
// apps/api/src/engines/ingestion/webhook.ts
export async function callSourcePlugin(
  plugin: PluginRegistration,
  config: SourceConfig,
): Promise<SourceResult> {
  const payload = JSON.stringify(config);
  const signature = computeHmac(payload, plugin.auth.credentials);

  const response = await fetch(`${plugin.url}/fetch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-PS-Signature': signature,
    },
    body: payload,
    signal: AbortSignal.timeout(30_000), // 30s timeout
  });

  if (!response.ok) throw new Error(`Plugin error: ${response.status}`);

  const data = await response.json();
  return sourceResultSchema.parse(data); // Zod validation
}
```

## Sprint 4: OpenAlex Adapter + Object Storage

### OpenAlex Adapter

```typescript
// plugins/openalex/src/index.ts
import type { SourceAdapter, SourceConfig, SourceResult } from '@ps/shared';

const OPENALEX_API = 'https://api.openalex.org';

export const openAlexAdapter: SourceAdapter = {
  async fetch(config: SourceConfig): Promise<SourceResult> {
    const { query, filters, institutionId } = config.config as OpenAlexConfig;

    // Build OpenAlex URL
    let url = `${OPENALEX_API}/works?filter=`;
    const filterParts: string[] = [];

    if (query) filterParts.push(`title_and_abstract.search:${query}`);
    if (institutionId) filterParts.push(`authorships.institutions.id:${institutionId}`);
    if (config.lastRunAt) filterParts.push(`from_created_date:${config.lastRunAt.split('T')[0]}`);

    url += filterParts.join(',');
    url += '&per_page=100&sort=created_date:desc';
    url += '&select=id,doi,title,abstract_inverted_index,publication_year,cited_by_count,type,open_access,authorships,primary_location';

    const response = await fetch(url, {
      headers: { 'User-Agent': 'PaperScraper/2.0 (mailto:contact@paperscraper.ai)' },
    });

    if (!response.ok) throw new Error(`OpenAlex API error: ${response.status}`);
    const data = await response.json();

    return {
      objects: data.results.map(normalizeOpenAlexWork),
      cursor: data.meta?.next_cursor,
      hasMore: data.results.length === 100,
    };
  },
};

function normalizeOpenAlexWork(work: OpenAlexWork): NormalizedObject {
  return {
    externalId: work.doi || work.id,
    type: 'paper',
    title: work.title || 'Untitled',
    content: work.abstract_inverted_index
      ? invertedIndexToText(work.abstract_inverted_index)
      : undefined,
    metadata: {
      year: work.publication_year,
      citationCount: work.cited_by_count,
      venue: work.primary_location?.source?.display_name,
      openAccess: work.open_access?.is_oa,
      paperType: work.type,
      openAlexId: work.id,
    },
    entities: [
      ...work.authorships.map((a, i) => ({
        name: a.author.display_name,
        type: 'person' as const,
        role: 'author',
        metadata: {
          orcid: a.author.orcid?.replace('https://orcid.org/', ''),
          openAlexId: a.author.id,
          position: i,
          isCorresponding: a.is_corresponding,
          affiliation: a.institutions?.[0]?.display_name,
          affiliationId: a.institutions?.[0]?.id,
        },
      })),
      // Extract unique institutions as organization entities
      ...extractUniqueInstitutions(work.authorships),
    ],
  };
}

function invertedIndexToText(index: Record<string, number[]>): string {
  const words: [number, string][] = [];
  for (const [word, positions] of Object.entries(index)) {
    for (const pos of positions) {
      words.push([pos, word]);
    }
  }
  return words.sort((a, b) => a[0] - b[0]).map(w => w[1]).join(' ');
}
```

### Ingestion Worker

```typescript
// apps/jobs/src/workers/ingestion.ts
import { Worker } from 'bullmq';
import { openAlexAdapter } from '@ps/plugins-openalex';

export const ingestionWorker = new Worker('ingestion', async (job) => {
  const { streamId } = job.data;

  // Load stream config
  const stream = await db.stream.findUniqueOrThrow({ where: { id: streamId } });

  // Select adapter based on source type
  const adapter = getAdapter(stream.sourceType); // openAlexAdapter for 'openalex'

  // Fetch objects
  const result = await adapter.fetch({
    streamId: stream.id,
    workspaceId: stream.workspaceId,
    config: stream.config as Record<string, unknown>,
    lastRunAt: stream.lastRunAt?.toISOString() ?? null,
  });

  // Store objects (batch upsert)
  let created = 0;
  for (const obj of result.objects) {
    const stored = await db.researchObject.upsert({
      where: {
        workspaceId_externalId: {
          workspaceId: stream.workspaceId,
          externalId: obj.externalId,
        },
      },
      update: {
        metadata: obj.metadata,
        content: obj.content,
        ingestedAt: new Date(),
      },
      create: {
        workspaceId: stream.workspaceId,
        type: obj.type,
        externalId: obj.externalId,
        source: stream.sourceType,
        title: obj.title,
        content: obj.content,
        metadata: obj.metadata,
      },
    });

    // Emit event for graph engine + scoring engine
    await graphQueue.add('resolve-entities', {
      objectId: stored.id,
      workspaceId: stream.workspaceId,
      entities: obj.entities || [],
    });

    created++;
  }

  // Update stream last run
  await db.stream.update({
    where: { id: streamId },
    data: { lastRunAt: new Date() },
  });

  return { objectsProcessed: created };
}, { connection: redis, concurrency: 5 });
```

### Verification Checklist
- [ ] Create stream via tRPC with OpenAlex config
- [ ] Trigger stream → papers appear in ResearchObject table
- [ ] Dedup works: trigger again → no duplicates
- [ ] `object.created` events emitted to graph queue
- [ ] Stream lastRunAt updated after run
