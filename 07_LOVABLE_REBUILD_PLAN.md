# Paper Scraper Love - State-of-the-Art Rebuild Plan

## Executive Summary

This plan outlines a comprehensive rebuild of the Research Paper Analysis and Technology Transfer Platform using modern architectural patterns, state-of-the-art tooling, and industry best practices.

**Current State:** React 18 SPA with Supabase, 80+ components, 18 pages, no tests, mixed mock/real data, type safety gaps
**Target State:** Production-ready, type-safe, tested, scalable monorepo with feature-based architecture

**Timeline:** 20 weeks (5 months)

---

## Recommended Tech Stack

### Keep (Already Good Choices)
| Technology | Reason |
|------------|--------|
| React 18 | Stable, excellent ecosystem, team familiar |
| TypeScript | Already adopted, enable stricter settings |
| Vite | Fast DX, great plugins |
| Tailwind CSS | Utility-first, already invested |
| shadcn/ui | Accessible components, already used |
| Supabase | Good PostgreSQL BaaS, keep |
| React Query (TanStack) | Good server state, enhance config |

### Upgrade/Add
| Technology | Replaces | Justification |
|------------|----------|---------------|
| **Drizzle ORM** | Direct Supabase calls | Type-safe queries, schema-as-code, edge-ready, smaller than Prisma |
| **Zustand** | Context API | Minimal boilerplate, great TS support, devtools, ~1KB |
| **Zod** (everywhere) | Partial validation | Runtime validation + TS inference |
| **Biome** | ESLint + Prettier | 10-100x faster, single tool |
| **Vitest** | None | Fast, Vite-native, Jest-compatible |
| **Playwright** | None | E2E tests, cross-browser |
| **MSW** | Mock data files | Request interception, works with all tests |
| **Storybook** | None | Component development, documentation |
| **Sentry** | None | Error tracking, session replay |
| **Vercel AI SDK** | None | Provider-agnostic LLM abstraction |
| **Turborepo** | Single repo | Monorepo caching, parallel builds |

---

## New Folder Structure

```
paper-scraper-v2/
├── .github/workflows/           # CI/CD pipelines
├── .storybook/                  # Storybook config
├── apps/
│   └── web/                     # Main web application
│       └── src/
│           ├── app/             # Entry, providers, routes
│           │   ├── providers/   # QueryProvider, ThemeProvider
│           │   ├── routes/      # Route definitions, guards
│           │   └── App.tsx
│           │
│           ├── features/        # Feature-based modules (vertical slices)
│           │   ├── papers/
│           │   │   ├── api/     # queries.ts, mutations.ts, keys.ts
│           │   │   ├── components/
│           │   │   │   ├── PaperCard/
│           │   │   │   │   ├── PaperCard.tsx
│           │   │   │   │   ├── PaperCard.test.tsx
│           │   │   │   │   └── PaperCard.stories.tsx
│           │   │   │   └── InnovationRadar/
│           │   │   ├── hooks/
│           │   │   ├── stores/  # Zustand stores
│           │   │   ├── types/
│           │   │   └── index.ts # Public API exports
│           │   │
│           │   ├── kanban/
│           │   ├── researchers/
│           │   ├── transfer/
│           │   ├── reports/
│           │   ├── alerts/
│           │   ├── search/
│           │   ├── settings/
│           │   └── auth/
│           │
│           ├── pages/           # Thin page components
│           │   ├── dashboard/
│           │   ├── papers/
│           │   └── ...
│           │
│           ├── shared/          # Shared utilities
│           │   ├── components/  # ErrorBoundary, DataTable
│           │   ├── hooks/       # useDebounce, useKeyboardShortcuts
│           │   ├── lib/         # api-client, supabase, utils
│           │   └── stores/      # uiStore, userStore
│           │
│           └── config/          # env.ts, constants.ts, featureFlags.ts
│
├── packages/                    # Shared packages
│   ├── ui/                      # shadcn/ui components
│   ├── database/                # Drizzle schema, migrations
│   ├── validators/              # Zod schemas
│   └── config/                  # Shared ESLint, TS, Tailwind configs
│
├── supabase/                    # Edge functions, migrations
├── e2e/                         # Playwright tests
├── docs/                        # Architecture docs
├── turbo.json
└── pnpm-workspace.yaml
```

---

## Implementation Phases

### Phase 0: Foundation Setup (Week 1-2)
**Complexity: Medium | Risk: Low**

**Tasks:**
1. Initialize Turborepo with pnpm workspaces
2. Set up Biome for linting/formatting
3. Configure Husky + lint-staged for pre-commit hooks
4. Set up GitHub Actions CI pipeline
5. Configure TypeScript strict mode (`strict: true`, `noUncheckedIndexedAccess`)
6. Initialize Storybook
7. Create shared package structure

**Deliverables:**
- Working monorepo build system
- CI pipeline on PRs
- Pre-commit quality gates

**Key Files to Create:**
- `turbo.json`
- `pnpm-workspace.yaml`
- `packages/config/typescript/tsconfig.base.json`
- `.github/workflows/ci.yml`

---

### Phase 1: Type Safety Foundation (Week 3-4)
**Complexity: High | Risk: Medium**

**Tasks:**
1. Set up Drizzle ORM with Supabase connection
2. Create typed schema from existing 18 tables:
   ```typescript
   // packages/database/src/schema/papers.ts
   export const papers = pgTable('papers', {
     id: uuid('id').primaryKey().defaultRandom(),
     title: text('title').notNull(),
     noveltyScore: numeric('novelty_score').notNull(),
     status: text('status').default('new'),
     // ... all fields
   });
   ```
3. Create Zod schemas for all domain objects:
   ```typescript
   // packages/validators/src/paper.ts
   export const paperSchema = z.object({
     id: z.string().uuid(),
     title: z.string().min(1),
     noveltyScore: z.number().min(0).max(1),
     status: paperStatusSchema,
   });
   export type Paper = z.infer<typeof paperSchema>;
   ```
4. Create type-safe API client wrapper
5. Eliminate all `any` types (currently in `paperService.ts:14`, `sortPapers:409`)

**Deliverables:**
- Drizzle schema for all 18 tables
- Zod schemas for all domain types
- Zero `any` types

**Critical Files to Migrate:**
- `/src/services/papers/paperService.ts` (remove `any` at line 14)
- `/src/types/supabase.ts` (convert to Drizzle)

---

### Phase 2: State Management Refactor (Week 5-6)
**Complexity: Medium | Risk: Medium**

**Tasks:**
1. Create Zustand stores for client state:
   ```typescript
   // apps/web/src/shared/stores/uiStore.ts
   export const useUIStore = create<UIState>()(
     devtools(persist((set) => ({
       sidebarOpen: true,
       commandMenuOpen: false,
       toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
     }), { name: 'ui-storage' }))
   );
   ```
2. Configure TanStack Query with proper defaults:
   ```typescript
   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 1000 * 60 * 5,  // 5 min
         gcTime: 1000 * 60 * 30,    // 30 min
         retry: 2,
         refetchOnWindowFocus: false,
       },
     },
   });
   ```
3. Implement optimistic updates for paper status changes
4. Remove `AppContext` (migrate to Zustand)
5. Create feature-specific stores where needed

**Deliverables:**
- Zustand stores for all client state
- Enhanced React Query config
- Optimistic update patterns

**Critical Files to Migrate:**
- `/src/context/AppContext.tsx` → Zustand stores
- `/src/App.tsx` → New provider hierarchy

---

### Phase 3: Feature Module Migration (Week 7-10)
**Complexity: High | Risk: Medium**

**Week 7-8: Core Features**
1. **Papers Feature** (`/features/papers/`)
   - Migrate 15+ paper components
   - Create API hooks with React Query
   - Add error boundaries
   - Write component tests (target: 70% coverage)

2. **Kanban Feature** (`/features/kanban/`)
   - Extract from `/pages/kanban/`
   - Improve drag-drop performance
   - Add keyboard navigation

**Week 9-10: Secondary Features**
3. Researchers feature (profiles, groups, collaborators)
4. Transfer/Messaging feature (conversations, stages)
5. Alerts feature (timeline, settings)
6. Settings features (user, org, model, repository, developer)

**Feature Module Structure:**
```typescript
// features/papers/index.ts - Public API
export { PaperCard, PaperGrid, InnovationRadar } from './components';
export { usePapers, usePaper } from './hooks';
export { useUpdatePaperStatus } from './api/mutations';
export type { Paper, PaperStatus } from './types';
```

**Deliverables:**
- All features in new structure
- Zero mock data in production
- Error boundaries on all features
- 70%+ component test coverage

---

### Phase 4: Testing Infrastructure (Week 11-12)
**Complexity: Medium | Risk: Low**

**Tasks:**
1. Set up Vitest with coverage:
   ```typescript
   // vite.config.ts
   test: {
     globals: true,
     environment: 'jsdom',
     coverage: { provider: 'v8', reporter: ['text', 'html'] },
   }
   ```
2. Set up MSW for API mocking
3. Create test factories with Fishery:
   ```typescript
   export const paperFactory = Factory.define<Paper>(() => ({
     id: faker.string.uuid(),
     title: faker.lorem.sentence(),
     noveltyScore: faker.number.float({ min: 0, max: 1 }),
   }));
   ```
4. Set up Playwright for E2E
5. Add visual regression testing

**Deliverables:**
- Unit test coverage > 80%
- Integration test coverage > 70%
- E2E tests for critical paths
- CI test gates

**Key Test Files:**
- `e2e/specs/kanban.spec.ts` - Drag-drop workflow
- `e2e/specs/paper-review.spec.ts` - Paper scoring flow

---

### Phase 5: Performance Optimization (Week 13-14)
**Complexity: Medium | Risk: Low**

**Tasks:**
1. Implement code splitting with lazy loading:
   ```typescript
   const KanbanPage = lazy(() => import('@/pages/kanban'));
   <Suspense fallback={<PageSkeleton />}>
     <KanbanPage />
   </Suspense>
   ```
2. Virtual lists for large datasets (TanStack Virtual)
3. Prefetching for navigation
4. Bundle analysis and size budgets
5. Image optimization

**Performance Targets:**
- Bundle size: < 200KB gzipped (initial)
- LCP: < 2.5s
- FID: < 100ms
- CLS: < 0.1

---

### Phase 6: AI/ML Integration Layer (Week 15-16)
**Complexity: High | Risk: Medium**

**Tasks:**
1. Create AI service abstraction:
   ```typescript
   export class AIService {
     private provider: AIProvider;

     async analyzePaper(paper: Paper): Promise<PaperAnalysis> {
       await this.usageTracker.checkQuota();
       const result = await this.provider.generateText(prompt);
       await this.usageTracker.recordUsage(result);
       return this.parseAnalysis(result);
     }

     async *streamEmailDraft(paper: Paper, researcher: Researcher) {
       for await (const chunk of this.provider.streamText(prompt)) {
         yield chunk;
       }
     }
   }
   ```
2. Implement streaming UI components
3. Add rate limiting and cost tracking
4. Create Supabase Edge Functions for AI
5. Implement analysis caching

**Deliverables:**
- Provider-agnostic AI layer (OpenAI, Anthropic, etc.)
- Streaming UI for AI features
- Cost tracking dashboard
- Rate limiting per user/org

---

### Phase 7: Observability & Security (Week 17-18)
**Complexity: Medium | Risk: Low**

**Tasks:**
1. Set up Sentry with source maps and session replay
2. Implement RBAC with type-safe permissions:
   ```typescript
   export const permissions = {
     'papers:read': ['admin', 'manager', 'member', 'researcher'],
     'papers:write': ['admin', 'manager'],
     'settings:write': ['admin'],
   } as const;

   export function usePermission(permission: keyof typeof permissions) {
     const { user } = useAuth();
     return permissions[permission].includes(user?.role);
   }
   ```
3. Add input sanitization with Zod
4. Configure security headers
5. Add Web Vitals tracking

**Deliverables:**
- Sentry integration
- Type-safe RBAC system
- Security headers
- Performance monitoring

---

### Phase 8: Polish & Documentation (Week 19-20)
**Complexity: Low | Risk: Low**

**Tasks:**
1. Complete Storybook documentation for all components
2. Write Architecture Decision Records (ADRs)
3. Create API documentation
4. Accessibility audit (WCAG 2.1 AA)
5. Production deployment runbook
6. Final security audit

**Deliverables:**
- Complete Storybook
- Architecture documentation
- WCAG 2.1 AA compliance
- Production checklist

---

## Key Architectural Decisions

### 1. Monorepo with Turborepo
**Choice:** Monorepo
**Trade-off:** Accept initial complexity for better code sharing and atomic changes

### 2. Drizzle ORM over Prisma
**Choice:** Drizzle
**Trade-off:** Smaller ecosystem for better edge support and type inference

### 3. Zustand over Redux Toolkit
**Choice:** Zustand
**Trade-off:** Less structure for simplicity and faster development

### 4. Feature-based Architecture
**Choice:** Vertical slices
**Trade-off:** Some code duplication for better encapsulation and maintainability

### 5. Keep Vite+React SPA (vs Next.js)
**Choice:** SPA
**Trade-off:** No SSR benefits to avoid migration complexity. Reconsider for v3.

---

## Migration Strategy: Strangler Fig Pattern

Instead of big-bang rewrite, incrementally migrate while keeping old code working:

1. **Create new structure alongside existing** (`/apps/web/src/` parallel to `/src/`)
2. **Migrate shared packages first** (UI, validators, database)
3. **Migrate one feature at a time** (start with Papers - most complex)
4. **Use feature flags** to switch between implementations:
   ```typescript
   if (featureFlags.useNewPapersModule) {
     return <NewPapersModule />;
   }
   return <LegacyPapersPage />;
   ```
5. **Remove old code** only after validation

---

## Complexity & Timeline Summary

| Phase | Duration | Complexity | Risk |
|-------|----------|------------|------|
| 0: Foundation | 2 weeks | Medium | Low |
| 1: Type Safety | 2 weeks | High | Medium |
| 2: State Management | 2 weeks | Medium | Medium |
| 3: Feature Migration | 4 weeks | High | Medium |
| 4: Testing | 2 weeks | Medium | Low |
| 5: Performance | 2 weeks | Medium | Low |
| 6: AI/ML Layer | 2 weeks | High | Medium |
| 7: Observability | 2 weeks | Medium | Low |
| 8: Polish | 2 weeks | Low | Low |
| **Total** | **20 weeks** | | |

---

## Critical Files for Implementation

| Current File | Issue | Migration Target |
|--------------|-------|------------------|
| `/src/services/papers/paperService.ts` | `any` types, mock fallback | `/features/papers/api/` |
| `/src/context/AppContext.tsx` | Mixed concerns | `/shared/stores/` (Zustand) |
| `/src/App.tsx` | No lazy loading, no error boundaries | `/app/App.tsx` |
| `/src/types/supabase.ts` | Generated types | `/packages/database/schema/` |
| `/src/pages/kanban/` | Large components | `/features/kanban/` |

---

## Verification Plan

1. **Development:**
   - `pnpm dev` - Start all apps
   - `pnpm storybook` - Component development

2. **Testing:**
   - `pnpm test` - Run Vitest
   - `pnpm test:e2e` - Run Playwright
   - `pnpm test:coverage` - Check coverage

3. **Build:**
   - `pnpm build` - Build all packages
   - `pnpm lint` - Biome checks
   - `pnpm typecheck` - TypeScript strict

4. **Deploy:**
   - Preview deployments on PRs
   - Staging environment for validation
   - Production with feature flags
