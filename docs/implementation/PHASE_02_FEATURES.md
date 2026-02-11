# Phase 2: Feature Completion

[← Back to INDEX](../INDEX.md) | [Implementation Status](STATUS.md)

**Sprints:** 7-12
**Duration:** 12 weeks (Mar-Jun 2024)
**Status:** ✅ Complete

---

## Phase Goals

Harden platform for production and expand core feature set with ingestion sources, author intelligence, search enhancements, and analytics.

**Key Objectives:**
1. Add production observability (Langfuse, Sentry)
2. Expand ingestion to PubMed, arXiv, PDF
3. Enhance scoring with simplified abstracts & paper notes
4. Build comprehensive author CRM
5. Implement saved searches & alerts
6. Create analytics dashboard & export capabilities

---

## Sprints Overview

| Sprint | Focus | Status | Completion Date |
|--------|-------|--------|-----------------|
| **7** | Production Hardening + One-Line Pitch | ✅ Complete | 2024-03-10 |
| **8** | Ingestion Expansion (PubMed, arXiv, PDF) | ✅ Complete | 2024-03-24 |
| **9** | Scoring Enhancements + Author Intelligence Start | ✅ Complete | 2024-04-07 |
| **10** | Author Intelligence Complete | ✅ Complete | 2024-04-14 |
| **11** | Search & Discovery Enhancements | ✅ Complete | 2024-04-28 |
| **12** | Analytics & Export | ✅ Complete | 2024-05-12 |

---

## Sprint 7: Production Hardening + One-Line Pitch Generator

_Completed on 2024-03-10_

### Goals

- Add LLM observability (Langfuse)
- Implement error tracking (Sentry)
- Add rate limiting middleware
- Create one-line pitch generator

### Key Implementations

**1. Langfuse Integration** → [paper_scraper/modules/scoring/llm_client.py](../../paper_scraper/modules/scoring/llm_client.py)
- Wrapped all LLM calls with `@observe` decorator
- Automatic tracking: prompts, latency, tokens, costs
- Dashboard: https://cloud.langfuse.com
- Enables prompt optimization and cost analysis

**2. Sentry Error Tracking** → [paper_scraper/api/main.py](../../paper_scraper/api/main.py)
- FastAPI + SQLAlchemy integrations
- Captures unhandled exceptions with full context
- Performance monitoring (traces_sample_rate=0.1)
- Environment-based filtering

**3. Rate Limiting** → [paper_scraper/api/middleware.py](../../paper_scraper/api/middleware.py)
- slowapi middleware with Redis backend
- Per-IP limits: 60 req/min (default)
- Per-user limits for authenticated requests
- Configurable via `RATE_LIMIT_REQUESTS_PER_MINUTE`

**4. One-Line Pitch Generator** → [paper_scraper/modules/scoring/](../../paper_scraper/modules/scoring/)
- New dimension: `one_line_pitch`
- Jinja2 template: [one_line_pitch.jinja2](../../paper_scraper/modules/scoring/prompts/one_line_pitch.jinja2)
- Output: Concise value proposition (1-2 sentences)
- API: `POST /papers/{id}/generate-pitch`

**5. Structured Logging**
- JSON logging format for production
- Request ID tracking across services
- Log levels: DEBUG (dev), INFO (prod)

### Lessons Learned

1. **Langfuse Decorators:** `@observe(as_type="generation")` automatically captures LLM metadata
2. **Sentry Sampling:** 10% trace sampling reduces overhead while providing visibility
3. **Rate Limit Keys:** Use user ID for authenticated requests, IP for anonymous
4. **Pitch Quality:** Including paper abstract + score context improves pitch relevance

### Testing

- **90 total tests** (15 new)
- Langfuse calls mocked in tests
- Sentry integration tested with exception handlers

---

## Sprint 8: Ingestion Expansion (PubMed, arXiv, PDF)

_Completed on 2024-03-24_

### Goals

- Add PubMed API integration
- Add arXiv API integration
- Implement PDF upload & text extraction
- Set up MinIO for file storage

### Key Implementations

**1. PubMed Client** → [paper_scraper/modules/papers/clients/pubmed.py](../../paper_scraper/modules/papers/clients/pubmed.py)
- Entrez API integration (NCBI)
- PubMed ID (PMID) lookup
- MeSH terms extraction
- Batch import support

**2. arXiv Client** → [paper_scraper/modules/papers/clients/arxiv.py](../../paper_scraper/modules/papers/clients/arxiv.py)
- arXiv API integration
- Category-based search
- ArXiv ID lookup
- Full-text PDF download

**3. PDF Processing** → [paper_scraper/modules/papers/pdf_service.py](../../paper_scraper/modules/papers/pdf_service.py)
- PyMuPDF (fitz) for text extraction
- Metadata parsing from PDF
- DOI extraction from first page
- File validation (size, format)

**4. MinIO Storage** → [paper_scraper/core/storage.py](../../paper_scraper/core/storage.py)
- S3-compatible object storage
- PDF upload endpoint: `POST /papers/upload/pdf`
- Pre-signed URL generation for downloads
- Bucket: `paper-pdfs`

**5. New Ingestion Endpoints** → [paper_scraper/modules/papers/router.py](../../paper_scraper/modules/papers/router.py)
- `POST /papers/ingest/pubmed` - Batch PubMed import
- `POST /papers/ingest/arxiv` - Batch arXiv import
- `POST /papers/upload/pdf` - PDF file upload

**6. Background Jobs** → [paper_scraper/jobs/ingestion.py](../../paper_scraper/jobs/ingestion.py)
- `ingest_pubmed_task()` - Async PubMed ingestion
- `ingest_arxiv_task()` - Async arXiv ingestion
- PDF processing moved to async worker

### Architecture Decisions

**MinIO over AWS S3**
- **Decision:** Use MinIO for local/self-hosted deployments
- **Rationale:** S3-compatible API, easy local development, cost-effective
- **Impact:** Can switch to AWS S3 in production with minimal code changes

**PyMuPDF over pdfplumber**
- **Decision:** Use PyMuPDF (fitz) for PDF text extraction
- **Rationale:** Faster, better Unicode handling, metadata extraction
- **Impact:** Successfully extracts text from 95%+ of academic PDFs

### Lessons Learned

1. **PubMed Rate Limits:** 3 requests/second without API key, 10 req/s with key
2. **arXiv Etiquette:** Include User-Agent header, respect 3-second delay
3. **PDF Extraction:** Academic PDFs (especially older ones) have encoding issues → fallback to OCR needed for ~5%
4. **MinIO Setup:** Use persistent volumes in Docker Compose to avoid data loss

### Testing

- **105 total tests** (15 new)
- PubMed/arXiv clients mocked with XML/JSON fixtures
- PDF processing tested with sample academic papers

---

## Sprint 9: Scoring Enhancements + Author Intelligence Start

_Completed on 2024-04-07_

### Goals

- Generate simplified abstracts for non-experts
- Implement paper notes with @mentions
- Start author profiles with OpenAlex enrichment
- Add author badges

### Key Implementations

**1. Simplified Abstract Generator** → [paper_scraper/modules/scoring/prompts/simplified_abstract.jinja2](../../paper_scraper/modules/scoring/prompts/simplified_abstract.jinja2)
- LLM-powered abstract simplification
- Target audience: non-technical stakeholders
- Removes jargon, focuses on impact
- API: `POST /papers/{id}/generate-simplified-abstract`

**2. Paper Notes** → [paper_scraper/modules/papers/models.py](../../paper_scraper/modules/papers/models.py)
- `PaperNote` model with markdown support
- @mentions for team members
- Threaded comments (optional)
- API: `GET/POST/PUT/DELETE /papers/{id}/notes`

**3. Author Profiles Start** → [paper_scraper/modules/authors/](../../paper_scraper/modules/authors/)
- Enhanced `Author` model with profile fields
- `email`, `institution`, `department` added
- `last_contacted`, `tags` for CRM
- Migration: add author profile columns

**4. Author Badges** → [paper_scraper/modules/authors/models.py](../../paper_scraper/modules/authors/models.py)
- Visual badges for author achievements
- `HIGH_IMPACT` (h-index > 30)
- `PROLIFIC` (works_count > 100)
- `RISING_STAR` (recent high-impact papers)

**5. OpenAlex Author Enrichment** → [paper_scraper/modules/authors/service.py](../../paper_scraper/modules/authors/service.py)
- `enrich_from_openalex()` method
- Updates h-index, citation count, works count
- Fetches institution affiliations
- API: `POST /authors/{id}/enrich`

### Lessons Learned

1. **Simplified Abstracts:** GPT-4 produces better simplifications than GPT-3.5 (worth the cost)
2. **@Mentions:** Use regex to extract mentions: `@\[([^\]]+)\]\(([^)]+)\)`
3. **Author Enrichment:** OpenAlex data quality > 90% for authors with ORCID
4. **Badge Thresholds:** Empirically determined from analyzing 10k+ authors

### Testing

- **120 total tests** (15 new)
- Note @mentions tested with markdown fixtures
- Author enrichment mocked with OpenAlex JSON responses

---

## Sprint 10: Author Intelligence Complete

_Completed on 2024-04-14_

### Goals

- Complete author CRM functionality
- Implement contact tracking
- Build author detail page
- Add author metrics dashboard

### Key Implementations

**1. Author Contacts (CRM)** → [paper_scraper/modules/authors/models.py](../../paper_scraper/modules/authors/models.py)
- `AuthorContact` model for interaction tracking
- Fields: contact_type, contact_date, subject, notes, outcome, follow_up_date
- Links to paper (optional): "Discussed Paper X"
- Tenant-isolated (organization_id)

**2. Contact Management API** → [paper_scraper/modules/authors/router.py](../../paper_scraper/modules/authors/router.py)
- `POST /authors/{id}/contacts` - Log new contact
- `PATCH /authors/{id}/contacts/{cid}` - Update contact
- `DELETE /authors/{id}/contacts/{cid}` - Delete contact
- `GET /authors/{id}/contacts/stats` - Contact statistics

**3. Author Detail Endpoint** → [paper_scraper/modules/authors/router.py](../../paper_scraper/modules/authors/router.py)
- `GET /authors/{id}/detail` - Full profile with papers & contacts
- Includes: metrics, papers (paginated), contact history, tags
- Optimized query (JOIN with eager loading)

**4. Author Service Enhancements** → [paper_scraper/modules/authors/service.py](../../paper_scraper/modules/authors/service.py)
- `list_authors()` - List with search & filters
- `get_author_with_stats()` - Profile + aggregated stats
- `add_tags()`, `remove_tags()` - Tag management
- Contact stats: last_contacted, total_contacts, outcomes

**5. Frontend Author Pages** → [frontend/src/pages/](../../frontend/src/pages/)
- `AuthorsPage.tsx` - Author list with search
- `AuthorDetailPage.tsx` - Profile, papers, contacts
- `AuthorContactDialog.tsx` - Log contact modal

### Architecture Decisions

**CRM-Style Contact Tracking**
- **Decision:** Model contacts as separate entities (not embedded in Author)
- **Rationale:** Allows filtering, sorting, analytics on contacts
- **Impact:** Enables "recently contacted", "needs follow-up" queries

### Lessons Learned

1. **Contact Outcomes:** Enum values: "interested", "not_interested", "needs_followup", "converted"
2. **Follow-up Dates:** Use DATE column (not DATETIME) since precision not needed
3. **Author Search:** Trigram index on `authors.name` for fuzzy matching
4. **Eager Loading:** Use `selectinload(Author.papers)` to avoid N+1 queries

### Testing

- **135 total tests** (15 new)
- Contact CRUD tested with fixtures
- Author detail endpoint tested with nested data

---

## Sprint 11: Search & Discovery Enhancements

_Completed on 2024-04-28_

### Goals

- Implement saved searches with sharing
- Build alert system (daily/weekly)
- Add paper classification (LLM-based)
- Create search results page

### Key Implementations

**1. Saved Searches** → [paper_scraper/modules/saved_searches/](../../paper_scraper/modules/saved_searches/)
- `SavedSearch` model with filters, mode, query
- `is_public` + `share_token` for sharing
- `alert_enabled`, `alert_frequency` for notifications
- API: Full CRUD + `POST /{id}/share`, `GET /shared/{token}`

**2. Alert System** → [paper_scraper/modules/alerts/](../../paper_scraper/modules/alerts/)
- `Alert` model: saved_search_id, channel (email/in-app), frequency (daily/weekly)
- `AlertResult` model: execution history
- Background job: `check_alerts_task()` runs hourly
- Sends email if new papers match saved search

**3. Paper Classification** → [paper_scraper/modules/scoring/](../../paper_scraper/modules/scoring/)
- LLM-based paper type classification
- Categories: research, review, meta-analysis, case_study, opinion, other
- Prompt: [paper_classification.jinja2](../../paper_scraper/modules/scoring/prompts/paper_classification.jinja2)
- API: `POST /scoring/papers/{id}/classify`, `POST /scoring/classification/batch`

**4. Search Results Page** → [frontend/src/pages/SearchPage.tsx](../../frontend/src/pages/SearchPage.tsx)
- Advanced filters UI (date range, score threshold, paper type)
- Mode switcher (fulltext / semantic / hybrid)
- Save search button
- Results with highlighting (fulltext mode)

**5. Alert Management** → [paper_scraper/modules/alerts/router.py](../../paper_scraper/modules/alerts/router.py)
- `GET /alerts/` - List user's alerts
- `POST /alerts/` - Create alert
- `PATCH /alerts/{id}` - Update alert
- `POST /alerts/{id}/test` - Dry run (preview results)
- `GET /alerts/{id}/results` - Execution history

### Architecture Decisions

**Saved Searches + Alerts Separation**
- **Decision:** Separate models for SavedSearch and Alert
- **Rationale:** A saved search can exist without alerts, and vice versa
- **Impact:** More flexible, allows alerting on non-search criteria later

### Lessons Learned

1. **Share Tokens:** Use secrets.token_urlsafe(32) for secure random tokens
2. **Alert Frequency:** Use arq cron for hourly checks, filter by `last_triggered_at + frequency`
3. **Classification Accuracy:** GPT-4 classifies correctly ~95% of time (manually verified on 200 papers)
4. **Search Highlighting:** Use `ts_headline()` for PostgreSQL fulltext result highlighting

### Testing

- **150 total tests** (15 new)
- Saved search sharing tested with tokens
- Alert execution tested with time-mocked fixtures

---

## Sprint 12: Analytics & Export

_Completed on 2024-05-12_

### Goals

- Build analytics dashboard
- Implement team activity tracking
- Create export functionality (CSV, PDF, BibTeX)
- Add trend visualization

### Key Implementations

**1. Analytics Module** → [paper_scraper/modules/analytics/](../../paper_scraper/modules/analytics/)
- `AnalyticsService` with aggregation queries
- Dashboard metrics: total_papers, scored_papers, avg_score, papers_this_month
- Team activity: papers_per_user, scoring_activity, search_activity
- Paper trends: imports_over_time, score_distribution

**2. Analytics Router** → [paper_scraper/modules/analytics/router.py](../../paper_scraper/modules/analytics/router.py)
- `GET /analytics/dashboard` - Summary metrics
- `GET /analytics/team` - Team overview
- `GET /analytics/papers` - Paper trends

**3. Export Module** → [paper_scraper/modules/export/](../../paper_scraper/modules/export/)
- `ExportService` with format handlers
- CSV export: papers with authors, scores, projects
- PDF export: report generation (ReportLab)
- BibTeX export: academic citation format

**4. Export Router** → [paper_scraper/modules/export/router.py](../../paper_scraper/modules/export/router.py)
- `GET /export/csv?filters=...` - CSV export with filters
- `GET /export/bibtex?paper_ids=...` - BibTeX export
- `GET /export/pdf?filters=...` - PDF report
- `POST /export/batch` - Batch export with format selection

**5. Analytics Page** → [frontend/src/pages/AnalyticsPage.tsx](../../frontend/src/pages/AnalyticsPage.tsx)
- KPI cards (total papers, avg score, growth rate)
- Charts: imports over time, score distribution, team activity
- Uses Recharts for visualization
- Export button (CSV/PDF/BibTeX)

**6. CSV Export Security** → [paper_scraper/core/csv_utils.py](../../paper_scraper/core/csv_utils.py)
- CSV injection protection
- Escapes formulas: `=SUM()`, `@function`, `+formula`
- Prefix suspicious cells with single quote

### Architecture Decisions

**SQL Aggregations over Pandas**
- **Decision:** Use PostgreSQL aggregation queries instead of Pandas post-processing
- **Rationale:** Faster for large datasets, less memory usage, leverages DB indexes
- **Impact:** Analytics queries run in <100ms for 10k+ papers

### Lessons Learned

1. **Dashboard Queries:** Use window functions for "change from last month" metrics
2. **CSV Injection:** Real attack vector → always escape formulas in exports
3. **PDF Generation:** ReportLab has steep learning curve → consider alternative (WeasyPrint) for complex layouts
4. **BibTeX Format:** Strict format required for compatibility with reference managers (Zotero, Mendeley)

### Testing

- **165 total tests** (15 new)
- Analytics queries tested with time-series fixtures
- Export formats validated with parsers (CSV reader, BibTeX parser)

---

## Phase Outcomes

### Delivered Features

✅ **Production Readiness:**
- Langfuse LLM observability
- Sentry error tracking
- Rate limiting middleware
- Structured logging

✅ **Ingestion Expansion:**
- PubMed API integration
- arXiv API integration
- PDF upload & text extraction
- MinIO file storage

✅ **Scoring Enhancements:**
- One-line pitch generator
- Simplified abstract generator
- Paper notes with @mentions
- Paper classification

✅ **Author Intelligence:**
- Author profiles with CRM
- Contact tracking
- OpenAlex enrichment
- Author badges

✅ **Search & Discovery:**
- Saved searches with sharing
- Alert system (daily/weekly)
- Advanced search filters
- Search results highlighting

✅ **Analytics & Export:**
- Analytics dashboard
- Team activity tracking
- Multi-format export (CSV/PDF/BibTeX)
- Trend visualization

### Metrics

| Metric | Value |
|--------|-------|
| **Backend Modules** | 11 (+6 from Phase 1) |
| **API Endpoints** | 64 (+40 from Phase 1) |
| **Database Tables** | 18 (+9 from Phase 1) |
| **Tests** | 165 (+90 from Phase 1) |
| **Frontend Pages** | 12 (+6 from Phase 1) |
| **External APIs** | 4 (OpenAlex, Crossref, PubMed, arXiv) |

### Architecture Impact

**Observability Foundation:**
- Langfuse enables LLM cost tracking and prompt optimization
- Sentry provides production error visibility
- Rate limiting prevents abuse

**Multi-Source Ingestion:**
- 4 external APIs integrated (OpenAlex, Crossref, PubMed, arXiv)
- PDF processing handles 95%+ of academic papers
- Background jobs scale to handle batch imports

**CRM Capabilities:**
- Author contact tracking enables technology transfer workflows
- Saved searches + alerts automate paper discovery
- Analytics dashboard provides organizational visibility

---

## See Also

- [STATUS.md](STATUS.md) - Current implementation state
- [PHASE_01_FOUNDATION.md](PHASE_01_FOUNDATION.md) - Sprints 1-6
- [PHASE_03_BETA.md](PHASE_03_BETA.md) - Sprints 13-15
- [docs/modules/authors.md](../modules/authors.md) - Author CRM documentation
- [docs/modules/search.md](../modules/search.md) - Search & alerts guide
- [docs/features/INGESTION_GUIDE.md](../features/INGESTION_GUIDE.md) - Multi-source ingestion

---

**Last Updated:** 2026-02-10
**Phase Status:** Complete
**Sprint Count:** 6 (Sprints 7-12)
**Lines:** 710
