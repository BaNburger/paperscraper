# User Story Implementation Workflow

You are implementing a user story for the **PaperScraper** platform. The user story is:

> $ARGUMENTS

Follow the 6-phase workflow below **in strict order**. Do NOT skip phases. Each phase has a clear output that feeds the next.

For project conventions, see [patterns.md](patterns.md).
For completion criteria, see [checklist.md](checklist.md).

---

## Phase 1: Clarify

**Goal:** Understand the user story completely before writing any code.

### 1.1 Parse the Story

Extract from the user story:
- **Role**: Who is the user? (e.g., TTO analyst, corporate researcher, admin)
- **Goal**: What do they want to accomplish?
- **Benefit**: Why does this matter?
- **Implicit requirements**: i18n (EN + DE), tenant isolation, mobile responsive, accessibility

### 1.2 Identify Ambiguities

Before proceeding, identify what's unclear:
- UX approach (new page vs. extending existing page vs. modal/dialog)
- Data model scope (new tables vs. extending existing ones)
- Integration points (which existing modules does this touch?)
- Permissions model (new permissions or reuse existing ones?)
- Navigation placement (sidebar position, mobile menu group)

### 1.3 Ask Clarifying Questions

Use the `AskUserQuestion` tool with 2-4 structured questions. Each question should have 2-4 concrete options with descriptions of trade-offs. Only ask questions where the answer materially affects the implementation.

Example patterns:
- "Which UX approach for [feature]?" → Standalone page / Extend existing page / Dialog-based
- "What data scope?" → New module with tables / Extend existing module / Frontend-only
- "Navigation?" → Main sidebar / Secondary sidebar / Settings sub-page / No dedicated nav

### 1.4 Output

After clarification, state the refined requirements as a bullet list:
- Feature name
- URL path (if applicable)
- Acceptance criteria (testable statements)
- Out of scope (explicitly excluded)

---

## Phase 2: Context

**Goal:** Deeply understand the existing codebase before designing anything.

### 2.1 Explore Related Code

Launch an `Explore` agent (subagent_type: "Explore") to find:
- Related backend modules in `paper_scraper/modules/`
- Related frontend pages in `frontend/src/pages/`
- Existing database models that will be referenced or extended
- UI components available for reuse in `frontend/src/components/ui/`
- Existing hooks and API methods that could be leveraged

### 2.2 Read Key Files

Read these files for context (only the relevant sections):
- `CLAUDE.md` — Project conventions and patterns
- `docs/architecture/DATA_MODEL.md` — Database schema (if new tables needed)
- The most similar existing module (e.g., if building a list page, study how `PapersPage` works)
- `frontend/src/config/routes.ts` — Current navigation structure
- `frontend/src/locales/en/translation.json` — i18n key naming patterns

### 2.3 Output

Produce a **context map**:
- **Files to create**: New files with their purpose
- **Files to modify**: Existing files and what changes
- **Code to reuse**: Existing services, components, hooks, utilities with file paths
- **Latest migration**: The current head revision ID (read from `alembic/versions/`)

---

## Phase 3: Plan

**Goal:** Design the implementation and get user approval before writing code.

### 3.1 Enter Plan Mode

Use the `EnterPlanMode` tool to switch to planning mode.

### 3.2 Design the Architecture

Write a comprehensive plan covering:

**Database** (if new tables needed):
- Table schemas with columns, types, FKs, indexes
- Migration revision ID and down_revision

**Backend** (if API needed):
- Module structure: `__init__.py`, `models.py`, `schemas.py`, `service.py`, `router.py`
- API endpoints: method, path, description, request/response schemas
- Business logic: key service methods with descriptions
- Registration: router prefix, tags, alembic/env.py imports, tests/conftest.py imports

**Frontend** (if UI needed):
- TypeScript types to add to `types/index.ts`
- API methods to add to `lib/api.ts`
- TanStack Query hooks (queries + mutations)
- Pages: layout wireframe (ASCII art), component breakdown
- Routes to add to `App.tsx` (lazy-loaded)
- Navigation entries in `config/routes.ts`
- i18n keys for both EN and DE (~list the key names)

### 3.3 Get Approval

Use `ExitPlanMode` to present the plan to the user. Do NOT proceed until approved.

---

## Phase 4: Execute

**Goal:** Implement the approved plan incrementally with progress tracking.

### 4.1 Create Todo List

Use `TodoWrite` to create a checklist from the plan. Typical order:
1. Database migration (if needed)
2. Backend models + schemas
3. Backend service + router
4. Register router + import models
5. Frontend types + API methods
6. Frontend hooks
7. Frontend page(s)
8. i18n keys (EN + DE)
9. Routes + navigation
10. Build verification

### 4.2 Implement

For each task:
1. **Mark as in_progress** before starting
2. **Write the code** following conventions from [patterns.md](patterns.md)
3. **Mark as completed** immediately after finishing

**Implementation rules:**
- Backend: async/await, type hints, tenant isolation (`organization_id`), `flush()` not `commit()`
- Frontend: TanStack Query, Shadcn/UI, `t('namespace.key', 'fallback')` for i18n
- Use `react-frontend-dev` agent for complex pages (it has access to all tools)
- Use `python-backend-dev` agent for complex backend logic
- Run agents in parallel when tasks are independent

### 4.3 Build Check

After all frontend changes:
```bash
cd frontend && npx tsc --noEmit && npx vite build
```

If TypeScript errors occur, fix them before proceeding.

---

## Phase 5: Test

**Goal:** Verify the feature works correctly at every layer.

### 5.1 Backend Tests

```bash
# If new pytest tests were written
cd /Users/bastianburger/Repos/PaperScraper && poetry run pytest tests/modules/<module>/ -v

# If migration was created, verify it applies cleanly
poetry run alembic upgrade head
```

### 5.2 Frontend Build

```bash
cd frontend && npx tsc --noEmit && npx vite build
```

### 5.3 Browser Testing

Use the Playwright MCP tools to test in the browser:

1. **Check backend is running**: `curl -s http://localhost:8000/docs`
   - If not running or missing new endpoints, restart: kill the uvicorn process and relaunch
   - Run `alembic upgrade head` if migration was created

2. **Navigate to the feature**: Log in and navigate to the new page
3. **Test empty state**: Verify empty state renders with correct i18n text
4. **Test create flow**: Fill form, submit, verify item appears
5. **Test detail/read flow**: Click into the item, verify all sections render
6. **Test delete flow**: Delete the item, verify it's removed
7. **Take screenshots** of key states for documentation

### 5.4 Specialist Reviews (parallel)

Launch these review agents **in parallel** using the Task tool:

**Security Review** (subagent_type: "security-engineer"):
- Input validation, authorization, tenant isolation, XSS/injection

**Code Review** (subagent_type: "feature-dev:code-reviewer", model: "sonnet"):
- Bug risks, logic errors, code quality, convention adherence

**Test Coverage** (subagent_type: "test-engineer"):
- Suggest unit tests, integration tests, E2E tests for the new feature

### 5.5 Fix Issues

Prioritize by severity: security > bugs > quality. Fix issues and re-run builds.

---

## Phase 6: Deploy

**Goal:** Package the work into a clean, reviewable delivery.

### 6.1 Review Changes

```bash
git status
git diff --stat
```

Summarize what was changed: files created, files modified, lines added/removed.

### 6.2 Commit

**Only if the user explicitly asks to commit.** If they do:
- Stage relevant files (NOT .env, credentials, or build artifacts)
- Write a conventional commit message summarizing the feature
- Include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

### 6.3 Pull Request (optional)

If the user asks for a PR:
- Create a branch if not already on one
- Push to remote
- Create PR with structured body (Summary, Test Plan, Screenshots)

### 6.4 Completion Report

Provide a final summary:
- **Feature**: What was built
- **Files**: Created and modified (with counts)
- **Endpoints**: New API endpoints (method + path)
- **Pages**: New frontend routes
- **Tests**: What was verified (build, browser, reviews)
- **Known limitations**: What doesn't work yet (e.g., no API key for embeddings)

---

## Error Recovery

| Problem | Action |
|---------|--------|
| API key missing (embedding/LLM) | Make the call graceful (try/except, return None), document as known limitation |
| Test failures | Fix before proceeding to next phase |
| Build errors | Fix immediately, re-run build |
| Backend not running | Restart uvicorn, run migrations |
| Browser can't launch | Clean up Playwright cache, retry |
| User rejects plan | Revise based on feedback, re-present |
| Unclear requirements | Use AskUserQuestion, never guess |
