# User Personas

> **Note on dimensions and pipelines below:** These are *template defaults*, not hardcoded features. Users select a template during onboarding, then freely add, remove, or modify any dimension, pipeline stage, or stream. The system is fully composable — templates are starting points for faster time-to-value, not constraints.

> **Note on "The hard question":** These questions represent the *ultimate* value proposition — what the platform enables over time. At MVP (no Chat interface), users answer these by filtering the Feed, browsing entity profiles, and using pipeline boards. Chat/query interface (Phase 2) will make these questions answerable conversationally.

## Persona 1: TTO (Technology Transfer Office)

**Role:** Technology transfer manager at a research university

**10x Problem:** They have hundreds of researchers. They need to know which research has commercial potential BEFORE the researcher comes to them. Currently reactive — they wait for disclosures instead of proactively scouting.

**How They Use PaperScraper:**
- **Subscribe to:** Their own university's output (OpenAlex institution filter), competitor institutions, patent filings in adjacent spaces (Phase 2: patent adapters)
- **Template dimensions:** IP readiness, licensing potential, market fit, researcher engagement history
- **Template pipeline:** Flagged → Assessment → Outreach → Negotiation → Licensed
- **The hard question:** "Which of our professors' work from the last 6 months has the highest licensing potential that we haven't engaged on yet?"
- **How MVP answers it:** Sort Feed by "licensing potential" dimension (descending), filter by date range. Entity detail pages show author-level aggregated scores — browse to find high-potential researchers with no pipeline cards (= not yet engaged).

**Template name:** "TTO Licensing Pipeline"

---

## Persona 2: Corporate Innovation / R&D

**Role:** Innovation scout or R&D strategy lead at a large corporation

**10x Problem:** Scanning the horizon for technologies that could disrupt or enhance their business. Currently done manually by reading papers or paying consultants.

**How They Use PaperScraper:**
- **Subscribe to:** Papers in their technology domains (OpenAlex keyword/concept filters), competitor patents (Phase 2), startup-adjacent research
- **Template dimensions:** Strategic relevance, technology maturity (user scores TRL via prompt like "estimate TRL 1-9 based on methods described"), competitive threat level, partnership potential
- **Template pipeline:** Detected → Evaluated → Recommended → Pilot → Integration
- **The hard question:** "Show me emerging battery technologies that could replace our current supply chain within 3 years."

**Template name:** "Technology Scouting"

---

## Persona 3: Venture Builder

**Role:** Venture studio operator who builds companies from science

**10x Problem:** Finding the science that could become a company. Not just interesting research — research + team + market timing.

**How They Use PaperScraper:**
- **Subscribe to:** Breakthrough papers across sectors (OpenAlex high-citation filters), founding team signals (author profile enrichment — Phase 2), patent clusters (Phase 2)
- **Template dimensions:** Venture potential, team coachability (LLM infers from co-author network breadth, industry affiliations, and publication trajectory — not precise, but directional), market timing, defensibility
- **Template pipeline:** Identified → Validated → Approached → Building → Launched
- **The hard question:** "Find me researchers who have breakthrough IP, industry connections, and no existing spin-off."

**Template name:** "Venture Pipeline"

---

## Persona 4: VC (Venture Capital)

**Role:** Deep tech investor doing technical due diligence

**10x Problem:** Is the science real? Is the team legit? What's the competitive landscape? Currently relies on expert networks and manual research.

**How They Use PaperScraper:**
- **Subscribe to:** Specific technology areas they invest in (OpenAlex concept/keyword filters), portfolio company competitive landscapes (author/institution filters)
- **Template dimensions:** Scientific rigor (LLM evaluates methodology, peer review status, citation quality), competitive differentiation, team strength, market size (LLM estimates based on paper's described application area — directional, not precise TAM)
- **Template pipeline:** Flagged → Deep Dive → Due Diligence → IC → Invested
- **The hard question:** "How does this startup's core technology compare to the top 20 research groups globally?"

**Template name:** "Deal Flow Intelligence"

---

## Persona 5: PE (Private Equity)

**Role:** Technology risk assessor for acquisitions

**10x Problem:** Technology risk assessment on acquisitions. Is this company's R&D pipeline real? Is their patent portfolio defensible?

**How They Use PaperScraper:**
- **Subscribe to:** Target company researchers' output (OpenAlex institution/author filters), industry technology trends
- **Template dimensions:** Technology moat durability (LLM assesses novelty vs. prior art from similar papers), R&D productivity (LLM evaluates publication frequency, citation growth), talent retention risk (LLM infers from author affiliation changes — directional signal)
- **Template pipeline:** Target → Assessment → Due Diligence → Recommendation
- **The hard question:** "Is this company's patent portfolio defensible given recent academic publications?"

**Template name:** "Tech Due Diligence"

---

## Universal Pattern

All personas share the same underlying needs:

| Need | MVP Feature | Phase 2+ Feature |
|------|------------|-------------------|
| "Show me what matters" | Streams + Dimensions + Feed with score sorting | Trend Radar page |
| "Who's behind this?" | Knowledge graph (objects → authors → orgs), Entity Detail pages | Relationship explorer |
| "What's trending?" | Score fold-up on entities, sorted views | BERTrend topic detection, Trend Radar |
| "What should I do about it?" | Pipeline board + manual card placement | Automated triggers, webhook actions |
| "Answer my hard question" | Filter/sort Feed + browse entity profiles + pipeline boards | Chat interface over the knowledge graph |

The product doesn't know or care which persona is using it. Templates provide starting points; the engine is universal.
