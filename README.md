# Paper Scraper

AI-powered SaaS platform for automated analysis of scientific publications.

**Target Users:** Technology Transfer Offices (TTOs), VCs, Corporate Innovation Teams

## Features

- **Paper Import** - DOI, OpenAlex, PubMed, arXiv, Crossref
- **5-Dimensional AI Scoring** - Novelty, IP Potential, Marketability, Feasibility, Commercialization
- **KanBan Pipeline** - Structured paper management workflow
- **Semantic Search** - Vector-based similarity using pgvector

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL 16 + pgvector (HNSW index) |
| Queue | arq (async-native) + Redis |
| Storage | MinIO (S3-compatible) |
| AI/LLM | GPT-5 mini (default), text-embedding-3-small |

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Install dependencies
poetry install

# 3. Start services
docker compose up -d

# 4. Run migrations
poetry run alembic upgrade head

# 5. Start server
poetry run uvicorn paper_scraper.api.main:app --reload --port 8000
```

API Docs: http://localhost:8000/docs

## Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](SETUP.md) | Detailed setup guide with troubleshooting |
| [CLAUDE.md](CLAUDE.md) | Project context for Claude Code |
| [01_TECHNISCHE_ARCHITEKTUR.md](01_TECHNISCHE_ARCHITEKTUR.md) | System architecture |
| [02_USER_STORIES.md](02_USER_STORIES.md) | Prioritized backlog |
| [03_CLAUDE_CODE_GUIDE.md](03_CLAUDE_CODE_GUIDE.md) | Development workflow |
| [04_ARCHITECTURE_DECISIONS.md](04_ARCHITECTURE_DECISIONS.md) | ADRs |
| [05_IMPLEMENTATION_PLAN.md](05_IMPLEMENTATION_PLAN.md) | Sprint plan |

## Project Status

| Sprint | Focus | Status |
|--------|-------|--------|
| 1 | Foundation & Auth | Complete |
| 2 | Papers & Ingestion | Complete |
| 3 | AI Scoring Pipeline | Complete |
| 4 | Projects & KanBan | Not Started |
| 5 | Search & Discovery | Not Started |
| 6 | Frontend MVP | Not Started |

## License

Proprietary - All rights reserved
