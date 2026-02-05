# Sprint Implementation Command

Implement a specific sprint from the PaperScraper implementation plan with multi-agent review.

## Arguments

$ARGUMENTS - The sprint number to implement (e.g., "7", "8", or "7-8" for a range)

## Instructions

You are tasked with implementing Sprint $ARGUMENTS from the PaperScraper project. Follow this structured workflow:

---

## Phase 1: Sprint Implementation

### Step 1.1: Read the Implementation Plan

First, read the implementation plan to understand what needs to be built:

```
Read: 05_IMPLEMENTATION_PLAN.md
```

Find the section for Sprint $ARGUMENTS and extract:
- All tasks and subtasks
- Files to create or modify
- API endpoints to implement
- Tests to write
- Definition of Done criteria

### Step 1.2: Create a Todo List

Use the TodoWrite tool to create a detailed checklist of all items from the sprint plan. Break down each task into actionable items.

### Step 1.3: Implement the Sprint

For each task in the sprint:

1. **Research first**: Check existing code patterns in the codebase
2. **Implement**: Write the code following project conventions from CLAUDE.md
3. **Test**: Run tests after each significant change
4. **Mark complete**: Update the todo list as you finish each item

Follow these conventions:
- Python: Async/await, type hints, Google-style docstrings
- TypeScript: Strict mode, no `any`, TanStack Query for server state
- Always filter by `organization_id` for tenant isolation
- Use existing UI components from `frontend/src/components/ui/`

### Step 1.4: Verify Implementation

Before moving to review phase:
```bash
poetry run pytest tests/ -v
cd frontend && npm run type-check && npm run build
```

---

## Phase 2: Specialist Agent Review

After completing the implementation, invoke each relevant specialist agent to review their domain. Run these agents in parallel where possible.

### 2.1: Backend Review (if backend code was written)

```
Task: python-backend-dev agent
Prompt: Review the Sprint $ARGUMENTS implementation in the paper_scraper/ directory. Check for:
- Async patterns and proper await usage
- Type hints completeness
- Error handling and edge cases
- Tenant isolation (organization_id filtering)
- API design consistency
Provide specific improvement suggestions with file paths and line numbers.
```

### 2.2: Frontend Review (if frontend code was written)

```
Task: react-frontend-dev agent
Prompt: Review the Sprint $ARGUMENTS frontend implementation in frontend/src/. Check for:
- TypeScript types (no `any`)
- TanStack Query usage patterns
- Component composition and reusability
- Loading/error/empty state handling
- Accessibility and responsive design
Provide specific improvement suggestions.
```

### 2.3: Database Review (if models/migrations were created)

```
Task: database-architect agent
Prompt: Review the Sprint $ARGUMENTS database changes. Check:
- Model design and relationships
- Index strategy (especially for pgvector)
- Migration correctness and rollback safety
- Query efficiency (N+1 problems)
Provide specific optimization suggestions.
```

### 2.4: AI/Scoring Review (if LLM code was written)

```
Task: ai-ml-scoring-engineer agent
Prompt: Review the Sprint $ARGUMENTS AI/scoring implementation. Check:
- Prompt design and effectiveness
- Response parsing robustness
- Error handling for LLM failures
- Cost optimization opportunities
Provide specific improvement suggestions.
```

### 2.5: Test Coverage Review

```
Task: test-engineer agent
Prompt: Review test coverage for Sprint $ARGUMENTS. Check:
- Unit test coverage for new code
- Edge cases and error scenarios
- Mocking strategy for external APIs
- E2E test coverage for new features
Suggest additional tests to write.
```

### 2.6: DevOps Review

```
Task: devops-engineer agent
Prompt: Review Sprint $ARGUMENTS for DevOps concerns:
- Docker configuration if changed
- Environment variables needed
- Background job configuration
- Deployment considerations
Provide recommendations.
```

### 2.7: Security Review

```
Task: security-engineer agent
Prompt: Security audit for Sprint $ARGUMENTS implementation:
- Input validation completeness
- Authorization checks
- Tenant isolation verification
- Sensitive data handling
- OWASP Top 10 considerations
Flag any security issues with severity ratings.
```

### 2.8: Implement Agent Feedback

After receiving feedback from all specialist agents:
1. Prioritize by severity (security issues first)
2. Implement the suggested improvements
3. Re-run tests to verify fixes
4. Update the todo list

---

## Phase 3: Architecture & Code Quality Review

After implementing specialist feedback, invoke the built-in review agents.

### 3.1: Code Review

```
Task: feature-dev:code-reviewer agent (sonnet)
Prompt: Review all code changes from Sprint $ARGUMENTS for:
- Bug risks and logic errors
- Code quality issues
- Security vulnerabilities
- Adherence to project conventions
Only report high-confidence issues.
```

### 3.2: Architecture Analysis

```
Task: feature-dev:code-architect agent (sonnet)
Prompt: Analyze the Sprint $ARGUMENTS implementation architecture:
- Does it follow existing patterns?
- Are abstractions appropriate?
- Any design improvements needed?
- Technical debt introduced?
```

### 3.3: Code Exploration

```
Task: feature-dev:code-explorer agent (sonnet)
Prompt: Explore how Sprint $ARGUMENTS integrates with existing code:
- Identify any missing integrations
- Check for consistency with similar features
- Find any orphaned or dead code
```

### 3.4: Code Simplification

```
Task: code-simplifier:code-simplifier agent (opus)
Prompt: Analyze Sprint $ARGUMENTS code for simplification:
- Find duplicate patterns that could be consolidated
- Identify over-engineered solutions
- Suggest cleaner implementations
- Remove unnecessary complexity
Focus only on code written in this sprint.
```

### 3.5: Implement Final Feedback

Implement improvements from the architecture and quality review:
1. Apply code simplifications
2. Fix any architectural issues
3. Address code review findings
4. Final test run

---

## Phase 4: Completion

### 4.1: Final Verification

```bash
# Run all tests
poetry run pytest tests/ -v --cov=paper_scraper

# Type checking
poetry run mypy paper_scraper
cd frontend && npm run type-check

# Linting
poetry run ruff check .

# Build verification
cd frontend && npm run build
```

### 4.2: Update Documentation

Update the implementation plan to mark Sprint $ARGUMENTS as complete:
- Change status from "Pending" to "Complete"
- Add any notes about implementation decisions
- Document any deviations from the original plan
- Note suggested tasks for future sprints

### 4.3: Summary Report

Provide a summary of what was implemented:
- Features completed
- Files created/modified
- Tests added
- Issues found and fixed during review
- Any remaining items for future sprints

---

## Error Handling

If you encounter blocking issues:

1. **Test failures**: Fix them before proceeding to review phase
2. **Missing dependencies**: Add them and document in the sprint summary
3. **Unclear requirements**: Check CLAUDE.md and existing code patterns first, then ask for clarification
4. **Agent unavailable**: Skip that review and note it in the summary

---

## Notes

- Always use the TodoWrite tool to track progress throughout
- Run tests frequently during implementation
- Commit logical chunks of work (don't wait until the end)
- If a sprint is too large, break it into multiple sessions
