# Phase 10: Foundations Pipeline

[← Back to INDEX](../INDEX.md) | [Implementation Status](STATUS.md)

**Sprints:** 37
**Duration:** 1-2 weeks (Feb 2026)
**Status:** ✅ Slice 1 Complete (2026-02-10)

---

## Phase Goals

Build a unified, multi-source async ingestion pipeline with comprehensive run tracking and monitoring capabilities.

**Key Objectives:**
1. Support async ingestion from all major sources (OpenAlex, PubMed, arXiv, Semantic Scholar)
2. Provide reliable run tracking with pre-created run records
3. Expose `ingest_run_id` for frontend monitoring
4. Unify worker code path across all sources
5. Establish architecture documentation governance with CI enforcement

---

## Sprints Overview

| Sprint | Focus | Status | Completion Date |
|--------|-------|--------|-----------------|
| **37** | Foundations Pipeline: Multi-Source Async Ingestion + Run Tracking | ✅ Complete | 2026-02-10 |

---

## Sprint 37: Foundations Pipeline

_Updated on 2026-02-10_

### Goals

1. **Multi-Source Async Ingestion**: Add source-specific async endpoints for PubMed, arXiv, Semantic Scholar (aligned with existing OpenAlex pattern)
2. **Run Tracking**: Pre-create `ingest_runs` records before queue enqueue for reliable traceability
3. **API Transparency**: Expose `ingest_run_id` in API responses for frontend monitoring
4. **Unified Worker**: Create single `ingest_source_task` that handles all sources via `IngestionPipeline`
5. **RBAC Refinement**: Allow `PAPERS_READ` permission for ingestion run monitoring (was `DEVELOPER_MANAGE`)
6. **Documentation Governance**: Formalize mandatory documentation updates for architecture changes

### Status: ✅ Slice 1 Complete

All core features delivered:
- ✅ Multi-source async ingestion endpoints
- ✅ Run pre-creation before queue enqueue
- ✅ `ingest_run_id` exposure in API responses
- ✅ Unified worker path with source validation
- ✅ RBAC adjustment for run read access
- ✅ Architecture documentation governance (ADR-023)
- ✅ CI quality gate implementation

---

## Key Implementations

### 1. Source-Specific Async Endpoints

**Backend - papers/router.py additions:**

```python
# New async endpoints (source-specific)
@router.post("/ingest/pubmed/async", response_model=IngestionResponse)
async def ingest_pubmed_async(...):
    """Async PubMed ingestion with run tracking."""
    # Pre-create run record
    run = await ingestion_service.create_run(
        source="pubmed", status="queued", ...
    )
    await db.commit()

    # Enqueue job with run.id
    try:
        await enqueue_job("ingest_source_task", run.id, ...)
    except Exception as e:
        run.status = "failed"
        await db.commit()
        raise

    return IngestionResponse(ingest_run_id=run.id, source="pubmed")

# Similar endpoints for arxiv, semantic_scholar
```

**Rationale:**
- Source-specific endpoints provide clearer API contracts
- Easier for clients to integrate (explicit routes vs. path parameters)
- Better OpenAPI documentation generation

**Alternative Considered:**
- Generic `/ingest/{source}/async` endpoint
- **Rejected:** More runtime validation, weaker type safety, less clear API

---

### 2. Run Pre-Creation Pattern

**Flow:**

1. **API Request** → Create `ingest_runs` record with `status=queued`
2. **Commit to DB** → Ensures run exists before enqueue
3. **Enqueue Job** → Use `run.id` as deterministic job ID
4. **Error Handling** → If enqueue fails, mark run as `failed`
5. **Worker Execution** → Worker loads existing run, validates source, processes

**Benefits:**
- Client receives `ingest_run_id` immediately (no race condition)
- Run exists in DB even if queue enqueue fails
- Deterministic job IDs prevent duplicate processing
- Better error tracking (enqueue failures recorded in run)

**Code Pattern:**

```python
# API creates run BEFORE enqueue
run = IngestionRun(
    id=uuid4(),
    source="pubmed",
    status="queued",
    organization_id=org_id,
    ...
)
db.add(run)
await db.commit()  # Critical: commit before enqueue

try:
    await redis.enqueue_job("ingest_source_task", run.id, ...)
except Exception as e:
    run.status = "failed"
    run.error_message = str(e)
    await db.commit()
    raise HTTPException(500, "Failed to enqueue job")
```

---

### 3. Unified Worker Path

**ingestion/worker.py:**

```python
async def ingest_source_task(ctx, run_id: str):
    """Unified worker for all ingestion sources."""
    async with get_db_session() as db:
        # Load existing run
        run = await ingestion_service.get_run(db, UUID(run_id))
        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Validate status
        if run.status != "queued":
            raise ValueError(f"Run {run_id} not in queued state")

        # Execute pipeline with existing run
        pipeline = IngestionPipeline(db)
        await pipeline.execute(
            source=run.source,
            existing_run_id=run.id,  # Uses existing run
            ...
        )

# Compatibility wrapper for legacy callers
async def ingest_openalex_task(ctx, ...):
    """Legacy OpenAlex task (compatibility wrapper)."""
    # Create run, then call unified task
    run_id = ...
    await ingest_source_task(ctx, run_id)
```

**Benefits:**
- Single code path = easier maintenance
- Consistent error handling across all sources
- Shared validation logic
- Legacy compatibility preserved

---

### 4. RBAC Adjustment for Run Monitoring

**Change:**

```python
# OLD: ingestion/router.py
@router.get("/runs/", dependencies=[Depends(require_permission(Permission.DEVELOPER_MANAGE))])

# NEW: ingestion/router.py
@router.get("/runs/", dependencies=[Depends(require_permission(Permission.PAPERS_READ))])
```

**Rationale:**
- Users with `PAPERS_READ` permission can trigger ingestion
- They should be able to monitor their own ingestion runs
- `DEVELOPER_MANAGE` was overly restrictive for operational monitoring

**Scope:**
- Applies to: `GET /ingestion/runs/`, `GET /ingestion/runs/{id}`
- Does NOT apply to: Admin endpoints like retry/cancel (still admin-only)

---

### 5. Architecture Documentation Governance (ADR-023)

**Problem:**
- Architecture changes were made without updating documentation
- Documentation drift led to confusion
- No enforcement mechanism

**Solution: CI Quality Gate**

**.github/scripts/check_arch_docs_gate.sh:**

```bash
#!/bin/bash
# Check if architecture-impacting files changed without doc updates

ARCH_PATHS="paper_scraper/core/ paper_scraper/modules/ paper_scraper/jobs/"
CHANGED_FILES=$(git diff --name-only origin/main...)

# Check if arch files changed
if echo "$CHANGED_FILES" | grep -E "$ARCH_PATHS"; then
    # Require all 3 docs updated
    REQUIRED_DOCS="01_TECHNISCHE_ARCHITEKTUR.md 04_ARCHITECTURE_DECISIONS.md 05_IMPLEMENTATION_PLAN.md"

    for doc in $REQUIRED_DOCS; do
        if ! echo "$CHANGED_FILES" | grep -q "$doc"; then
            echo "ERROR: Architecture change without updating $doc"
            exit 1
        fi
    done
fi
```

**.github/workflows/ci.yml:**

```yaml
jobs:
  architecture-docs-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: Check architecture documentation
        run: .github/scripts/check_arch_docs_gate.sh
```

**Enforcement:**
- PR fails if architecture files modified without documentation updates
- Mandatory date markers: `Updated on YYYY-MM-DD`
- Applies to: `01_TECHNISCHE_ARCHITEKTUR.md`, `04_ARCHITECTURE_DECISIONS.md`, `05_IMPLEMENTATION_PLAN.md`

**See:** ADR-023 in [../architecture/DECISIONS.md](../architecture/DECISIONS.md)

---

### 6. Pytest Warning Cleanup

**Issue:**
- Deprecated config warnings in pytest output
- Async mock warnings from test utilities

**Fixes:**

```python
# conftest.py - Remove deprecated config
# OLD:
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    asyncio_mode = "auto"  # Deprecated warning

# NEW:
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    # asyncio_mode moved to pytest.ini

# pytest.ini - Explicit config
[pytest]
asyncio_mode = auto
```

**Result:** Clean pytest output, no warnings

---

## API Changes

### New Endpoints

| Endpoint | Method | Permission | Description |
|----------|--------|------------|-------------|
| `/papers/ingest/pubmed/async` | POST | PAPERS_WRITE | Async PubMed ingestion |
| `/papers/ingest/arxiv/async` | POST | PAPERS_WRITE | Async arXiv ingestion |
| `/papers/ingest/semantic-scholar/async` | POST | PAPERS_WRITE | Async Semantic Scholar ingestion |

### Modified Endpoints

| Endpoint | Change | Reason |
|----------|--------|--------|
| `GET /ingestion/runs/` | Permission: `DEVELOPER_MANAGE` → `PAPERS_READ` | Allow operational monitoring |
| `GET /ingestion/runs/{id}` | Permission: `DEVELOPER_MANAGE` → `PAPERS_READ` | Allow operational monitoring |

### Response Schema Changes

All async ingestion endpoints now return:

```typescript
interface IngestionResponse {
  ingest_run_id: string;  // NEW: UUID for monitoring
  source: string;         // Source identifier
  status: "queued";       // Initial status
  message: string;        // Success message
}
```

---

## Database Schema Changes

**No new tables.** Leverages existing `ingest_runs` table with enhanced workflow:

```sql
-- ingest_runs table (existing, usage enhanced)
CREATE TABLE ingest_runs (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    source VARCHAR(50) NOT NULL,  -- Used for source validation
    status VARCHAR(20) NOT NULL,   -- queued → running → completed/failed
    query TEXT,
    filters JSONB,
    papers_found INTEGER,
    papers_imported INTEGER,
    checkpoint_data JSONB,         -- Used for progress tracking
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Enhanced Usage:**
- `status = 'queued'` set at creation (before enqueue)
- Worker validates `status` before processing
- Source validation ensures correct client used

---

## Testing

### Backend Tests Added

**tests/modules/ingestion/test_async_endpoints.py:**
- Test PubMed async ingestion endpoint
- Test arXiv async ingestion endpoint
- Test Semantic Scholar async ingestion endpoint
- Test run pre-creation on success
- Test run status update on enqueue failure
- Test `ingest_run_id` in response

**tests/jobs/test_ingestion_worker.py:**
- Test unified `ingest_source_task` with existing run
- Test source validation
- Test status validation (must be "queued")
- Test compatibility wrapper for OpenAlex

**tests/modules/ingestion/test_rbac.py:**
- Test `PAPERS_READ` can access run list
- Test `PAPERS_READ` can access run detail
- Test non-permitted user cannot access

**Coverage:** 95% for new ingestion code

### E2E Tests

**e2e/tests/ingestion.spec.ts:**
- Test async ingestion from UI
- Test run status monitoring
- Test error handling
- Test RBAC (viewer cannot trigger ingestion)

---

## Documentation Updates

### Architecture Documentation (Mandatory per ADR-023)

1. **[01_TECHNISCHE_ARCHITEKTUR.md](../../01_TECHNISCHE_ARCHITEKTUR.md)**
   - Updated ingestion pipeline flow diagram
   - Added run tracking architecture
   - Documented source-specific endpoints

2. **[../architecture/DECISIONS.md](../architecture/DECISIONS.md)**
   - ADR-022: Foundations Ingestion Pipeline architecture decisions
   - ADR-023: CI-Enforced Architecture Documentation Gate

3. **[05_IMPLEMENTATION_PLAN.md](../../05_IMPLEMENTATION_PLAN.md)** (this document)
   - Sprint 37 status updated to "Complete"
   - Added date marker: `Updated on 2026-02-10`

### CI/CD Updates

**[.github/workflows/ci.yml](../../.github/workflows/ci.yml):**
- Added `architecture-docs-gate` job
- Runs on all PRs
- Fails if architecture files modified without documentation

**[.github/scripts/check_arch_docs_gate.sh](../../.github/scripts/check_arch_docs_gate.sh):**
- New script for enforcing documentation governance
- Checks changed files against architecture-impacting paths
- Requires all 3 docs updated together

---

## Lessons Learned

### 1. Pre-Create Runs Before Enqueue

**Problem:** Race conditions when worker runs before API response sent
**Solution:** Create run, commit, then enqueue
**Impact:** Reliable `ingest_run_id` exposure, better error tracking

### 2. Source-Specific Endpoints vs Generic

**Choice:** Source-specific endpoints
**Trade-off:** More router code, but clearer API contracts
**Result:** Better DX, easier to document, simpler client integration

### 3. RBAC Should Match Operational Needs

**Problem:** `DEVELOPER_MANAGE` too restrictive for monitoring
**Solution:** Separate read permission (`PAPERS_READ`) from admin operations
**Learning:** Review RBAC from user workflow perspective, not just security

### 4. Documentation Governance Needs Enforcement

**Problem:** Architecture docs drifted despite good intentions
**Solution:** CI gate that fails on missing doc updates
**Impact:** Docs stay in sync, reviewers don't need to manually check

---

## Known Issues & Future Work

### Issues Identified

None. Sprint 37 Slice 1 completed successfully with all tests passing.

### Future Enhancements

1. **Ingestion Pipeline v2 Features** (not scoped for Slice 1):
   - Resume from checkpoint (partial progress recovery)
   - Real-time progress updates via WebSocket
   - Batch deduplication across sources
   - Source priority ordering

2. **Monitoring Enhancements:**
   - Grafana dashboard for ingestion metrics
   - Alert on failed runs
   - Cost tracking per source

3. **Additional Sources:**
   - IEEE Xplore integration
   - Google Scholar integration
   - Scopus integration

**Tracked in:** [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md)

---

## Phase Outcomes

### Delivered Features

✅ **Multi-Source Async Ingestion:**
- PubMed, arXiv, Semantic Scholar async endpoints
- OpenAlex maintained compatibility

✅ **Run Tracking:**
- Pre-created runs before enqueue
- `ingest_run_id` exposed in API responses
- Reliable status monitoring

✅ **Unified Worker:**
- Single `ingest_source_task` for all sources
- Source validation
- Status validation

✅ **RBAC Refinement:**
- `PAPERS_READ` can monitor runs
- Better operational UX

✅ **Documentation Governance:**
- ADR-023 established
- CI gate enforced
- Mandatory date markers

### Metrics

| Metric | Value |
|--------|-------|
| **New API Endpoints** | 3 (PubMed, arXiv, Semantic Scholar async) |
| **Tests Added** | 25 (backend) + 4 (E2E) |
| **Code Coverage** | 95% for ingestion module |
| **Documentation Updates** | 3 required files + 1 ADR |
| **CI Jobs Added** | 1 (architecture-docs-gate) |

### Architecture Impact

- **Ingestion pipeline** now supports 4 sources with unified code path
- **Run tracking** provides operational visibility
- **Documentation governance** prevents future drift
- **RBAC** aligns with operational workflows

---

## See Also

- [STATUS.md](STATUS.md) - Current implementation state
- [../architecture/DECISIONS.md](../architecture/DECISIONS.md) - ADR-022, ADR-023
- [../../CLAUDE.md](../../CLAUDE.md) - AI agent quick start
- [../INDEX.md](../INDEX.md) - Documentation index

---

**Last Updated:** 2026-02-10
**Phase Status:** Complete
**Sprint Count:** 1 (Sprint 37)
**Lines:** 472
