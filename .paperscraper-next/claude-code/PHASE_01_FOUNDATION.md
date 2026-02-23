# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 1: Foundation

## Goal
Working Turborepo monorepo with PostgreSQL + pgvector, Redis, Better Auth, and first tRPC endpoint.

## Sprint 1: Monorepo + Database

### Step 1: Initialize Monorepo

```bash
mkdir paper-scraper-next && cd paper-scraper-next
pnpm init
```

Create `pnpm-workspace.yaml`:
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'plugins/*'
```

Create `turbo.json`:
```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "dev": { "cache": false, "persistent": true },
    "lint": {},
    "test": {},
    "db:push": { "cache": false },
    "db:generate": { "outputs": ["node_modules/.prisma/**"] }
  }
}
```

### Step 2: Create Package Scaffolds

```
packages/shared/        → Types, Zod schemas, constants
packages/db/            → Prisma schema, migrations, seed
packages/plugin-sdk/    → Plugin type definitions
apps/api/               → Bun + tRPC server
apps/web/               → TanStack Start (empty shell for now)
apps/jobs/              → BullMQ workers (empty shell for now)
```

Each package needs:
- `package.json` with name `@ps/<name>`
- `tsconfig.json` extending root config
- `src/index.ts` as entry point

### Step 3: Prisma Schema

Create `packages/db/prisma/schema.prisma` with the FULL schema from `../engineering/DATA_MODEL.md`. All 12 tables.

Key: Prisma can't handle pgvector natively. The embedding columns will be added via a raw SQL migration after `prisma db push`.

### Step 4: Raw SQL Migration for pgvector

Create `packages/db/prisma/migrations/001_pgvector.sql`:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE "ResearchObject" ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE "Entity" ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS idx_objects_embedding ON "ResearchObject"
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_entities_embedding ON "Entity"
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_objects_fts ON "ResearchObject"
  USING GIN (to_tsvector('english', title || ' ' || COALESCE(content, '')));

CREATE INDEX IF NOT EXISTS idx_objects_metadata ON "ResearchObject" USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_entities_metadata ON "Entity" USING GIN (metadata);
```

### Step 5: Docker Compose

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: paperscraper
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - '5432:5432'
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'

volumes:
  pgdata:
```

### Step 6: Seed Script

`packages/db/src/seed.ts`:
- Create a test workspace
- Create an admin user
- Verify all tables exist

### Verification
```bash
docker-compose up -d
pnpm --filter @ps/db db:push
pnpm --filter @ps/db db:seed
# Should: create tables, insert test data, no errors
```

---

## Sprint 2: API + Auth

### Step 1: Bun + tRPC Server

`apps/api/src/index.ts`:
```typescript
import { Hono } from 'hono';
import { trpcServer } from '@hono/trpc-server';
import { appRouter } from './routers';
import { createContext } from './context';

const app = new Hono();

app.use('/trpc/*', trpcServer({ router: appRouter, createContext }));
app.get('/health', async (c) => {
  // Check DB + Redis connectivity
  return c.json({ status: 'ok', db: true, redis: true });
});

export default { port: 3001, fetch: app.fetch };
```

Use Hono as the HTTP layer (lighter than Express, works natively with Bun).

### Step 2: tRPC Setup

`apps/api/src/trpc.ts`:
```typescript
import { initTRPC, TRPCError } from '@trpc/server';
import { type Context } from './context';

const t = initTRPC.context<Context>().create();

export const router = t.router;
export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(async ({ ctx, next }) => {
  if (!ctx.user) throw new TRPCError({ code: 'UNAUTHORIZED' });
  if (!ctx.workspaceId) throw new TRPCError({ code: 'FORBIDDEN' });
  return next({ ctx: { ...ctx, user: ctx.user, workspaceId: ctx.workspaceId } });
});
```

### Step 3: Better Auth Integration

```typescript
// apps/api/src/auth.ts
import { betterAuth } from 'better-auth';
import { prismaAdapter } from 'better-auth/adapters/prisma';
import { db } from '@ps/db';

export const auth = betterAuth({
  database: prismaAdapter(db),
  emailAndPassword: { enabled: true },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    },
  },
  session: {
    cookieCache: { enabled: true, maxAge: 60 * 5 }, // 5 min cache
  },
});
```

### Step 4: Workspace Middleware

The context creator extracts user from Better Auth session, then looks up their workspace:

```typescript
// apps/api/src/context.ts
export async function createContext({ req }: { req: Request }) {
  const session = await auth.api.getSession({ headers: req.headers });
  if (!session?.user) return { user: null, workspaceId: null, db };

  const user = await db.user.findUnique({
    where: { email: session.user.email },
    select: { id: true, workspaceId: true, role: true },
  });

  return { user, workspaceId: user?.workspaceId ?? null, db };
}
```

### Step 5: First Router

```typescript
// apps/api/src/routers/workspaces.ts
export const workspacesRouter = router({
  get: protectedProcedure.query(async ({ ctx }) => {
    return ctx.db.workspace.findUniqueOrThrow({
      where: { id: ctx.workspaceId },
    });
  }),
});
```

### Step 6: Rate Limiting

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '1 m'),
});

// Apply as middleware in Hono
app.use('*', async (c, next) => {
  const ip = c.req.header('x-forwarded-for') || 'unknown';
  const { success } = await ratelimit.limit(ip);
  if (!success) return c.json({ error: 'Rate limited' }, 429);
  return next();
});
```

### Verification
```bash
pnpm --filter @ps/api dev
# POST /auth/sign-up with email/password → creates user
# GET /trpc/workspaces.get with session cookie → returns workspace
# GET /health → { status: 'ok' }
```
