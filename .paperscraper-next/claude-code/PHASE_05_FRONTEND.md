# LEGACY DRAFT (Superseded)

This file is retained for reference only.
Use `STAGE_1_LOCAL_MVP.md` and `STAGE_2_PRODUCTIZATION.md` as the source of truth.

# Phase 5: Frontend

## Goal
All 9 pages built with TanStack Start + Shadcn/UI, connected to real backend data.

## UX References
- **Twenty CRM** — record detail pages, sidebar navigation, clean data tables
- **Notion** — database views, empty states, minimalist aesthetic
- **Linear** — keyboard shortcuts, fast transitions, command palette

## Sprint 9: Shell + Feed + Object Detail

### TanStack Start Setup

```typescript
// apps/web/app.config.ts
import { defineConfig } from '@tanstack/react-start/config';

export default defineConfig({
  server: { preset: 'vercel' },
});
```

### Layout Shell

```
┌──────────────────────────────────────┐
│ ┌─────┐ ┌──────────────────────────┐ │
│ │ Nav │ │                          │ │
│ │     │ │      Page Content        │ │
│ │ Feed│ │                          │ │
│ │ Pipe│ │                          │ │
│ │ Strm│ │                          │ │
│ │ Dims│ │                          │ │
│ │ Sets│ │                          │ │
│ └─────┘ └──────────────────────────┘ │
└──────────────────────────────────────┘
Mobile: bottom tab bar (Feed | Pipeline | Settings)
```

Components needed:
- `AppLayout` — sidebar + main content area
- `Sidebar` — navigation links, workspace name, user avatar
- `MobileNav` — bottom tab bar for small screens

### Feed Page (`/`)

The primary view. Shows a chronological stream of research objects with score badges.

```
┌─────────────────────────────────────────┐
│  Feed                    [Search] [Filter]│
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 📄 Paper Title                       │ │
│ │ Author A, Author B · 2025 · NeurIPS │ │
│ │ [IP: 8.2] [Nov: 7.1] [Mkt: 6.5]    │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 📄 Another Paper                     │ │
│ │ Author C · 2025 · arXiv             │ │
│ │ [IP: 5.0] [Nov: 9.2]                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ──── Load More ────                     │
└─────────────────────────────────────────┘
```

Key components:
- `ObjectCard` — title, authors, metadata, score badges
- `ScoreBadge` — colored badge showing dimension name + value
- `FilterBar` — type filter, date range, score threshold
- Infinite scroll with TanStack Query `useInfiniteQuery`

### Object Detail Page (`/objects/:id`)

```
┌──────────────────────────────────────────────┐
│ ← Back to Feed                                │
├──────────────────────────────────────────────┤
│                                              │
│  Paper Title (Full)                          │
│  Author A · Author B · Author C              │
│  2025 · NeurIPS · DOI: 10.1234/...          │
│                                              │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Spider Chart │  │  Scores Detail       │ │
│  │  (Recharts)   │  │  IP Potential: 8.2   │ │
│  │               │  │  "Strong IP due to..." │ │
│  │               │  │  Novelty: 7.1        │ │
│  │               │  │  "Builds on..."      │ │
│  └──────────────┘  └──────────────────────┘ │
│                                              │
│  Abstract                                    │
│  Lorem ipsum dolor sit amet...               │
│                                              │
│  Related Authors                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Author A │ │ Author B │ │ Author C │    │
│  │ IP: 7.5  │ │ IP: 6.2  │ │ IP: 8.8  │    │
│  └──────────┘ └──────────┘ └──────────┘    │
│                                              │
│  [Add to Pipeline ▼]                         │
└──────────────────────────────────────────────┘
```

Key components:
- `SpiderChart` — Recharts radar chart, reusable for objects and entities
- `ScoreDetail` — dimension name, value, explanation (expandable)
- `EntityChip` — small clickable card linking to entity detail
- `AddToPipeline` — dropdown to add object to a pipeline stage

### Spider Chart Component

```typescript
// apps/web/src/components/spider-chart.tsx
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';

interface SpiderChartProps {
  scores: Array<{ dimension: string; value: number; max: number }>;
  size?: number;
}

export function SpiderChart({ scores, size = 300 }: SpiderChartProps) {
  const data = scores.map(s => ({
    dimension: s.dimension,
    value: s.value,
    fullMark: s.max,
  }));

  return (
    <ResponsiveContainer width={size} height={size}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="dimension" />
        <Radar dataKey="value" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.3} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

## Sprint 10: Entity Pages + Stream/Dimension Management

### Entity Detail Page (`/entities/:id`)

Similar to Object Detail but for people/organizations:
- Profile header (name, type, affiliation, metadata)
- Spider chart (aggregated scores across all their objects)
- Timeline of research objects (most recent first)
- Related entities (co-authors, affiliated organizations)
- Score trend over time (line chart showing dimension scores by quarter)

### Streams Page (`/streams`)

CRUD interface for subscription management:
- List of streams with status (active/paused, last run, object count)
- Create stream form: name, source type (dropdown), config (dynamic form based on source)
- For OpenAlex: query field, institution filter, date range
- Trigger button to run immediately
- Schedule toggle with cron preset selector

### Dimensions Page (`/dimensions`)

CRUD for scoring dimensions:
- List of dimensions with apply count
- Create form: name, description, prompt template (code editor), scale config
- Prompt editor with syntax highlighting for `{{placeholders}}`
- Preview: show available placeholders (title, content, metadata.*, authors)
- Backfill toggle: "Score all existing objects?" checkbox

## Sprint 11: Settings + Onboarding

### Settings Page (`/settings`)

Tabs:
- **Workspace**: name, branding
- **API Keys**: add/remove BYOK keys per provider (OpenAI, Anthropic, etc.)
- **Team**: invite members, manage roles (admin/member/viewer)
- **Account**: email, password, delete account

### Login/Signup

Better Auth provides pre-built components. Customize with Shadcn/UI theming:
- Email + password
- Google OAuth button
- Magic link option

### Onboarding Wizard (First Run)

```
Step 1: "Welcome! Let's set up your workspace."
        → Workspace name

Step 2: "Add an AI provider key."
        → OpenAI or Anthropic key input
        → "We'll use this to score your research. Your key, your costs."

Step 3: "What do you want to track?"
        → Template selection: TTO | VC | Corporate | Custom
        → Pre-configures dimensions + pipeline

Step 4: "Create your first subscription."
        → Source: OpenAlex (pre-selected)
        → Query builder (institution, topic, date range)

Step 5: "Running your first ingestion..."
        → Progress indicator
        → "Done! 47 papers imported. View your feed →"
```

### Verification Checklist
- [ ] All 9 routes render without errors
- [ ] Feed shows real objects from database with scores
- [ ] Object detail shows spider chart + score explanations
- [ ] Entity detail shows aggregated scores + related objects
- [ ] Streams CRUD works (create, trigger, delete)
- [ ] Dimensions CRUD works (create with prompt, backfill)
- [ ] Settings: can add/remove API keys
- [ ] Onboarding wizard completes full flow
- [ ] Mobile responsive: all pages usable on 375px width
- [ ] Loading states on all data-fetching components
- [ ] Error boundaries catch and display errors gracefully
