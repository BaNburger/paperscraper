# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 8: Polish

## Goal
Production-ready MVP: onboarding templates, comprehensive testing, security hardening, observability.

## Sprint 16: Onboarding + Templates

### Persona Templates

Each template pre-configures: dimensions, a pipeline, and a suggested stream config.

```typescript
// packages/shared/src/templates/index.ts
export const templates = {
  tto: {
    name: 'Technology Transfer Office',
    description: 'Scout university research for licensing and spin-off potential.',
    dimensions: [
      { name: 'IP Potential', prompt: '...', config: { maxScore: 10 } },
      { name: 'Market Readiness', prompt: '...', config: { maxScore: 10 } },
      { name: 'Team Strength', prompt: '...', config: { maxScore: 10 } },
    ],
    pipeline: {
      name: 'Licensing Pipeline',
      stages: [
        { name: 'Flagged', order: 0, color: '#3b82f6' },
        { name: 'Assessment', order: 1, color: '#f59e0b' },
        { name: 'Outreach', order: 2, color: '#8b5cf6' },
        { name: 'Negotiation', order: 3, color: '#ef4444' },
        { name: 'Licensed', order: 4, color: '#22c55e' },
      ],
      triggers: [{ dimensionName: 'IP Potential', operator: 'gte', threshold: 7, targetStage: 'Flagged' }],
    },
    suggestedStream: {
      sourceType: 'openalex',
      configHint: 'Enter your institution name to track your researchers\' output.',
    },
  },

  vc: {
    name: 'Venture Capital',
    description: 'Deep tech due diligence and competitive landscape monitoring.',
    dimensions: [
      { name: 'Scientific Rigor', prompt: '...', config: { maxScore: 10 } },
      { name: 'Competitive Differentiation', prompt: '...', config: { maxScore: 10 } },
      { name: 'Venture Potential', prompt: '...', config: { maxScore: 10 } },
    ],
    pipeline: {
      name: 'Deal Flow',
      stages: [
        { name: 'Detected', order: 0, color: '#3b82f6' },
        { name: 'Deep Dive', order: 1, color: '#f59e0b' },
        { name: 'Due Diligence', order: 2, color: '#8b5cf6' },
        { name: 'IC', order: 3, color: '#ef4444' },
        { name: 'Invested', order: 4, color: '#22c55e' },
      ],
      triggers: [{ dimensionName: 'Venture Potential', operator: 'gte', threshold: 8, targetStage: 'Detected' }],
    },
    suggestedStream: {
      sourceType: 'openalex',
      configHint: 'Enter technology keywords you invest in (e.g., "quantum computing").',
    },
  },

  corporate: {
    name: 'Corporate Innovation',
    description: 'Technology scouting and strategic R&D monitoring.',
    dimensions: [
      { name: 'Strategic Relevance', prompt: '...', config: { maxScore: 10 } },
      { name: 'Technology Maturity', prompt: '...', config: { maxScore: 10 } },
      { name: 'Partnership Potential', prompt: '...', config: { maxScore: 10 } },
    ],
    pipeline: {
      name: 'Scouting Pipeline',
      stages: [
        { name: 'Detected', order: 0, color: '#3b82f6' },
        { name: 'Evaluated', order: 1, color: '#f59e0b' },
        { name: 'Recommended', order: 2, color: '#8b5cf6' },
        { name: 'Pilot', order: 3, color: '#22c55e' },
      ],
      triggers: [{ dimensionName: 'Strategic Relevance', operator: 'gte', threshold: 7, targetStage: 'Detected' }],
    },
    suggestedStream: {
      sourceType: 'openalex',
      configHint: 'Enter keywords related to your industry and technology domain.',
    },
  },

  custom: {
    name: 'Custom Setup',
    description: 'Start from scratch and define everything yourself.',
    dimensions: [],
    pipeline: null,
    suggestedStream: null,
  },
};
```

### Template Application

During onboarding, when user selects a template:
1. Create dimensions from template
2. Create pipeline from template
3. Pre-fill stream creation form with suggested config
4. Skip the empty "no data yet" state — go straight to stream creation

## Sprint 17: Testing + Hardening

### Unit Tests (Vitest)

Test each engine's core logic:

```
tests/
├── engines/
│   ├── ingestion/
│   │   ├── openalex-adapter.test.ts    # Normalize OpenAlex data
│   │   └── dedup.test.ts               # Deduplication logic
│   ├── graph/
│   │   ├── resolver.test.ts            # Entity resolution confidence
│   │   └── relationships.test.ts       # Co-authorship inference
│   ├── scoring/
│   │   ├── template.test.ts            # Prompt template rendering
│   │   ├── fold-up.test.ts             # Weighted average computation
│   │   └── keys.test.ts                # Encryption/decryption
│   ├── pipeline/
│   │   └── triggers.test.ts            # Trigger evaluation logic
│   └── query/
│       └── hybrid-search.test.ts       # Search ranking
├── routers/
│   ├── streams.test.ts                  # CRUD + auth checks
│   ├── dimensions.test.ts
│   ├── pipelines.test.ts
│   └── search.test.ts
└── middleware/
    ├── auth.test.ts                     # Better Auth session validation
    └── workspace.test.ts                # Tenant isolation enforcement
```

Target: **~100 unit tests** covering all core logic paths.

### Integration Tests

Test tRPC routes end-to-end with a test database:

```typescript
// tests/setup.ts
import { createTestContext } from './helpers';

beforeEach(async () => {
  // Create fresh test workspace + user
  const ctx = await createTestContext();
  // Seed with test data
});

afterEach(async () => {
  // Clean up test data
});
```

### E2E Tests (Playwright)

Critical user flows:

```
e2e/
├── signup.spec.ts           # Sign up → see onboarding
├── onboarding.spec.ts       # Select template → create stream → see results
├── feed.spec.ts             # View feed → click object → see detail
├── scoring.spec.ts          # Create dimension → objects get scored
├── pipeline.spec.ts         # Create pipeline → drag card → verify move
└── search.spec.ts           # Search query → see results → filter
```

Target: **~15 E2E tests** covering the complete user journey.

### Security Hardening

- [ ] SSRF validation: block private/reserved IP ranges in plugin URLs
- [ ] Rate limiting: all endpoints, 100 req/min per user
- [ ] CSRF: Better Auth handles this with httpOnly cookies
- [ ] Input validation: Zod on all tRPC inputs (already done)
- [ ] SQL injection: Prisma parameterized queries (already done)
- [ ] XSS: React escapes by default, CSP headers
- [ ] API key encryption: verify enc:v1 format, test decrypt
- [ ] Audit: log all mutations with user + timestamp (lightweight)

### Performance Targets

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Page load (p95) | < 1 second | Lighthouse CI |
| Search latency | < 200ms | Vitest benchmark |
| Scoring throughput | 10 papers/second | BullMQ dashboard |
| Feed pagination | < 100ms | tRPC response time |

### Observability

- [ ] Langfuse: wrap all LLM calls with trace context (dimension name, workspace, model)
- [ ] Sentry: error tracking on API + frontend + workers
- [ ] BullMQ Dashboard: monitor queue depth, job latency, failures
- [ ] Health endpoint: DB + Redis connectivity check

### Final Verification

Run the complete test suite:
```bash
pnpm test              # Vitest unit + integration
pnpm test:e2e          # Playwright
pnpm lint              # TypeScript strict
pnpm build             # Production build succeeds
```

All must pass before declaring MVP complete.
