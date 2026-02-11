# PaperScraper Documentation Index

[← Back to README](../README.md)

## Quick Navigation

**I want to...**

### Understand the System
- 📐 **Understand the system architecture** → [architecture/OVERVIEW.md](architecture/OVERVIEW.md)
- 🛠️ **Review technology stack & versions** → [architecture/TECH_STACK.md](architecture/TECH_STACK.md)
- 🗄️ **Understand the data model** → [architecture/DATA_MODEL.md](architecture/DATA_MODEL.md)
- 📋 **Review architecture decisions (ADRs)** → [architecture/DECISIONS.md](architecture/DECISIONS.md)

### Develop Features
- 🔌 **Look up an API endpoint** → [api/API_REFERENCE.md](api/API_REFERENCE.md)
- 📦 **Understand a specific module** → [modules/MODULES_OVERVIEW.md](modules/MODULES_OVERVIEW.md)
- ⭐ **Implement scoring features** → [features/SCORING_GUIDE.md](features/SCORING_GUIDE.md)
- 📥 **Implement paper ingestion** → [features/INGESTION_GUIDE.md](features/INGESTION_GUIDE.md)
- 🔍 **Implement search features** → [features/SEARCH_GUIDE.md](features/SEARCH_GUIDE.md)
- 🔄 **Implement pipeline workflows** → [features/PIPELINE_GUIDE.md](features/PIPELINE_GUIDE.md)

### Setup & Deploy
- 🚀 **Set up my local environment** → [../SETUP.md](../SETUP.md)
- 🌐 **Deploy to production** → [../DEPLOYMENT.md](../DEPLOYMENT.md)

### Track Progress
- ✅ **Check current sprint status** → [implementation/STATUS.md](implementation/STATUS.md)
- 📖 **Review implementation history** → [implementation/](implementation/)
- 🐛 **Check technical debt** → [implementation/TECHNICAL_DEBT.md](implementation/TECHNICAL_DEBT.md)
- 🔮 **See future enhancements** → [implementation/FUTURE_ENHANCEMENTS.md](implementation/FUTURE_ENHANCEMENTS.md)

### Write Code
- 📝 **Follow coding standards** → [development/CODING_STANDARDS.md](development/CODING_STANDARDS.md)
- 🧪 **Write and run tests** → [development/TESTING_GUIDE.md](development/TESTING_GUIDE.md)
- 🔧 **Perform common tasks** → [development/COMMON_TASKS.md](development/COMMON_TASKS.md)
- 🔍 **Troubleshoot issues** → [development/TROUBLESHOOTING.md](development/TROUBLESHOOTING.md)

---

## Documentation Structure

```
docs/
├── INDEX.md (this file) ← Master navigation
│
├── architecture/         → System design & decisions
│   ├── OVERVIEW.md      → Architecture overview & diagrams
│   ├── TECH_STACK.md    → Technology stack details
│   ├── DATA_MODEL.md    → Database schema & relationships
│   └── DECISIONS.md     → Architecture Decision Records (ADRs)
│
├── api/                 → API documentation
│   ├── API_REFERENCE.md → All 208+ endpoints
│   └── API_PATTERNS.md  → Common API patterns
│
├── modules/             → Per-module documentation (24 modules)
│   ├── MODULES_OVERVIEW.md → All modules overview
│   ├── auth.md          → Authentication & authorization
│   ├── papers.md        → Paper management
│   ├── scoring.md       → AI scoring system
│   ├── search.md        → Fulltext & semantic search
│   ├── projects.md      → KanBan pipelines
│   └── ... (19 more)
│
├── features/            → Feature implementation guides
│   ├── SCORING_GUIDE.md     → 6-dimension AI scoring
│   ├── INGESTION_GUIDE.md   → Paper import from APIs
│   ├── SEARCH_GUIDE.md      → Search implementation
│   └── PIPELINE_GUIDE.md    → Pipeline workflows
│
├── development/         → Development workflows
│   ├── CODING_STANDARDS.md → Python & TypeScript conventions
│   ├── TESTING_GUIDE.md    → pytest & Playwright patterns
│   ├── COMMON_TASKS.md     → Frequent development tasks
│   └── TROUBLESHOOTING.md  → Common issues & solutions
│
└── implementation/      → Sprint history & roadmap
    ├── STATUS.md            → Current implementation state
    ├── PHASE_01_FOUNDATION.md (Sprints 1-6)
    ├── PHASE_02_FEATURES.md   (Sprints 7-12)
    ├── PHASE_03_BETA.md       (Sprints 13-15)
    ├── PHASE_04_LOVABLE.md    (Sprints 16-19)
    ├── PHASE_05_STABILIZATION.md (Sprints 20-21)
    ├── PHASE_06_SECURITY.md   (Sprints 22-24)
    ├── PHASE_07_PLATFORM.md   (Sprints 25-27)
    ├── PHASE_08_ENTERPRISE.md (Sprints 28-30)
    ├── PHASE_09_QUALITY.md    (Sprints 31-36)
    ├── PHASE_10_FOUNDATIONS.md (Sprint 37)
    ├── TECHNICAL_DEBT.md
    └── FUTURE_ENHANCEMENTS.md
```

---

## Legacy Documents (Deprecated)

The following documents have been restructured for better navigation. They are kept for backward compatibility but are no longer maintained:

| Old Document | New Location | Notes |
|--------------|--------------|-------|
| `01_TECHNISCHE_ARCHITEKTUR.md` | [architecture/](architecture/) | Split into OVERVIEW, TECH_STACK, DATA_MODEL |
| `02_USER_STORIES.md` | [implementation/](implementation/) | Archived - actual implementation tracked in PHASE docs |
| `03_CLAUDE_CODE_GUIDE.md` | [development/](development/) | Merged into CODING_STANDARDS and COMMON_TASKS |
| `04_ARCHITECTURE_DECISIONS.md` | [architecture/DECISIONS.md](architecture/DECISIONS.md) | Moved to architecture directory |
| `05_IMPLEMENTATION_PLAN.md` | [implementation/](implementation/) | Split by phase (10 documents) |
| `06_LOVABLE_FEATURES.md` | [02_USER_STORIES.md](../02_USER_STORIES.md) | **Deleted** - consolidated into 02_USER_STORIES.md |
| `07_LOVABLE_REBUILD_PLAN.md` | [architecture/DECISIONS.md](architecture/DECISIONS.md) | **Deleted** - historical context in ADRs |

---

## Search Index

Find documentation by keyword:

| Topic | Document |
|-------|----------|
| **API Endpoints** | [api/API_REFERENCE.md](api/API_REFERENCE.md) |
| **Architecture Decisions** | [architecture/DECISIONS.md](architecture/DECISIONS.md) |
| **Authentication** | [modules/auth.md](modules/auth.md) |
| **Background Jobs** | [architecture/TECH_STACK.md](architecture/TECH_STACK.md#background-jobs) |
| **Badges & Gamification** | [modules/badges.md](modules/badges.md) |
| **Coding Standards** | [development/CODING_STANDARDS.md](development/CODING_STANDARDS.md) |
| **Current Sprint** | [implementation/STATUS.md](implementation/STATUS.md) |
| **Database Schema** | [architecture/DATA_MODEL.md](architecture/DATA_MODEL.md) |
| **Deployment** | [../DEPLOYMENT.md](../DEPLOYMENT.md) |
| **Docker** | [../SETUP.md](../SETUP.md#docker) |
| **Embeddings** | [features/SCORING_GUIDE.md](features/SCORING_GUIDE.md#embeddings) |
| **Environment Setup** | [../SETUP.md](../SETUP.md) |
| **Frontend** | [modules/frontend.md](modules/frontend.md) |
| **Ingestion** | [features/INGESTION_GUIDE.md](features/INGESTION_GUIDE.md) |
| **KanBan Pipelines** | [modules/projects.md](modules/projects.md) |
| **LLM Integration** | [features/SCORING_GUIDE.md](features/SCORING_GUIDE.md#llm-providers) |
| **Migrations** | [../DEPLOYMENT.md](../DEPLOYMENT.md#migrations) |
| **Modules Overview** | [modules/MODULES_OVERVIEW.md](modules/MODULES_OVERVIEW.md) |
| **Papers** | [modules/papers.md](modules/papers.md) |
| **Permissions & RBAC** | [modules/auth.md](modules/auth.md#permissions) |
| **Scoring System** | [features/SCORING_GUIDE.md](features/SCORING_GUIDE.md) |
| **Search** | [features/SEARCH_GUIDE.md](features/SEARCH_GUIDE.md) |
| **Security** | [architecture/TECH_STACK.md](architecture/TECH_STACK.md#security) |
| **Sprint History** | [implementation/](implementation/) |
| **Tech Stack** | [architecture/TECH_STACK.md](architecture/TECH_STACK.md) |
| **Technical Debt** | [implementation/TECHNICAL_DEBT.md](implementation/TECHNICAL_DEBT.md) |
| **Testing** | [development/TESTING_GUIDE.md](development/TESTING_GUIDE.md) |
| **Troubleshooting** | [development/TROUBLESHOOTING.md](development/TROUBLESHOOTING.md) |

---

## Documentation Principles

1. **Single Source of Truth** - Each piece of information lives in exactly one place
2. **Cross-Referencing** - Documents link to related docs, no content duplication
3. **Modular** - Each document focuses on one topic, <1,000 lines
4. **Navigable** - Clear paths from high-level overviews to detailed guides
5. **Maintainable** - Updates affect minimal number of files

---

## For AI Coding Agents

**Start here:** [../CLAUDE.md](../CLAUDE.md) (350 lines) - Lean entry point with cross-references

**For specific queries:**
1. Read CLAUDE.md for quick context
2. Follow links to specialized documents
3. Read only what you need (73% context window reduction vs old structure)

**Example navigation paths:**
- "Implement new API endpoint" → CLAUDE.md → modules/MODULES_OVERVIEW.md → modules/{module}.md
- "Understand scoring" → CLAUDE.md → features/SCORING_GUIDE.md
- "Check sprint status" → CLAUDE.md → implementation/STATUS.md

---

Last updated: 2026-02-10
