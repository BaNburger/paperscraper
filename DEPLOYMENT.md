# Paper Scraper - Deployment Guide

This guide covers deployment procedures for Paper Scraper to staging and production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Local Development](#local-development)
- [CI/CD Pipeline](#cicd-pipeline)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Database Migrations](#database-migrations)
- [Monitoring & Logging](#monitoring--logging)
- [Rollback Procedures](#rollback-procedures)
- [Security Checklist](#security-checklist)

---

## Prerequisites

### Required Tools
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 with pgvector extension
- Redis 7+

### Required Accounts/Services
- GitHub (repository access)
- Container registry (ghcr.io or Docker Hub)
- Sentry (error tracking)
- Langfuse (LLM observability)
- Resend (email service)
- OpenAI API key (or compatible provider)

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file based on the template below. **Never commit secrets to git.**

```bash
# =============================================================================
# Core Settings
# =============================================================================
ENVIRONMENT=production  # development, staging, production
DEBUG=false
SECRET_KEY=<generate-a-secure-256-bit-key>
APP_NAME="Paper Scraper"

# =============================================================================
# Database
# =============================================================================
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/paper_scraper
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# =============================================================================
# Redis
# =============================================================================
REDIS_URL=redis://host:6379/0

# =============================================================================
# Authentication
# =============================================================================
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# =============================================================================
# CORS
# =============================================================================
CORS_ORIGINS=["https://app.paperscraper.com"]

# =============================================================================
# AI/LLM
# =============================================================================
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# =============================================================================
# Object Storage (MinIO/S3)
# =============================================================================
MINIO_ENDPOINT=storage.paperscraper.com
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<secret-key>
MINIO_BUCKET=paper-scraper
MINIO_SECURE=true

# =============================================================================
# Email (Resend)
# =============================================================================
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@paperscraper.com
FRONTEND_URL=https://app.paperscraper.com

# =============================================================================
# Observability
# =============================================================================
SENTRY_DSN=https://...@sentry.io/...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

# =============================================================================
# Rate Limiting
# =============================================================================
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### Generating a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Local Development

### Quick Start

```bash
# Start all services
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn paper_scraper.api.main:app --reload

# Start the frontend (in another terminal)
cd frontend && npm run dev

# Start the background worker (in another terminal)
arq paper_scraper.jobs.worker.WorkerSettings
```

### Service URLs

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| MinIO Console | http://localhost:9001 |
| Redis | localhost:6379 |
| PostgreSQL | localhost:5432 |

---

## CI/CD Pipeline

The CI/CD pipeline is defined in `.github/workflows/`:

### Continuous Integration (`ci.yml`)

Triggered on every push and PR to `main`:

1. **Lint** - Ruff format and style checks
2. **Backend Tests** - pytest with coverage
3. **Frontend Tests** - Vitest unit tests
4. **E2E Tests** - Playwright end-to-end tests
5. **Build** - Docker image build verification

### Continuous Deployment (`deploy.yml`)

Triggered on:
- Push to `main` branch → deploys to **staging**
- Version tags (`v*`) → deploys to **production**
- Manual workflow dispatch

---

## Staging Deployment

### Automatic Deployment

Commits to `main` automatically deploy to staging.

### Manual Deployment

```bash
# Via GitHub Actions
gh workflow run deploy.yml -f environment=staging
```

### Staging Configuration

- Use staging-specific environment variables
- Enable debug logging
- Use separate database (staging_paper_scraper)
- Configure test email addresses only

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing in CI
- [ ] Database migration tested in staging
- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] Backup of production database

### Deployment Process

1. **Create a release tag:**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Monitor the deployment:**
   - Watch GitHub Actions workflow
   - Check Sentry for new errors
   - Monitor application logs

3. **Verify deployment:**
   ```bash
   curl https://api.paperscraper.com/health
   ```

### Manual Deployment (Emergency)

```bash
# Via GitHub Actions
gh workflow run deploy.yml -f environment=production
```

---

## Database Migrations

### Creating a Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file
cat alembic/versions/<migration_id>.py
```

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Check current revision
alembic current

# View migration history
alembic history
```

### Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Best Practices

- Always test migrations in staging first
- Make migrations backward-compatible when possible
- Include both upgrade and downgrade functions
- Keep migrations small and focused

---

## Monitoring & Logging

### Sentry (Error Tracking)

- Dashboard: https://sentry.io/organizations/your-org/
- Alerts configured for:
  - Error rate spikes
  - New error types
  - Performance degradation

### Langfuse (LLM Observability)

- Dashboard: https://cloud.langfuse.com/
- Tracks:
  - LLM call latency
  - Token usage
  - Cost per request
  - Quality metrics

### Application Logs

```bash
# View API logs
docker logs paper-scraper-api -f

# View worker logs
docker logs paper-scraper-worker -f
```

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Basic health check |
| `/` | API info |

---

## Rollback Procedures

### Quick Rollback (Container)

```bash
# List recent images
docker images | grep paper-scraper

# Rollback to previous image
docker service update --image <previous-image> paper-scraper-api
```

### Code Rollback

```bash
# Revert to previous release
git revert HEAD
git push origin main

# Or checkout specific tag
git checkout v1.0.0
```

### Database Rollback

```bash
# Identify current migration
alembic current

# Rollback to previous migration
alembic downgrade -1
```

---

## Security Checklist

### Before Going Live

- [ ] **Secrets Management**
  - [ ] All secrets in environment variables, not code
  - [ ] Secret key is unique and secure (256+ bits)
  - [ ] API keys have appropriate permissions

- [ ] **Authentication**
  - [ ] JWT tokens expire appropriately
  - [ ] Password hashing uses bcrypt
  - [ ] Rate limiting active on auth endpoints
  - [ ] Account lockout after failed attempts

- [ ] **Authorization**
  - [ ] Tenant isolation tested
  - [ ] Role-based access control working
  - [ ] Admin endpoints protected

- [ ] **Data Protection**
  - [ ] HTTPS enforced (HSTS header)
  - [ ] CORS configured correctly
  - [ ] Security headers middleware active
  - [ ] Audit logging enabled

- [ ] **Infrastructure**
  - [ ] Database connections encrypted (SSL)
  - [ ] Redis password protected
  - [ ] Firewall rules configured
  - [ ] DDoS protection active

- [ ] **Compliance**
  - [ ] GDPR data export endpoint working
  - [ ] Account deletion endpoint working
  - [ ] Privacy policy published
  - [ ] Cookie consent implemented

### Security Headers

The application includes these security headers:

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (production only)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check database is running
docker-compose ps postgres

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### Redis Connection Errors

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -u $REDIS_URL ping
```

#### Migration Failures

```bash
# Check for pending migrations
alembic current

# View migration status
alembic history

# Force migration state (use carefully!)
alembic stamp <revision_id>
```

### Getting Help

- Create an issue: https://github.com/your-org/paper-scraper/issues
- Check Sentry for error details
- Review application logs

---

## Docker Images

### Building Images

```bash
# Backend
docker build -t paper-scraper-backend .

# Frontend
docker build -t paper-scraper-frontend ./frontend
```

### Image Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest from main branch |
| `v1.0.0` | Specific release version |
| `sha-abc123` | Specific commit |

---

## Scaling

### Horizontal Scaling

```bash
# Scale API replicas
docker-compose up -d --scale api=3

# Scale workers
docker-compose up -d --scale worker=5
```

### Database Scaling

- Use read replicas for read-heavy workloads
- Configure connection pooling (PgBouncer)
- Monitor query performance

### Caching

- Redis caches frequent queries
- Frontend uses React Query for client-side caching
- CDN for static assets
