# Paper Scraper - User Stories & Product Vision

> **📌 Important:** This document represents the **initial product vision** and planning context.
> **For actual implementation status**, see **[docs/implementation/STATUS.md](docs/implementation/STATUS.md)**
>
> **✅ All 37 sprints completed** (2024-2026) across 10 development phases.
> This document is maintained for historical context and product vision alignment.

---

## Implementation Status

### Completed Features (Sprint 1-37)

**✅ All Core Features (100%)**
- User Authentication & Authorization (Sprint 1)
- Paper Management & CRUD (Sprint 2)
- 6-Dimension AI Scoring (Sprints 3, 23)
- KanBan Project Pipelines (Sprint 4)
- Semantic & Fulltext Search (Sprints 5, 11)
- Multi-Source Ingestion (Sprints 2, 8, 37)
- Author Intelligence & CRM (Sprints 9-10)
- Analytics & Reporting (Sprints 12, 27)
- Data Export (CSV, BibTeX, PDF) (Sprint 12)

**✅ All Advanced Features (100%)**
- Team Invitations & User Management (Sprint 13)
- Email Infrastructure (Sprint 13)
- Onboarding Wizard (Sprint 14)
- Researcher Groups (Sprint 16)
- Technology Transfer Workflows (Sprint 17)
- Research Submission Portal (Sprint 18)
- Gamification & Badges (Sprint 19)
- Knowledge Management (Sprint 19)
- Granular RBAC & Permissions (Sprints 22, 31)
- Model Settings & LLM Configuration (Sprint 23)
- Developer API & Webhooks (Sprint 25)
- MCP Server (Sprint 25)
- Repository Management (Sprint 25)
- Keyboard Navigation (Sprint 26)
- Mobile Responsiveness (Sprint 26)
- Scheduled Reports (Sprint 27)

**✅ All Enterprise Features (100%)**
- Audit Logging (Sprint 28)
- Data Retention Policies (Sprint 28)
- SOC2 Compliance Framework (Sprint 28)
- Internationalization EN/DE (Sprints 29, 35)
- Server-side Notifications (Sprint 36)
- Saved Searches & Alerts (Sprints 11, 34)
- Unified Ingestion Pipeline (Sprint 37)

**📊 Key Metrics:**
- **24 Backend Modules** with 208+ API endpoints
- **841 pytest unit/integration tests**
- **40+ database tables** with pgvector support
- **28 frontend pages** with E2E test coverage
- **6 background job types** (arq workers)

**For detailed sprint history:** See [docs/implementation/](docs/implementation/) (10 phase documents covering Sprints 1-37)

---

## Original Epic Structure (Historical Planning Context)

The following Epics guided the initial development. All features have been implemented and expanded beyond the original scope.

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 0: Foundation                           │
│         Technical Base, Auth, Database Setup                    │
│                    ✅ Completed: Sprint 1-2                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 1: Paper Ingestion                      │
│         Paper Import, PDF Parsing, Metadata                     │
│                    ✅ Completed: Sprint 2-3, 37                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 2: AI Scoring Core                      │
│      6-Dimensional Scoring, Pitch, Summaries                    │
│                    ✅ Completed: Sprint 3-5, 23                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 3: KanBan Pipeline                      │
│         Projects, Stages, Drag&Drop, Rejection Tracking         │
│                    ✅ Completed: Sprint 4-6                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 4: Search & Discovery                   │
│         Semantic Search, Filters, Alerts                        │
│                    ✅ Completed: Sprint 5-7, 11, 34             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 5: Author Intelligence                  │
│         Author Profiles, Contact Tracking, Outreach             │
│                    ✅ Completed: Sprint 7-10                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 6: Analytics & Reporting                │
│         Dashboard, Trends, Export                               │
│                    ✅ Completed: Sprint 9-12, 27                │
└─────────────────────────────────────────────────────────────────┘
```

**Note:** Development continued beyond these 6 epics through Sprint 37, adding Enterprise, Security, and AI advancement features. See [docs/implementation/STATUS.md](docs/implementation/STATUS.md) for complete feature list.

---

## Core User Stories (Condensed)

### EPIC 0: Foundation ✅

**US-0.1: Project Setup**
**As** a developer, **I want** a fully configured development environment **so that** I can start implementing immediately.

**Delivered:** Sprint 1 (docker-compose, FastAPI, PostgreSQL, Redis, MinIO, Alembic, pytest, CI/CD)

---

**US-0.2: User Authentication**
**As** a user, **I want** to securely log in **so that** my data is protected.

**Delivered:** Sprint 1 (JWT auth, refresh tokens, password hashing, rate limiting, magic link login)
**Expanded:** Sprint 13 (email verification, password reset, team invitations), Sprint 22 (granular RBAC)

---

**US-0.3: Multi-Tenancy**
**As** an organization, **I want** my data isolated from other organizations **so that** confidentiality is ensured.

**Delivered:** Sprint 2 (organization model, tenant-id filtering, row-level security)

---

### EPIC 1: Paper Ingestion ✅

**US-1.1: DOI Import**
**As** a TTO manager, **I want** to add papers via DOI **so that** I can quickly import specific publications.

**Delivered:** Sprint 2 (DOI input, Crossref API, author extraction, duplicate detection)

---

**US-1.2: PubMed/arXiv Integration**
**As** a researcher, **I want** to import papers from PubMed and arXiv **so that** I can streamline my literature research.

**Delivered:** Sprint 2-3 (PubMed API, arXiv API, batch import, scheduled import)
**Expanded:** Sprint 8 (OpenAlex integration), Sprint 37 (unified multi-source pipeline with run tracking)

---

**US-1.3: PDF Upload and Parsing**
**As** a user, **I want** to upload PDFs **so that** non-indexed papers can be analyzed.

**Delivered:** Sprint 3 (PDF upload, text extraction via PyMuPDF, metadata extraction, S3 storage)

---

**US-1.4: Full-Text Link**
**As** a user analyzing a paper, **I want** a direct link to the full text in a new tab **so that** I don't lose context.

**Delivered:** Sprint 2 (full-text link button on paper detail page)

---

### EPIC 2: AI Scoring Core ✅

**US-2.1: Novelty Scoring**
**As** a TTO analyst, **I want** AI to score technological novelty **so that** I can prioritize groundbreaking research.

**Delivered:** Sprint 3 (LLM-based novelty scoring with confidence metrics)

---

**US-2.2: IP-Potential Scoring**
**As** a TTO manager, **I want** AI to assess patent potential **so that** I can identify commercializable IP.

**Delivered:** Sprint 3 (patent landscape analysis, prior art assessment)

---

**US-2.3: Marketability Scoring**
**As** a VC analyst, **I want** AI to score market potential **so that** I can estimate ROI.

**Delivered:** Sprint 3 (market size estimation, industry fit analysis)

---

**US-2.4: Feasibility & Commercialization Scoring**
**As** a TTO manager, **I want** AI to assess TRL and commercialization path **so that** I can plan outreach.

**Delivered:** Sprint 3 (TRL estimation, commercialization path recommendation)

---

**US-2.5: Team Readiness Scoring**
**As** a TTO analyst, **I want** AI to assess author track record **so that** I can evaluate team strength.

**Delivered:** Sprint 23 (h-index, works count, industry experience, institutional support scoring)

---

**US-2.6: One-Line-Pitch Generator**
**As** a TTO manager, **I want** AI to generate concise pitches **so that** I can quickly communicate value.

**Delivered:** Sprint 3 (GPT-based pitch generation, max 15 words)

---

**US-2.7: Simplified Abstract**
**As** a non-technical stakeholder, **I want** simplified abstracts **so that** I can understand complex research.

**Delivered:** Sprint 3 (layman-friendly abstract generation)

---

**US-2.8: Score Breakdown**
**As** a user, **I want** detailed score explanations **so that** I can understand AI reasoning.

**Delivered:** Sprint 3 (dimension-level details stored in JSONB)
**Expanded:** Sprint 6 (Innovation Radar visualization on frontend)

---

### EPIC 3: KanBan Pipeline ✅

**US-3.1: Project Creation**
**As** a TTO manager, **I want** to create screening projects **so that** I can organize papers.

**Delivered:** Sprint 4 (project CRUD, customizable stages)

---

**US-3.2: Drag & Drop KanBan**
**As** a user, **I want** to drag papers between stages **so that** I can visualize progress.

**Delivered:** Sprint 4 (drag & drop with @dnd-kit, stage history tracking)

---

**US-3.3: Rejection Tracking**
**As** a TTO manager, **I want** to document rejection reasons **so that** we learn from decisions.

**Delivered:** Sprint 4 (mandatory rejection reason, rejection notes)

---

**US-3.4: Paper Assignment**
**As** a TTO manager, **I want** to assign papers to team members **so that** workload is distributed.

**Delivered:** Sprint 4 (assignee field, assignment tracking)

---

**US-3.5: Paper Notes**
**As** a team member, **I want** to add notes to papers **so that** I can collaborate.

**Delivered:** Sprint 4 (notes CRUD, @mention support)

---

### EPIC 4: Search & Discovery ✅

**US-4.1: Fulltext Search**
**As** a user, **I want** to search by keywords **so that** I can find relevant papers.

**Delivered:** Sprint 5 (PostgreSQL pg_trgm full-text search)

---

**US-4.2: Semantic Search**
**As** a researcher, **I want** to find similar papers **so that** I can discover related work.

**Delivered:** Sprint 5 (pgvector HNSW index, cosine distance, hybrid RRF ranking)
**Expanded:** Sprint 11 (saved searches, alerts)

---

**US-4.3: Advanced Filters**
**As** a user, **I want** to filter by date, journal, score **so that** I can narrow results.

**Delivered:** Sprint 5 (multi-field filters, score thresholds, date ranges)

---

**US-4.4: Automatic Alerts**
**As** a user, **I want** automated search alerts **so that** I don't miss new papers.

**Delivered:** Sprint 11 (daily/weekly alerts via arq cron jobs)
**Expanded:** Sprint 34 (refined alert system with notification integration)

---

**US-4.5: Paper Classification**
**As** a user, **I want** papers classified by type **so that** I can filter by research type.

**Delivered:** Sprint 5 (LLM-based classification: original_research, review, case_study, etc.)

---

### EPIC 5: Author Intelligence ✅

**US-5.1: Author Profiles**
**As** a TTO analyst, **I want** to view author profiles **so that** I can assess expertise.

**Delivered:** Sprint 9 (h-index, citation count, works count, affiliations)

---

**US-5.2: Contact Tracking**
**As** a TTO manager, **I want** to log author contacts **so that** we track outreach.

**Delivered:** Sprint 10 (contact type, subject, notes, outcome, follow-up date)

---

**US-5.3: Author Enrichment**
**As** a user, **I want** to enrich author data **so that** I have current information.

**Delivered:** Sprint 9 (OpenAlex API enrichment, ORCID/Semantic Scholar stubs)

---

**US-5.4: Contact Statistics**
**As** a TTO manager, **I want** to see contact stats **so that** I can measure engagement.

**Delivered:** Sprint 10 (contact count by type, outcome distribution, follow-up tracking)

---

### EPIC 6: Analytics & Reporting ✅

**US-6.1: Dashboard Overview**
**As** a TTO manager, **I want** a dashboard **so that** I can see key metrics.

**Delivered:** Sprint 12 (total papers, average score, pipeline stage distribution, recent activity)

---

**US-6.2: Team Activity**
**As** a TTO manager, **I want** to see team activity **so that** I can track productivity.

**Delivered:** Sprint 12 (user activity metrics, papers scored per user, contributions)

---

**US-6.3: Paper Trends**
**As** a user, **I want** to see paper trends **so that** I can identify patterns.

**Delivered:** Sprint 12 (import trends, score distributions, source breakdown)

---

**US-6.4: Data Export**
**As** a user, **I want** to export data **so that** I can use external tools.

**Delivered:** Sprint 12 (CSV, BibTeX, PDF report export)

---

**US-6.5: Scheduled Reports**
**As** a TTO manager, **I want** automated reports **so that** I stay informed.

**Delivered:** Sprint 27 (weekly/monthly reports, configurable metrics, email delivery)

---

## Beyond Original Epics (Sprint 13-37)

The product evolved significantly beyond the original 6 epics. Additional features delivered:

### Team Collaboration (Sprints 13-14, 16-19)
- Team invitations with role management
- Onboarding wizard (4-step)
- Researcher groups with AI-suggested members
- Technology transfer conversation workflows
- Research submission portal
- Gamification & badges (15+ achievement types)
- Knowledge management

### Security & Compliance (Sprints 22, 28, 31)
- Granular RBAC with permission system
- Audit logging (GDPR compliance)
- Data retention policies
- SOC2 compliance framework
- Account lockout & token blacklist

### Platform & Developer Features (Sprints 23, 25-27)
- LLM model settings & configuration
- Developer API (keys, webhooks, repository sources)
- MCP server implementation
- Scheduled reports
- Keyboard navigation & accessibility
- Mobile responsive design

### Enterprise Features (Sprints 28-36)
- Internationalization (EN/DE)
- Server-side notification system
- Advanced alert refinements
- Quality & production hardening

### Foundations Pipeline (Sprint 37)
- Unified multi-source ingestion pipeline
- Ingestion run tracking & checkpointing
- Source record deduplication
- Comprehensive E2E testing

**Detailed Implementation History:** See [docs/implementation/PHASE_01_FOUNDATION.md](docs/implementation/PHASE_01_FOUNDATION.md) through [PHASE_10_FOUNDATIONS.md](docs/implementation/PHASE_10_FOUNDATIONS.md)

---

## RICE Prioritization Framework (Historical Context)

User stories were prioritized using RICE:
- **Reach:** Number of users affected per time period (1-10)
- **Impact:** Value to those users (1-10: minimal, low, medium, high, massive)
- **Confidence:** Certainty in estimates (1-10)
- **Effort:** Person-weeks to implement (1-10)

**RICE Score = (Reach × Impact × Confidence) / Effort**

**Priority Tiers:**
- **High Priority (RICE ≥ 200):** MVP-critical features
- **Medium Priority (RICE 100-199):** Post-MVP enhancements
- **Low Priority (RICE < 100):** Nice-to-have features

**Note:** Actual sprint planning evolved beyond RICE scoring as the product matured.

---

## Future Enhancements

For planned future work, see **[docs/implementation/FUTURE_ENHANCEMENTS.md](docs/implementation/FUTURE_ENHANCEMENTS.md)**

Potential next features:
- Advanced analytics (cohort analysis, funnel tracking)
- White-label branding customization
- Mobile app (React Native)
- API rate limiting per tier
- Redis caching layer
- Slack/Teams integration
- Advanced IP analytics (patent search integration)
- Batch operations UI

---

## Documentation Navigation

**For detailed information:**
- **[docs/INDEX.md](docs/INDEX.md)** - Master navigation hub
- **[docs/implementation/STATUS.md](docs/implementation/STATUS.md)** - Current state & metrics
- **[docs/implementation/](docs/implementation/)** - Sprint-by-sprint history (10 phase docs)
- **[docs/features/](docs/features/)** - Feature implementation guides
- **[docs/modules/](docs/modules/)** - Module-level documentation (24 modules)
- **[docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)** - All 208+ API endpoints

**For development:**
- **[CLAUDE.md](CLAUDE.md)** - AI agent quick start
- **[docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)** - Code conventions
- **[docs/development/TESTING_GUIDE.md](docs/development/TESTING_GUIDE.md)** - Testing patterns

---

**Last Updated:** 2026-02-10
**Document Status:** Refactored to reflect 37 completed sprints with cross-references
**Lines:** 462 (reduced from 746 = 38% reduction)
