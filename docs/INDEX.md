# PaperScraper Documentation Index

[← Back to README](../README.md)

## Canonical Architecture Docs (v2.0)
These root files are the source of truth for architecture and rollout decisions:
- [../01_TECHNISCHE_ARCHITEKTUR.md](../01_TECHNISCHE_ARCHITEKTUR.md)
- [../04_ARCHITECTURE_DECISIONS.md](../04_ARCHITECTURE_DECISIONS.md)
- [../05_IMPLEMENTATION_PLAN.md](../05_IMPLEMENTATION_PLAN.md)

## Strict Lint Commands
Run these before finalizing architecture-impacting work:

```bash
npm run lint:agents
npm run lint:all
```

Exceptions are only allowed via:
- [../.agent-lint-allowlist.yaml](../.agent-lint-allowlist.yaml)

## Quick Navigation

### Architecture and Platform
- Runtime architecture summary: [../01_TECHNISCHE_ARCHITEKTUR.md](../01_TECHNISCHE_ARCHITEKTUR.md)
- ADRs: [../04_ARCHITECTURE_DECISIONS.md](../04_ARCHITECTURE_DECISIONS.md)
- Cutover and runbook: [../05_IMPLEMENTATION_PLAN.md](../05_IMPLEMENTATION_PLAN.md)
- Supplemental architecture notes: [architecture/](architecture/)

### API and Modules
- API reference: [api/API_REFERENCE.md](api/API_REFERENCE.md)
- Module overview: [modules/MODULES_OVERVIEW.md](modules/MODULES_OVERVIEW.md)

### Development
- Coding standards: [development/CODING_STANDARDS.md](development/CODING_STANDARDS.md)
- Testing guide: [development/TESTING_GUIDE.md](development/TESTING_GUIDE.md)
- Common tasks: [development/COMMON_TASKS.md](development/COMMON_TASKS.md)

### Setup and Deployment
- Local setup: [../SETUP.md](../SETUP.md)
- Deployment guide: [../DEPLOYMENT.md](../DEPLOYMENT.md)

### Implementation Tracking
- Current status page: [implementation/STATUS.md](implementation/STATUS.md)
- Historical phase docs: [implementation/](implementation/)

## Documentation Policy
- Root architecture docs are canonical for v2.
- `docs/` contains supplemental and historical implementation material.
- Architecture-impacting changes must update canonical root docs in the same change.
