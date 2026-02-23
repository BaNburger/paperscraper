# Product Vision

## One-Liner

PaperScraper is a **knowledge streaming and action platform** that turns research data into actionable intelligence — like a CRM for science.

## The Problem

Research intelligence is broken. TTOs manually scan papers. VCs do due diligence by reading PDFs. Corporate innovation teams build spreadsheets. Everyone is drowning in unstructured research data with no systematic way to monitor, analyze, and act on it.

LLM providers can answer "what's hot in transformers" — but they answer from frozen training data, with no custom lens, no entity tracking, and no longitudinal awareness. Point-in-time answers from general knowledge are not intelligence.

## The Solution

A composable platform where users:

1. **Subscribe** to research streams (papers, patents, reports, news — any source)
2. **Define** their own analytical dimensions (not our 6 hardcoded scores — *their* lenses)
3. **See** scores fold up automatically: paper → author → group → trend
4. **Act** through customizable pipelines (Kanban boards, automations, integrations)

Same engine for TTOs, VCs, Corporate Innovation, PE, and Venture Builders — differentiated by configuration, not code.

## Key Concepts (Glossary)

| Term | Definition |
|------|-----------|
| **Stream** | A recurring data subscription. Contains: a source adapter (e.g. OpenAlex), a query/filter config, and a cron schedule. Each run fetches new objects matching the criteria since the last run. Stored as `Stream` table row. |
| **Research Object** | A single unit of research data (paper, patent, report). Has a title, content, JSONB metadata, and a vector embedding. The universal entity that gets scored. |
| **Entity** | A person or organization resolved from research objects. Entities persist across objects — the same author appearing on 10 papers maps to one entity. |
| **Dimension** | A user-defined scoring lens. Contains a name, an LLM prompt template with `{{placeholders}}`, and a scale (default 0–10). Each dimension produces one score per object, which then aggregates up to entities. |
| **Score Fold-Up** | The mechanism that aggregates object-level scores to entity-level scores. Uses exponential recency-weighted averaging: `weight = exp(-age_days / 365)`. When a paper scores 8 on "IP Potential," that score contributes to the paper's author's aggregated IP Potential score, weighted by recency. Fold-up runs asynchronously via BullMQ after each object score. |
| **Pipeline** | A Kanban workflow that accepts any entity type. Has ordered stages (user-defined, e.g. "Inbox → Review → Shortlist → Act") and optional triggers that auto-place entities based on score thresholds. |
| **Trigger** | A rule on a pipeline: "when [dimension] [operator] [threshold], add entity to [stage]." E.g., "when IP Potential > 7, add to Review stage." Evaluated after each fold-up. |
| **View** | A saved query over objects or entities with filters, sorts, and layout (table, grid). Like a Notion database view. |
| **Template** | A pre-configured set of dimensions + pipeline + example stream for a specific persona (TTO, VC, etc.). Applied during onboarding. Users can modify everything after application — templates are starting points, not constraints. |

## The Moat

**Structured, longitudinal, custom intelligence on real-time research data.**

No LLM provider will build this because it requires:
- Domain-specific ingestion pipelines with entity resolution (connecting papers to people to orgs)
- Persistent knowledge graphs maintained over time (not frozen training data — live, incrementally updated)
- User-defined analytical frameworks applied consistently at scale (custom dimensions, not generic summarization)
- Grounded, cited, quantitative answers from curated streams (scores derived from actual papers, not hallucinated)

ChatGPT answers from training data. PaperScraper answers from **your** data, through **your** lenses, with **real** citations.

## Core Mental Model

```
        Trend Radar (overview)
             ↕
    Research Objects (papers, patents, ...)
             ↕
         Authors (people)
             ↕
      Work Groups (organizations)
```

Four entity types. User-defined scoring dimensions. Scores fold up the chain. That's the entire product.

## Design Principles

1. **User defines the pipe, not us.** We provide the engine. They bring the opinions.
2. **10% of features, 10x the value.** Every feature must work for every persona or it doesn't belong.
3. **Configuration over code.** Adding "TTO mode" is a template, not new endpoints.
4. **Lean and fast.** Sub-second page loads. Real-time scoring updates. No clutter.
5. **Plug anything in.** APIs on the front (sources), middle (processing), and back (actions).

## Key Metrics

- **Time to first scored result:** < 60 seconds (measured: from stream trigger → first object's first dimension score stored in DB)
- **Pages in the product:** 9 (Feed, Object Detail, Entity Detail, Pipeline Board, Streams, Dimensions, Settings, Login, Onboarding)
- **Core database tables:** 12 (see DATA_MODEL.md — Workspace, User, ApiKey, Stream, ResearchObject, Entity, ObjectEntity, EntityRelation, Dimension, Score, Pipeline, PipelineCard, View)
- **Backend engines:** 5 (Ingestion, Graph, Scoring, Pipeline, Query)

## Positioning

"The analytical CRM for research intelligence."

CRMs succeeded because they said: "here are contacts, companies, deals, activities — you decide your sales process." We say: "here are papers, authors, groups, trends — you decide your analysis process."
