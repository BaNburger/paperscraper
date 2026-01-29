# Paper Scraper - Setup Guide

Complete setup instructions for local development.

---

## Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| **Python** | 3.11+ | `python --version` |
| **Poetry** | 1.7+ | `poetry --version` |
| **Docker** | 24+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker compose version` |

### Install Prerequisites (macOS)

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Docker Desktop
brew install --cask docker
```

---

## Quick Start (5 minutes)

```bash
# 1. Clone and enter project
cd /path/to/PaperScraper

# 2. Copy environment file
cp .env.example .env

# 3. Install Python dependencies
poetry install

# 4. Start Docker services
docker compose up -d

# 5. Run database migrations
poetry run alembic upgrade head

# 6. Run tests to verify
poetry run pytest tests/ -v

# 7. Start API server
poetry run uvicorn paper_scraper.api.main:app --reload --port 8000
```

API is now available at: http://localhost:8000/docs

---

## Step-by-Step Setup

### Step 1: Environment Configuration

```bash
cp .env.example .env
```

**What it does:** Creates your local environment file from the template.

**Edit `.env`** and set at minimum:
```bash
# Required for AI scoring (get from https://platform.openai.com)
OPENAI_API_KEY=sk-your-actual-key

# Generate a secure JWT secret
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Set your email for polite API access
OPENALEX_EMAIL=your-email@example.com
CROSSREF_EMAIL=your-email@example.com
```

---

### Step 2: Install Python Dependencies

```bash
poetry install
```

**What it does:**
- Creates a virtual environment in `.venv/`
- Installs all dependencies from `pyproject.toml`
- Installs dev dependencies (pytest, ruff, mypy)

**Verify:**
```bash
poetry env info
# Shows Python version and virtualenv path
```

---

### Step 3: Start Docker Services

```bash
# Start all services in background
docker compose up -d
```

**What it does:** Starts 4 containers:

| Container | Port | Purpose |
|-----------|------|---------|
| `paperscraper_db` | 5432 | PostgreSQL 16 + pgvector |
| `paperscraper_redis` | 6379 | Redis for job queue + cache |
| `paperscraper_minio` | 9000, 9001 | S3-compatible storage |
| `paperscraper_api` | 8000 | FastAPI application |

**Verify services are running:**
```bash
docker compose ps
```

Expected output:
```
NAME                  STATUS
paperscraper_db       running (healthy)
paperscraper_redis    running (healthy)
paperscraper_minio    running (healthy)
paperscraper_api      running
```

---

### Step 4: Run Database Migrations

```bash
poetry run alembic upgrade head
```

**What it does:**
- Connects to PostgreSQL
- Creates all tables (organizations, users, papers, authors, scores, etc.)
- Enables pgvector extension
- Creates HNSW indexes for vector search

**Verify:**
```bash
docker compose exec db psql -U postgres -d paperscraper -c "\dt"
```

Expected output shows tables: `organizations`, `users`, `papers`, `authors`, etc.

---

### Step 5: Run Tests

```bash
poetry run pytest tests/ -v
```

**What it does:**
- Runs all test files in `tests/`
- Uses SQLite in-memory for fast testing
- Mocks external APIs (OpenAI, OpenAlex, etc.)

**Expected:** All tests pass (55+ tests across auth, papers, scoring)

---

### Step 6: Start the API Server

**Option A: Local (recommended for development)**
```bash
poetry run uvicorn paper_scraper.api.main:app --reload --port 8000
```

**Option B: Via Docker (already running)**
```bash
# Already started with docker compose up -d
# Logs: docker compose logs -f api
```

**What `--reload` does:** Auto-restarts on code changes.

---

## Quick Verification

### Test the Auth Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "organization_name": "Test Org",
    "organization_type": "university"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
# Save the access_token from response

# 3. Get current user (replace TOKEN)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

### Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Docker running | `docker compose ps` | All containers "healthy" |
| DB accessible | `docker compose exec db pg_isready` | "accepting connections" |
| API health | `curl http://localhost:8000/health` | `{"status": "healthy"}` |
| Swagger docs | Open http://localhost:8000/docs | Interactive API docs |
| Tests pass | `poetry run pytest -v` | All green |

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Docs** | http://localhost:8000/docs | - |
| **API ReDoc** | http://localhost:8000/redoc | - |
| **MinIO Console** | http://localhost:9001 | `minio` / `minio123` |
| **PostgreSQL** | `localhost:5432` | `postgres` / `postgres` |
| **Redis** | `localhost:6379` | - |

---

## Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f              # All services
docker compose logs -f api          # API only
docker compose logs -f db           # Database only

# Restart a service
docker compose restart api

# Run tests
poetry run pytest tests/ -v
poetry run pytest tests/test_auth.py -v    # Specific file
poetry run pytest -k "test_login" -v       # Pattern match

# Database migrations
poetry run alembic upgrade head            # Apply all
poetry run alembic downgrade -1            # Rollback one
poetry run alembic revision -m "desc"      # Create new

# Code quality
poetry run ruff check .                    # Linting
poetry run mypy paper_scraper              # Type checking

# Start arq worker (for background jobs)
poetry run arq paper_scraper.jobs.worker.WorkerSettings
```

---

## Troubleshooting

### Docker Issues

#### "Cannot connect to the Docker daemon"
```bash
# Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```
**Fix:** Start Docker Desktop application, wait for the whale icon to show "running".

#### "Port already in use"
```bash
# Error: Bind for 0.0.0.0:5432 failed: port is already allocated
```
**Fix:** Stop the conflicting service:
```bash
# Find what's using the port
lsof -i :5432

# Or change the port in docker-compose.yml:
# ports:
#   - "5433:5432"  # Use 5433 instead
```

#### Containers not starting
```bash
# Check logs for the failing container
docker compose logs db
docker compose logs api

# Recreate containers
docker compose down -v  # WARNING: Deletes data volumes
docker compose up -d
```

---

### Database Issues

#### "Connection refused" to database
```bash
# Error: asyncpg.exceptions.ConnectionDoesNotExistError
```
**Fix:** Ensure the database container is healthy:
```bash
docker compose ps
# If db shows "unhealthy":
docker compose restart db
docker compose logs db
```

#### Migration errors
```bash
# Error: alembic.util.exc.CommandError: Target database is not up to date
```
**Fix:**
```bash
# Show current migration state
poetry run alembic current

# Apply pending migrations
poetry run alembic upgrade head

# If corrupted, reset (WARNING: deletes all data):
docker compose down -v
docker compose up -d
poetry run alembic upgrade head
```

#### "Relation does not exist"
```bash
# Error: relation "users" does not exist
```
**Fix:** Migrations haven't run:
```bash
poetry run alembic upgrade head
```

---

### Poetry Issues

#### "Command not found: poetry"
**Fix:** Add Poetry to PATH:
```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$HOME/.local/bin:$PATH"

# Then reload:
source ~/.zshrc
```

#### Dependency conflicts
```bash
# Error: Package X requires Y, but you have Z
```
**Fix:**
```bash
poetry lock --no-update
poetry install
```

#### Wrong Python version
```bash
# Error: The currently activated Python version 3.9 is not supported
```
**Fix:**
```bash
poetry env use python3.11
poetry install
```

---

### Test Issues

#### Tests fail with import errors
```bash
# Error: ModuleNotFoundError: No module named 'paper_scraper'
```
**Fix:** Install in editable mode:
```bash
poetry install
```

#### Tests fail with database errors
The tests use SQLite in-memory, not PostgreSQL. If you see Postgres errors:
```bash
# Ensure you're not accidentally connecting to real DB
# Check tests/conftest.py uses sqlite:///...
```

---

### API Issues

#### "Internal Server Error" on endpoints
```bash
# Check API logs
docker compose logs -f api

# Or if running locally:
# The terminal shows the traceback
```

#### "Unauthorized" on protected endpoints
```bash
# Error: {"detail": "Not authenticated"}
```
**Fix:** Include the Bearer token:
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://localhost:8000/api/v1/auth/me
```

#### CORS errors in browser
**Fix:** Add your frontend URL to `.env`:
```bash
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

---

### LLM/Scoring Issues

#### "OpenAI API key not set"
```bash
# Error: openai.AuthenticationError
```
**Fix:** Add your API key to `.env`:
```bash
OPENAI_API_KEY=sk-your-actual-key
```

#### Rate limits
```bash
# Error: openai.RateLimitError
```
**Fix:** The scoring uses caching. Wait and retry, or upgrade your OpenAI plan.

---

## Reset Everything

If you need a fresh start:

```bash
# Stop and remove all containers + volumes
docker compose down -v

# Remove Poetry environment
poetry env remove python

# Reinstall
poetry install
docker compose up -d
poetry run alembic upgrade head
poetry run pytest -v
```

---

## Next Steps

After setup is verified:

1. **Explore the API:** http://localhost:8000/docs
2. **Read the architecture:** [01_TECHNISCHE_ARCHITEKTUR.md](01_TECHNISCHE_ARCHITEKTUR.md)
3. **Check implementation status:** [05_IMPLEMENTATION_PLAN.md](05_IMPLEMENTATION_PLAN.md)
4. **Start Sprint 4:** Projects & KanBan module
