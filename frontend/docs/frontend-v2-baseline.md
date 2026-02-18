# Frontend V2 Baseline

Captured: 2026-02-18
Workspace: /Users/bastianburger/Repos/PaperScraper/frontend

## Build baseline (before chunk-strategy budget hardening)

Command:

```bash
npm run build
```

Observed highlights:

- Total `dist/`: ~1.4 MB
- Largest JS chunk: `dist/assets/index-*.js` at ~675.5 KB (warning above Vite's default 500 KB)
- Largest route chunks:
  - `dist/assets/PaperDetailPage-*.js`: ~44.8 KB
  - `dist/assets/AnalyticsPage-*.js`: ~29.1 KB
  - `dist/assets/CompliancePage-*.js`: ~21.1 KB

## Largest non-generated source files

Excludes `src/api/generated/*` and tests.

- `src/types/index.ts`: 1879 lines
- `src/api/domains/core.ts`: 1614 lines
- `src/pages/PaperDetailPage.tsx`: 1471 lines
- `src/pages/AnalyticsPage.tsx`: 924 lines
- `src/pages/SearchPage.tsx`: 918 lines
- `src/pages/DeveloperSettingsPage.tsx`: 874 lines
- `src/pages/CompliancePage.tsx`: 827 lines
- `src/pages/ModelSettingsPage.tsx`: 773 lines
- `src/pages/PapersPage.tsx`: 741 lines

## E2E baseline artifacts

- Local `e2e/test-results` and `e2e/playwright-report` were not present at capture time.
- No failing local Playwright artifact bundle was available to snapshot in this baseline.

## Refactor guardrails and conventions

- Query keys:
  - Use `src/config/queryKeys.ts` exclusively.
  - Avoid ad-hoc tuple literals in hooks/components.
- API module boundaries:
  - HTTP concerns stay in `src/api/http/*`.
  - Domain APIs stay in `src/api/domains/*`.
  - Public API surface re-exported by `src/api/index.ts`.
- Page composition:
  - Pages should orchestrate data and composition, while reusable controls (pagination, async states, links, auth shell) stay in shared UI components.
- Budget gates (CI):
  - Entry bundle max: 716800 bytes.
  - Largest non-generated source file max: 1900 lines.
