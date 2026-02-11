# Paper Scraper - Claude Code Development Guide

> **📖 Documentation Navigation:** This guide focuses on **working with Claude Code** on this project.
> For detailed technical information:
> - **[CLAUDE.md](CLAUDE.md)** - AI agent quick start & project overview
> - **[docs/INDEX.md](docs/INDEX.md)** - Master navigation hub
> - **[docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)** - Code conventions & style
> - **[docs/development/TESTING_GUIDE.md](docs/development/TESTING_GUIDE.md)** - Testing patterns & best practices
> - **[docs/development/COMMON_TASKS.md](docs/development/COMMON_TASKS.md)** - Frequent development tasks
> - **[docs/development/TROUBLESHOOTING.md](docs/development/TROUBLESHOOTING.md)** - Common issues & solutions

---

## Overview

This guide defines best practices for developing Paper Scraper with Claude Code. It covers workflows, prompts, and implementation checklists specific to AI-assisted development.

---

## 1. Project Context for Claude Code

### Quick Reference

**What is Paper Scraper?**
AI-powered SaaS platform for analyzing scientific publications (TTOs, VCs, Corporate Innovation)

**Current State:**
- ✅ 37 sprints completed (10 phases)
- 24 backend modules, 208+ API endpoints
- 841 tests, 40+ database tables
- Full-stack TypeScript/Python application

**Core Features:**
- Multi-source paper ingestion (OpenAlex, PubMed, arXiv, DOI, PDF)
- 6-dimensional AI scoring (Novelty, IP-Potential, Marketability, Feasibility, Commercialization, Team Readiness)
- KanBan pipeline management
- Semantic & fulltext search
- Author CRM & technology transfer workflows

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy (async), PostgreSQL 16 + pgvector
- Frontend: React 19, TypeScript, Vite, TailwindCSS, Shadcn/UI
- Queue: arq (async-native) + Redis
- AI/ML: Multi-provider LLMs (GPT-5 mini default), text-embedding-3-small

**For complete context:** Read [CLAUDE.md](CLAUDE.md) (350 lines, optimized for AI agents)

---

## 2. Development Workflow with Claude Code

### 2.1 Recommended Workflow

**1. Understand the Context**
```bash
# Start with project overview
cat CLAUDE.md

# Navigate to relevant documentation
cat docs/INDEX.md

# Check current implementation status
cat docs/implementation/STATUS.md
```

**2. Read Relevant Module Docs**
```bash
# For module changes
cat docs/modules/MODULES_OVERVIEW.md
cat docs/modules/<module_name>.md

# For feature implementation
cat docs/features/SCORING_GUIDE.md  # AI scoring
cat docs/features/INGESTION_GUIDE.md  # Paper import
cat docs/features/SEARCH_GUIDE.md  # Search implementation
```

**3. Plan Before Coding**
- Use `/plan` mode for non-trivial features
- Read existing code patterns before proposing changes
- Check [docs/development/COMMON_TASKS.md](docs/development/COMMON_TASKS.md) for established workflows

**4. Implement with Tests**
- Write tests FIRST for TDD (or immediately after implementation)
- Run `pytest tests/` frequently
- Check coverage with `pytest --cov=paper_scraper`

**5. Document as You Go**
- Update module docs if adding features
- Update API_REFERENCE.md if changing endpoints
- Keep CLAUDE.md in sync with major architectural changes

**6. Review Before Commit**
- Run full test suite: `pytest tests/ -v`
- Run E2E tests: `cd e2e && npm test`
- Check linting: `ruff check .`
- Verify type hints: `mypy paper_scraper/`

### 2.2 Effective Prompts for Claude Code

**Good Prompts:**
- ✅ "Implement a new scoring dimension for environmental impact following the existing pattern in scoring/dimensions/"
- ✅ "Add pagination to the /api/v1/papers endpoint maintaining backward compatibility"
- ✅ "Refactor the ingestion service to use the new unified pipeline (see docs/features/INGESTION_GUIDE.md)"

**Ineffective Prompts:**
- ❌ "Make the app better"
- ❌ "Add some tests"
- ❌ "Fix the bug" (without context)

**Prompt Templates:**

**For new API endpoint:**
```
Add a new endpoint GET /api/v1/<module>/<resource> following these patterns:
1. Read docs/modules/<module>.md for context
2. Add schema to modules/<module>/schemas.py (Pydantic v2)
3. Add service method to modules/<module>/service.py (async, type-hinted)
4. Add router endpoint to modules/<module>/router.py (with permissions)
5. Write tests in tests/modules/<module>/test_<resource>.py
6. Update docs/api/API_REFERENCE.md
```

**For new background job:**
```
Implement a new arq background job for <task>:
1. Create async function in jobs/<task_name>.py
2. Register in jobs/worker.py WorkerSettings.functions list
3. If periodic: add arq.cron() schedule to WorkerSettings
4. Add tests in tests/jobs/test_<task_name>.py
5. Document in docs/architecture/TECH_STACK.md#background-jobs
```

**For new scoring dimension:**
```
Add a new scoring dimension "<dimension_name>" following the 6-dimension pattern:
1. Read docs/features/SCORING_GUIDE.md for architecture
2. Create Jinja2 prompt template in scoring/prompts/<dimension>.jinja2
3. Implement DimensionScorer in scoring/dimensions/<dimension>.py
4. Register in scoring/orchestrator.py
5. Add field to PaperScore model + migration
6. Update PaperScoreResponse schema
7. Add tests in tests/modules/scoring/test_<dimension>.py
8. Update frontend InnovationRadar to show new dimension
```

### 2.3 Context Management

**For Backend Tasks:**
```
# Essential context (read in order)
1. CLAUDE.md - Project overview
2. docs/modules/<module>.md - Module architecture
3. paper_scraper/modules/<module>/models.py - Data models
4. paper_scraper/modules/<module>/service.py - Business logic
5. tests/modules/<module>/ - Existing test patterns
```

**For Frontend Tasks:**
```
# Essential context
1. CLAUDE.md - Project overview
2. docs/modules/frontend.md - Frontend architecture
3. frontend/src/lib/api.ts - API client
4. frontend/src/pages/<PageName>.tsx - Existing page patterns
5. frontend/src/hooks/use<Resource>.ts - TanStack Query patterns
```

**For Scoring/AI Tasks:**
```
# Essential context
1. docs/features/SCORING_GUIDE.md - Complete scoring architecture
2. paper_scraper/modules/scoring/llm_client.py - LLM abstraction
3. paper_scraper/modules/scoring/orchestrator.py - Pipeline coordination
4. paper_scraper/modules/scoring/prompts/ - Existing prompt templates
5. paper_scraper/modules/scoring/dimensions/ - Dimension implementations
```

**For Database Changes:**
```
# Essential context
1. docs/architecture/DATA_MODEL.md - Complete schema
2. alembic/versions/ - Existing migrations
3. paper_scraper/modules/<module>/models.py - SQLAlchemy models
4. docs/architecture/TECH_STACK.md#database - PostgreSQL + pgvector patterns
```

---

## 3. Implementation Checklist

Use this checklist for every user story or feature implementation:

### ✅ Code

- [ ] Read relevant module documentation before changing code
- [ ] Follow async/await patterns (no blocking I/O)
- [ ] Add type hints to all functions
- [ ] Use Pydantic v2 for all DTOs/schemas
- [ ] Implement tenant isolation (`organization_id` filtering)
- [ ] Add docstrings (Google-style) to public functions
- [ ] Use absolute imports (`from paper_scraper.core import ...`)
- [ ] No hardcoded values (use `core/config.py` settings)
- [ ] Log important events (`logger.info()`, `logger.warning()`)

**Style Guide:** See [docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)

### ✅ Tests

- [ ] Write unit tests for service layer (`tests/modules/<module>/`)
- [ ] Write integration tests for API endpoints (`tests/api/`)
- [ ] Test happy path + error cases
- [ ] Test tenant isolation (organization_id filtering)
- [ ] Mock external API calls (OpenAlex, LLMs, etc.)
- [ ] Use pytest fixtures for common setup
- [ ] Achieve ≥80% coverage for critical paths
- [ ] Run full test suite before commit: `pytest tests/ -v`

**Testing Guide:** See [docs/development/TESTING_GUIDE.md](docs/development/TESTING_GUIDE.md)

### ✅ API (if applicable)

- [ ] Add endpoint to module router (`modules/<module>/router.py`)
- [ ] Use proper HTTP methods (GET, POST, PATCH, DELETE)
- [ ] Add permission decorators (`@require_permission()`)
- [ ] Include OpenAPI documentation (docstrings)
- [ ] Return appropriate HTTP status codes
- [ ] Handle pagination for list endpoints (limit, offset)
- [ ] Validate input with Pydantic schemas
- [ ] Update [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)

### ✅ Database (if applicable)

- [ ] Create Alembic migration (`alembic revision --autogenerate -m "..."`)
- [ ] Add indexes for frequently queried columns
- [ ] Use `organization_id` for tenant isolation
- [ ] Add foreign key constraints
- [ ] Test migration up/down (`alembic upgrade head` / `alembic downgrade -1`)
- [ ] Import new models in `alembic/env.py` and `tests/conftest.py`
- [ ] Update [docs/architecture/DATA_MODEL.md](docs/architecture/DATA_MODEL.md)

### ✅ Frontend (if applicable)

- [ ] Create TanStack Query hook in `hooks/use<Resource>.ts`
- [ ] Use Shadcn/UI components (`components/ui/`)
- [ ] Implement loading/error states
- [ ] Add form validation with Zod
- [ ] Make responsive (mobile + desktop)
- [ ] Test with React Developer Tools
- [ ] Run E2E tests: `cd e2e && npm test`
- [ ] Update [docs/modules/frontend.md](docs/modules/frontend.md) if needed

### ✅ Documentation

- [ ] Update CLAUDE.md if architecture changed
- [ ] Update module doc in `docs/modules/<module>.md` if features added
- [ ] Add docstrings to all public functions
- [ ] Update API_REFERENCE.md if endpoints changed
- [ ] Update DATA_MODEL.md if schema changed
- [ ] Add comments for non-obvious logic

### ✅ Review

- [ ] Code passes all tests (`pytest tests/ -v`)
- [ ] Code passes linting (`ruff check .`)
- [ ] Code passes type checking (`mypy paper_scraper/`)
- [ ] No secrets/credentials in code (use `.env`)
- [ ] No commented-out code (remove or document why)
- [ ] Git commit message is clear and follows convention
- [ ] PR description explains what/why (not just how)

---

## 4. Common Development Tasks

**Quick Reference (detailed guide:** [docs/development/COMMON_TASKS.md](docs/development/COMMON_TASKS.md)**)**

### Add New API Endpoint

```bash
# 1. Schema
vim paper_scraper/modules/<module>/schemas.py

# 2. Service method
vim paper_scraper/modules/<module>/service.py

# 3. Router endpoint
vim paper_scraper/modules/<module>/router.py

# 4. Tests
vim tests/modules/<module>/test_<resource>.py

# 5. Run tests
pytest tests/modules/<module>/ -v
```

### Add New Scoring Dimension

```bash
# 1. Prompt template
vim paper_scraper/modules/scoring/prompts/<dimension>.jinja2

# 2. Scorer implementation
vim paper_scraper/modules/scoring/dimensions/<dimension>.py

# 3. Register in orchestrator
vim paper_scraper/modules/scoring/orchestrator.py

# 4. Database migration
alembic revision --autogenerate -m "Add <dimension> scoring"
alembic upgrade head

# 5. Update frontend
vim frontend/src/components/InnovationRadar.tsx

# 6. Tests
vim tests/modules/scoring/test_<dimension>.py
pytest tests/modules/scoring/ -v
```

### Add Background Job

```bash
# 1. Create job
vim paper_scraper/jobs/<task_name>.py

# 2. Register in worker
vim paper_scraper/jobs/worker.py

# 3. Tests
vim tests/jobs/test_<task_name>.py
pytest tests/jobs/ -v

# 4. Test manually
arq paper_scraper.jobs.worker.WorkerSettings
```

### Run Full Test Suite

```bash
# Backend unit + integration tests
pytest tests/ -v --cov=paper_scraper

# Frontend tests
cd frontend && npm test

# E2E tests
cd e2e && npm test
```

---

## 5. Code Quality Guidelines

**Full guidelines:** [docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)

### Python Quick Reference

**✅ DO:**
```python
# Async, typed, documented
async def get_paper(
    db: AsyncSession,
    paper_id: UUID,
    org_id: UUID,
) -> Paper | None:
    """Retrieve paper with tenant isolation."""
    query = select(Paper).where(
        Paper.id == paper_id,
        Paper.organization_id == org_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

**❌ DON'T:**
```python
# Blocking, untyped, undocumented
def get_paper(db, id):
    return db.query(Paper).filter(Paper.id == id).first()
```

### TypeScript Quick Reference

**✅ DO:**
```typescript
// Typed, uses TanStack Query
const usePapers = (filters: PaperFilters) => {
  return useQuery({
    queryKey: ['papers', filters],
    queryFn: () => api.papers.list(filters),
  });
};
```

**❌ DON'T:**
```typescript
// Untyped, manual state management
const usePapers = () => {
  const [papers, setPapers] = useState<any>([]);
  useEffect(() => {
    fetch('/papers').then(r => setPapers(r));
  }, []);
  return papers;
};
```

---

## 6. Troubleshooting

**Full troubleshooting guide:** [docs/development/TROUBLESHOOTING.md](docs/development/TROUBLESHOOTING.md)

### Quick Fixes

**Database Connection Issues:**
```bash
# Check PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart db

# Check connection
docker-compose exec db psql -U postgres -d paperscraper -c "SELECT 1"
```

**LLM Rate Limiting:**
```bash
# Check current provider
echo $LLM_PROVIDER

# Switch to Ollama for local development
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

**Slow Tests:**
```bash
# Run specific module only
pytest tests/modules/papers/ -v

# Skip slow E2E tests
pytest tests/ -v -m "not slow"

# Parallel execution
pytest tests/ -v -n auto
```

**Migration Conflicts:**
```bash
# Check current revision
alembic current

# Downgrade one step
alembic downgrade -1

# Regenerate migration
alembic revision --autogenerate -m "Fix: <description>"
```

---

## 7. Sprint Implementation with Claude Code

For implementing new sprints or features, follow this workflow:

### Step 1: Plan
```
/plan

Read:
- docs/implementation/STATUS.md (what's done)
- docs/implementation/FUTURE_ENHANCEMENTS.md (what's planned)
- Relevant module docs

Create implementation plan with:
- Technical approach
- Files to modify/create
- Testing strategy
- Documentation updates needed
```

### Step 2: Implement
```
Follow the Implementation Checklist (Section 3)

Break work into atomic commits:
- "Add <resource> model and migration"
- "Implement <resource> service layer"
- "Add <resource> API endpoints"
- "Add <resource> tests"
```

### Step 3: Test
```
# Unit tests
pytest tests/modules/<module>/ -v

# Integration tests
pytest tests/api/ -v

# E2E tests (if UI changes)
cd e2e && npm test

# Full suite
pytest tests/ -v --cov=paper_scraper
```

### Step 4: Document
```
Update:
- docs/modules/<module>.md
- docs/api/API_REFERENCE.md (if API changed)
- docs/architecture/DATA_MODEL.md (if schema changed)
- docs/implementation/STATUS.md (mark features complete)
- CLAUDE.md (if major architectural change)
```

### Step 5: Commit
```
# Use conventional commits
git commit -m "feat(<module>): add <feature>

- Implement <detail>
- Add tests with 90% coverage
- Update API documentation

Closes #<issue>"
```

---

## 8. Resources

**Project Documentation:**
- **[docs/INDEX.md](docs/INDEX.md)** - Master navigation
- **[docs/implementation/STATUS.md](docs/implementation/STATUS.md)** - Current state
- **[docs/modules/MODULES_OVERVIEW.md](docs/modules/MODULES_OVERVIEW.md)** - All 24 modules
- **[docs/features/](docs/features/)** - Feature guides (scoring, ingestion, search, pipeline)
- **[docs/development/](docs/development/)** - Development guides

**External Resources:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [pgvector Docs](https://github.com/pgvector/pgvector)
- [arq Docs](https://arq-docs.helpmanual.io/)

---

**Last Updated:** 2026-02-10
**Document Status:** Refactored to focus on Claude Code workflows with cross-references
**Lines:** 540 (reduced from 843 = 36% reduction)
