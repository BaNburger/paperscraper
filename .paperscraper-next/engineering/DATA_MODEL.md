# Data Model (Stage 1 Minimal, Stage 2 Extensions)

## Stage 1 Database Contract

Stage 1 uses a minimal schema to support only the 10x loop.

### 1. `streams`

```prisma
model Stream {
  id         String   @id @default(uuid())
  name       String
  sourceType String   // openalex only in Stage 1
  config     Json
  isActive   Boolean  @default(true)
  lastRunAt  DateTime?
  createdAt  DateTime @default(now())

  runs StreamRun[]
}
```

### 2. `stream_runs`

```prisma
model StreamRun {
  id        String   @id @default(uuid())
  streamId  String
  status    String   // queued | running | succeeded | failed
  startedAt DateTime?
  endedAt   DateTime?
  stats     Json     @default("{}")
  error     String?
  cursor    String?
  createdAt DateTime @default(now())

  stream Stream @relation(fields: [streamId], references: [id], onDelete: Cascade)

  @@index([streamId, createdAt(sort: Desc)])
}
```

### 3. `research_objects`

```prisma
model ResearchObject {
  id         String   @id @default(uuid())
  externalId String
  source     String   // openalex
  type       String   // paper
  title      String
  content    String?
  metadata   Json     @default("{}")
  createdAt  DateTime @default(now())
  ingestedAt DateTime @default(now())

  objectEntities ObjectEntity[]
  objectScores   ObjectScore[]
  pipelineCards  ObjectPipelineCard[]

  @@unique([externalId, source])
  @@index([createdAt(sort: Desc)])
}
```

### 4. `entities`

```prisma
model Entity {
  id        String   @id @default(uuid())
  type      String   // person | organization
  name      String
  metadata  Json     @default("{}")
  createdAt DateTime @default(now())

  objectEntities ObjectEntity[]
  entityScores   EntityScore[]

  @@index([type, name])
}
```

### 5. `object_entities`

```prisma
model ObjectEntity {
  objectId String
  entityId String
  role     String  // author | affiliation
  position Int?

  object ResearchObject @relation(fields: [objectId], references: [id], onDelete: Cascade)
  entity Entity         @relation(fields: [entityId], references: [id], onDelete: Cascade)

  @@id([objectId, entityId, role])
}
```

### 6. `dimensions`

```prisma
model Dimension {
  id          String   @id @default(uuid())
  name        String
  description String?
  prompt      String
  config      Json     @default("{}")
  isActive    Boolean  @default(true)
  createdAt   DateTime @default(now())

  objectScores ObjectScore[]
  entityScores EntityScore[]
}
```

### 7. `object_scores`

```prisma
model ObjectScore {
  id          String   @id @default(uuid())
  dimensionId String
  objectId    String
  value       Float
  explanation String?
  metadata    Json     @default("{}")
  scoredAt    DateTime @default(now())

  dimension Dimension      @relation(fields: [dimensionId], references: [id], onDelete: Cascade)
  object    ResearchObject @relation(fields: [objectId], references: [id], onDelete: Cascade)

  @@unique([dimensionId, objectId])
  @@index([objectId])
}
```

### 8. `entity_scores`

```prisma
model EntityScore {
  id          String   @id @default(uuid())
  dimensionId String
  entityId    String
  value       Float
  metadata    Json     @default("{}")
  scoredAt    DateTime @default(now())

  dimension Dimension @relation(fields: [dimensionId], references: [id], onDelete: Cascade)
  entity    Entity    @relation(fields: [entityId], references: [id], onDelete: Cascade)

  @@unique([dimensionId, entityId])
  @@index([entityId])
}
```

### 9. `pipelines`

```prisma
model Pipeline {
  id        String   @id @default(uuid())
  name      String
  createdAt DateTime @default(now())

  stages PipelineStage[]
  cards  ObjectPipelineCard[]
}
```

### 10. `pipeline_stages`

```prisma
model PipelineStage {
  id         String   @id @default(uuid())
  pipelineId String
  name       String
  sortOrder  Int
  color      String?

  pipeline Pipeline @relation(fields: [pipelineId], references: [id], onDelete: Cascade)

  @@unique([pipelineId, name])
  @@index([pipelineId, sortOrder])
}
```

### 11. `object_pipeline_cards`

```prisma
model ObjectPipelineCard {
  id         String   @id @default(uuid())
  pipelineId String
  objectId   String
  stageId    String
  position   Int      @default(0)
  metadata   Json     @default("{}")
  enteredAt  DateTime @default(now())

  pipeline Pipeline      @relation(fields: [pipelineId], references: [id], onDelete: Cascade)
  object   ResearchObject @relation(fields: [objectId], references: [id], onDelete: Cascade)
  stage    PipelineStage  @relation(fields: [stageId], references: [id], onDelete: Restrict)

  @@unique([pipelineId, objectId])
  @@index([pipelineId, stageId, position])
}
```

### 12. `api_keys`

```prisma
model ApiKey {
  id           String   @id @default(uuid())
  provider     String   // openai | anthropic
  encryptedKey String   // enc:v1:...
  label        String?
  createdAt    DateTime @default(now())
}
```

## Stage 1 SQL Additions

```sql
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE "ResearchObject" ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS idx_objects_embedding_hnsw
  ON "ResearchObject" USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_objects_fts
  ON "ResearchObject"
  USING GIN (to_tsvector('english', title || ' ' || COALESCE(content, '')));
```

Stage 1 does not require vector search queries, but the column/index are allowed for later expansion.

## Stage 2 Additions (Deferred)

1. `workspaces`, `users`, role bindings
2. RLS policies and tenant-aware indexes
3. `entity_pipeline_cards` for non-object pipeline targets
4. `views` for saved filters/layouts
5. `audit_logs` for mutation history
6. `plugin_registrations`, `plugin_runs` for extensibility
7. `trigger_rules` and trigger execution tracking

## Data Integrity Rules

1. Use split score tables (`object_scores`, `entity_scores`) to avoid polymorphic FK gaps.
2. Use split pipeline card tables to preserve strict referential integrity.
3. Keep ingestion idempotent through unique external keys.
4. Never overload Stage 1 schema with deferred Stage 2 concerns.
