# Paper Scraper - Claude Code Entwicklungsguide

## Übersicht

Dieser Guide definiert Best Practices für die Entwicklung von Paper Scraper mit Claude Code. Er dient als CLAUDE.md für das Projekt-Repository.

---

## 1. Projekt-Kontext für Claude

### 1.1 CLAUDE.md Template

```markdown
# Paper Scraper - AI-Powered Research Intelligence Platform

## Projekt-Übersicht

Paper Scraper ist eine SaaS-Plattform zur automatisierten Analyse wissenschaftlicher Publikationen für Technology Transfer Offices (TTOs), VCs und Corporate Innovation Teams.

### Kernfunktionen
- Paper-Import (DOI, PubMed, arXiv, PDF)
- 5-dimensionales AI-Scoring (Novelty, IP, Market, Feasibility, Commercialization)
- KanBan-Pipeline für Paper-Management
- Semantische Suche
- Autor-Intelligence

### Tech Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy (async), arq (background jobs)
- **Database:** PostgreSQL 16 + pgvector (HNSW index)
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS, Shadcn/UI
- **AI/ML:** Flexible LLM (GPT-5 mini default), Embeddings (text-embedding-3-small)
- **Data Sources:** OpenAlex, EPO OPS, arXiv, PubMed, Crossref, Semantic Scholar
- **Infrastructure:** Docker, Redis, MinIO (S3-compatible)

## Projekt-Struktur

```
paper_scraper/
├── paper_scraper/          # Backend Python Package
│   ├── core/               # Shared utilities, config, security
│   ├── modules/            # Feature modules (papers, scoring, projects, etc.)
│   ├── jobs/               # arq background tasks (async-native)
│   └── api/                # FastAPI application
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── features/       # Feature-specific components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # Utilities, API client
│   │   └── pages/          # Route pages
│   └── ...
├── tests/                  # Test suite
├── docs/                   # Documentation
└── docker-compose.yml      # Local development
```

## Entwicklungs-Konventionen

### Python Backend
- Async/await für alle I/O-Operationen
- Pydantic v2 für alle Schemas
- Type hints für alle Funktionen
- Docstrings im Google-Style
- Absolute Imports

### TypeScript Frontend
- Functional Components mit Hooks
- TanStack Query für Server State
- Zod für Runtime-Validation
- Barrel Exports (index.ts)

### Testing
- pytest für Backend (pytest-asyncio)
- Vitest für Frontend
- Mindestens 80% Coverage für kritische Pfade

## Wichtige Dateien

- `paper_scraper/core/config.py` - Pydantic Settings
- `paper_scraper/modules/scoring/prompts/` - LLM Prompt Templates
- `paper_scraper/modules/scoring/dimensions/` - Scoring Logic pro Dimension
- `frontend/src/lib/api.ts` - API Client

## Datenmodell-Übersicht

Siehe `01_TECHNISCHE_ARCHITEKTUR.md` für das vollständige Datenbankschema.

Kern-Entities:
- Organization → User (1:n)
- Organization → Project (1:n)
- Project → PaperStatus (1:n)
- Paper → PaperScore (1:n, pro Organization)
- Paper → Author (n:m via paper_authors)

## LLM Integration

### Provider Abstraktion
Alle LLM-Aufrufe laufen über `scoring/llm_client.py`. Provider ist konfigurierbar (OpenAI, Anthropic, Ollama).

### Prompt Management
Prompts sind in `scoring/prompts/` als Jinja2 Templates. Langfuse-Integration für Prompt-Versioning und Monitoring.

### Scoring Pipeline
1. Paper wird an Orchestrator übergeben
2. Für jede Dimension: Load Prompt → Call LLM → Parse Response
3. Ergebnisse aggregieren, Confidence berechnen
4. In Datenbank speichern

## Häufige Aufgaben

### Neue API-Endpoint hinzufügen
1. Schema in `modules/<feature>/schemas.py`
2. Service-Logik in `modules/<feature>/service.py`
3. Route in `modules/<feature>/router.py`
4. Router in `api/v1/router.py` registrieren
5. Tests in `tests/api/test_<feature>.py`

### Neue Scoring-Dimension hinzufügen
1. Prompt Template in `scoring/prompts/<dimension>.jinja2`
2. Dimension-Modul in `scoring/dimensions/<dimension>.py`
3. In Orchestrator registrieren
4. Schema erweitern
5. Migration für DB-Spalten

### Background Job hinzufügen
1. Async Task-Funktion in `jobs/<task_name>.py`
2. In `jobs/worker.py` WorkerSettings.functions registrieren
3. Schedule via `arq.cron()` (wenn periodisch)

## Troubleshooting

### Database Connection Issues
```bash
docker-compose logs db
docker-compose exec api alembic upgrade head
```

### LLM Rate Limiting
Implementiere exponential backoff in `llm_client.py`.

### Slow Scoring
- Prüfe Langfuse für Latenz-Metriken
- Batch-Scoring verwenden für >10 Papers

## Ressourcen

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Langfuse](https://langfuse.com/docs)
```

---

## 2. Task-Prompts für Claude Code

### 2.1 Sprint 1: Foundation

#### Task 1.1: Projekt-Scaffolding

```
Erstelle das Python-Backend-Projekt mit folgender Struktur:

1. Verzeichnisstruktur:
   paper_scraper/
   ├── paper_scraper/
   │   ├── __init__.py
   │   ├── core/
   │   │   ├── __init__.py
   │   │   ├── config.py (Pydantic Settings mit DATABASE_URL, REDIS_URL, OPENAI_API_KEY, etc.)
   │   │   ├── database.py (SQLAlchemy async session factory)
   │   │   ├── security.py (JWT utilities, password hashing)
   │   │   └── exceptions.py (Custom exceptions mit FastAPI handlers)
   │   ├── modules/
   │   │   └── __init__.py
   │   ├── jobs/
   │   │   └── __init__.py
   │   └── api/
   │       ├── __init__.py
   │       ├── main.py (FastAPI app mit CORS, exception handlers)
   │       ├── dependencies.py (get_db, get_current_user)
   │       └── v1/
   │           ├── __init__.py
   │           └── router.py
   ├── tests/
   │   ├── conftest.py (pytest fixtures für async db, test client)
   │   └── __init__.py
   ├── alembic/
   │   └── versions/
   ├── alembic.ini
   ├── pyproject.toml (poetry mit dependencies)
   ├── Dockerfile
   ├── docker-compose.yml
   └── .env.example

2. Dependencies in pyproject.toml:
   - fastapi[all]
   - sqlalchemy[asyncio]
   - asyncpg
   - pydantic-settings
   - python-jose[cryptography]
   - passlib[bcrypt]
   - arq (async-native background jobs)
   - httpx
   - pytest-asyncio
   - alembic

3. docker-compose.yml mit:
   - PostgreSQL 16 + pgvector
   - Redis 7
   - MinIO
   - API Service mit hot reload

Stelle sicher, dass `docker-compose up` funktioniert und die API unter http://localhost:8000/docs erreichbar ist.
```

#### Task 1.2: Auth-Modul

```
Erstelle das Authentication-Modul in paper_scraper/modules/auth/:

1. Models (models.py):
   - Organization: id (UUID), name, type (enum), subscription_tier, settings (JSONB), timestamps
   - User: id, organization_id (FK), email (unique), hashed_password, full_name, role (enum), preferences (JSONB), is_active, timestamps
   - Role Enum: admin, manager, member, viewer

2. Schemas (schemas.py):
   - UserCreate, UserUpdate, UserResponse
   - OrganizationCreate, OrganizationResponse
   - Token, TokenPayload
   - LoginRequest

3. Service (service.py):
   - create_user, get_user_by_email, authenticate_user
   - create_organization, get_organization
   - verify_password, get_password_hash
   - create_access_token, create_refresh_token

4. Router (router.py):
   - POST /auth/register (erstellt User + Organization)
   - POST /auth/login (returns JWT)
   - POST /auth/refresh
   - GET /auth/me
   - PUT /auth/me

5. Alembic Migration für die neuen Tabellen

6. Tests:
   - test_register_creates_user_and_org
   - test_login_returns_token
   - test_protected_route_requires_auth

Implementiere mit async/await und verwende die bestehenden core utilities.
```

### 2.2 Sprint 2-3: Paper Ingestion

#### Task 2.1: Paper-Modul Grundstruktur

```
Erstelle das Papers-Modul in paper_scraper/modules/papers/:

1. Models (models.py):
   - Paper: id, doi, title, abstract, publication_date, source, source_id, source_url,
            pdf_url, pdf_path, full_text, raw_metadata (JSONB), embedding (vector),
            organization_id, timestamps
   - Author: id, orcid, name, normalized_name, email, affiliations (JSONB),
             h_index, citation_count, profile_data (JSONB), last_contact_at
   - PaperAuthor: paper_id, author_id, position, is_corresponding

2. Schemas (schemas.py):
   - PaperCreate (für manuelles Hinzufügen)
   - PaperIngestByDOI, PaperIngestByURL
   - PaperResponse, PaperListResponse (mit Pagination)
   - PaperFilters (für Query-Parameter)
   - AuthorResponse

3. Service (service.py):
   - create_paper, get_paper, list_papers (mit Filtern)
   - ingest_by_doi (ruft Crossref API auf)
   - link_authors (findet oder erstellt Autoren)
   - search_papers (Volltextsuche mit pg_trgm)

4. Router (router.py):
   - GET /papers (Liste mit Pagination, Filter)
   - GET /papers/{id}
   - POST /papers/ingest/doi
   - DELETE /papers/{id}

5. Migration mit pgvector Extension und Indizes

Fokussiere auf saubere Abstraktion - die Ingestion-Logic kommt separat.
```

#### Task 2.2: Crossref Integration

```
Erstelle den Crossref-Connector in paper_scraper/modules/papers/ingestion/sources/crossref.py:

1. CrossrefClient Klasse:
   - __init__(self, email: str) - polite pool mit email
   - async get_work_by_doi(doi: str) -> CrossrefWork
   - async search_works(query: str, filters: dict) -> list[CrossrefWork]

2. Pydantic Models für Crossref Response:
   - CrossrefWork mit allen relevanten Feldern
   - CrossrefAuthor
   - CrossrefAffiliation

3. Mapping-Funktionen:
   - crossref_to_paper(work: CrossrefWork) -> PaperCreate
   - crossref_to_authors(work: CrossrefWork) -> list[AuthorCreate]

4. Error Handling:
   - DOI nicht gefunden
   - Rate Limiting (429)
   - Timeout

5. Tests mit mocked responses (fixture mit echten Crossref-Responses)

Verwende httpx.AsyncClient mit Retry-Logic.
```

#### Task 2.3: PubMed Integration

```
Erstelle den PubMed-Connector in paper_scraper/modules/papers/ingestion/sources/pubmed.py:

1. PubMedClient Klasse:
   - __init__(self, api_key: str = None)
   - async search(query: str, max_results: int = 100) -> list[str] (PMIDs)
   - async fetch_details(pmids: list[str]) -> list[PubMedArticle]

2. E-Utilities Endpoints:
   - esearch für Suche
   - efetch für Details (XML parsing)

3. Pydantic Models:
   - PubMedArticle
   - PubMedAuthor

4. Mapping zu Paper-Entities

5. Batch-Ingestion arq Task (async):
   - ingest_pubmed_search(ctx, query, max_results, project_id)
   - Progress-Tracking

6. Tests

Beachte PubMed API Guidelines (max 3 requests/sec ohne API key, 10/sec mit).
```

### 2.3 Sprint 3-5: AI Scoring

#### Task 3.1: LLM Client Abstraktion

```
Erstelle die LLM-Abstraktion in paper_scraper/modules/scoring/llm_client.py:

1. Abstract Base Class:
   class LLMClient(ABC):
       @abstractmethod
       async def complete(prompt: str, system: str = None, **kwargs) -> str

       @abstractmethod
       async def stream(prompt: str, system: str = None) -> AsyncIterator[str]

       @abstractmethod
       async def embed(text: str) -> list[float]

2. Implementierungen:
   - OpenAIClient (GPT-4-turbo, ada-002)
   - AnthropicClient (Claude 3)
   - OllamaClient (für lokale Entwicklung)

3. Factory-Funktion:
   def get_llm_client(provider: str = None) -> LLMClient

4. Retry-Logic mit exponential backoff

5. Cost-Tracking Hooks (für Langfuse Integration)

6. Config in core/config.py:
   - LLM_PROVIDER: str = "openai"
   - OPENAI_API_KEY: SecretStr
   - ANTHROPIC_API_KEY: SecretStr
   - OLLAMA_BASE_URL: str = "http://localhost:11434"
```

#### Task 3.2: Novelty Scoring Dimension

```
Implementiere Novelty Scoring in paper_scraper/modules/scoring/dimensions/novelty.py:

1. Prompt Template (novelty.jinja2):
   - Input: title, abstract, similar_papers (Top 5 ähnlichste)
   - Output Schema: score (0-10), explanation, evidence[], confidence

2. NoveltyScorer Klasse:
   - async score(paper: Paper, similar_papers: list[Paper]) -> NoveltyResult
   - Ruft LLM mit Prompt auf
   - Parsed strukturierte Response (JSON mode)

3. Similar Papers Lookup:
   - Vector similarity search in pgvector
   - Top 5 ähnlichste Papers abrufen

4. Pydantic Models:
   - NoveltyResult (score, explanation, evidence, confidence)

5. Integration Tests:
   - Mock LLM response
   - Verifiziere Parsing

Der Prompt sollte:
- Nach semantischer Distanz zum Stand der Technik fragen
- Neue Terminologie erkennen
- Interdisziplinäre Aspekte bewerten
- Evidenz aus dem Abstract zitieren
```

#### Task 3.3: Scoring Orchestrator

```
Erstelle den Scoring Orchestrator in paper_scraper/modules/scoring/orchestrator.py:

1. ScoringOrchestrator Klasse:
   - dimensions: dict[str, BaseDimensionScorer]
   - async score_paper(paper_id: UUID, dimensions: list[str] = None, force: bool = False) -> PaperScore
   - async score_batch(paper_ids: list[UUID]) -> list[PaperScore]

2. Workflow:
   a. Paper laden
   b. Prüfen ob Scores existieren (skip wenn nicht force)
   c. Embedding generieren (wenn nicht vorhanden)
   d. Ähnliche Papers finden
   e. Alle Dimensionen parallel scoren
   f. Ergebnisse aggregieren (gewichteter Durchschnitt)
   g. In DB speichern

3. PaperScore Model:
   - Alle 5 Dimensionen
   - overall_score
   - model_version, prompt_version
   - raw_llm_response (für Debugging)

4. arq Tasks (async-native):
   - score_paper_task (einzeln)
   - score_batch_task (für Ingestion)

5. API Endpoints:
   - POST /papers/{id}/score
   - GET /papers/{id}/scores

6. Feature Flag für Scoring (an/aus pro Organization)
```

#### Task 3.4: One-Line-Pitch und Simplified Summary

```
Implementiere Content-Generation in paper_scraper/modules/scoring/content.py:

1. ContentGenerator Klasse:
   - async generate_one_line_pitch(paper: Paper) -> str
   - async generate_simplified_abstract(paper: Paper) -> str
   - async generate_simplified_explanation(text: str) -> str

2. Prompt Templates:
   - one_line_pitch.jinja2:
     "Generiere einen prägnanten One-Liner (max 15 Wörter) der den Kernwert dieser Forschung für kommerzielle Anwendungen beschreibt."

   - simplified_abstract.jinja2:
     "Erkläre dieses Abstract so, dass jemand ohne wissenschaftlichen Hintergrund es verstehen kann. Verwende einfache Sprache und konkrete Beispiele."

3. Caching:
   - Ergebnisse in Paper-Tabelle speichern (one_line_pitch, simplified_abstract)
   - Nur generieren wenn NULL oder force_regenerate

4. API:
   - Felder in PaperResponse inkludieren
   - Optional: separate Endpoints für on-demand Generation

5. Tests mit verschiedenen Paper-Typen
```

### 2.4 Sprint 4-6: KanBan & Search

#### Task 4.1: Projects Modul

```
Erstelle das Projects-Modul in paper_scraper/modules/projects/:

1. Models (models.py):
   - Project: id, organization_id, name, description, filters (JSONB),
              scoring_weights (JSONB), stages (JSONB array), timestamps
   - PaperProjectStatus: id, paper_id, project_id, stage, assigned_to,
                         priority, rejection_reason, notes (JSONB), last_action_at

2. Schemas:
   - ProjectCreate, ProjectUpdate, ProjectResponse
   - PaperStatusCreate, PaperStatusUpdate, PaperStatusResponse
   - KanbanBoardResponse (grouped by stage)

3. Service:
   - CRUD für Projects
   - add_paper_to_project
   - move_paper (stage change mit validation)
   - get_kanban_board (papers grouped by stage)
   - update_assignment

4. Business Rules:
   - Stage-Transitions validieren (z.B. nicht direkt von Inbox zu Archived)
   - Bei Ablehnung: rejection_reason required
   - Activity Log bei jeder Änderung

5. Router:
   - CRUD für /projects
   - GET /projects/{id}/kanban
   - POST /projects/{id}/papers
   - PATCH /projects/{id}/papers/{paper_id}/move
   - PATCH /projects/{id}/papers/{paper_id}/assign
```

#### Task 4.2: Search-Modul

```
Erstelle das Search-Modul in paper_scraper/modules/search/:

1. Volltextsuche (fulltext.py):
   - PostgreSQL pg_trgm für Fuzzy Matching
   - Suche in title, abstract, authors
   - Highlighting der Treffer

2. Semantische Suche (semantic.py):
   - Query → Embedding → pgvector similarity
   - Konfigurierbare Threshold
   - Explain-Funktion (warum ähnlich)

3. Filter-Engine (filters.py):
   - Score-Range Filter (min/max pro Dimension)
   - Datums-Filter
   - Source-Filter
   - Tags-Filter
   - Kombinierbar mit UND/ODER

4. Unified Search API:
   - POST /search
   - Body: { query?, semantic?, filters?, sort?, limit, offset }
   - Response: papers mit search_score

5. Saved Searches:
   - Model: SavedSearch (user_id, name, query, filters)
   - CRUD Endpoints
   - Verwendbar für Alerts
```

---

## 3. Code-Qualitäts-Richtlinien

### 3.1 Python Style

```python
# GOOD: Async, typed, documented
async def get_paper_with_scores(
    db: AsyncSession,
    paper_id: UUID,
    organization_id: UUID,
) -> PaperWithScores | None:
    """
    Retrieve a paper with its associated scores.

    Args:
        db: Database session
        paper_id: The paper's UUID
        organization_id: Current organization for tenant isolation

    Returns:
        Paper with scores if found, None otherwise

    Raises:
        PermissionError: If paper belongs to different organization
    """
    query = (
        select(Paper)
        .options(selectinload(Paper.scores))
        .where(Paper.id == paper_id)
    )
    result = await db.execute(query)
    paper = result.scalar_one_or_none()

    if paper and paper.organization_id != organization_id:
        raise PermissionError("Access denied")

    return paper


# BAD: Blocking, untyped, no docs
def get_paper(db, id):
    return db.query(Paper).filter(Paper.id == id).first()
```

### 3.2 Error Handling

```python
# Custom exceptions
class PaperNotFoundError(Exception):
    def __init__(self, paper_id: UUID):
        self.paper_id = paper_id
        super().__init__(f"Paper {paper_id} not found")


class ScoringError(Exception):
    def __init__(self, paper_id: UUID, dimension: str, reason: str):
        self.paper_id = paper_id
        self.dimension = dimension
        super().__init__(f"Scoring failed for {paper_id}/{dimension}: {reason}")


# In router
@router.get("/papers/{paper_id}")
async def get_paper(
    paper_id: UUID,
    paper_service: PaperService = Depends(get_paper_service),
):
    paper = await paper_service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


# Global exception handler
@app.exception_handler(ScoringError)
async def scoring_error_handler(request: Request, exc: ScoringError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "scoring_failed",
            "paper_id": str(exc.paper_id),
            "dimension": exc.dimension,
            "message": str(exc),
        },
    )
```

### 3.3 Testing Pattern

```python
# conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_llm_client(mocker):
    """Mock LLM client for scoring tests."""
    mock = mocker.patch("paper_scraper.modules.scoring.llm_client.get_llm_client")
    mock.return_value.complete.return_value = json.dumps({
        "score": 8.5,
        "explanation": "Highly novel approach...",
        "evidence": ["Quote 1", "Quote 2"],
        "confidence": 0.9
    })
    return mock


# Test example
@pytest.mark.asyncio
async def test_score_paper_novelty(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_client,
    sample_paper,
):
    # Arrange
    paper = await create_paper(db_session, sample_paper)

    # Act
    response = await client.post(
        f"/api/v1/papers/{paper.id}/score",
        json={"dimensions": ["novelty"]}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["novelty"]["score"] == 8.5
    assert "explanation" in data["novelty"]
```

---

## 4. Entwicklungs-Workflow mit Claude Code

### 4.1 Empfohlener Workflow

```
1. VORBEREITUNG
   - Claude Code Session mit Projekt-Kontext starten
   - Relevante Dateien in Kontext laden
   - Task klar formulieren

2. IMPLEMENTIERUNG
   - Claude generiert Code
   - Review und iterative Verbesserung
   - Tests generieren lassen

3. INTEGRATION
   - Code in Repository übernehmen
   - CI/CD durchlaufen lassen
   - Manuelle Verifikation

4. DOKUMENTATION
   - Docstrings prüfen
   - README aktualisieren
   - ADR wenn nötig (Architecture Decision Record)
```

### 4.2 Effektive Prompts

```markdown
# Für neue Features:
"Implementiere [Feature] nach dem Pattern in [existierende_datei.py].
Erstelle:
1. Pydantic Schemas
2. SQLAlchemy Models
3. Service Layer
4. FastAPI Router
5. Tests

Beachte:
- Async/await überall
- Tenant Isolation
- Error Handling nach bestehenden Konventionen"

# Für Bugfixes:
"Der Endpoint [X] gibt [falsches Verhalten].
Erwartetes Verhalten: [Y]
Reproduktion: [Schritte]

Analysiere den Code in [datei.py] und erstelle einen Fix."

# Für Refactoring:
"Refactore [modul] um [Ziel] zu erreichen.
Constraints:
- Keine Breaking Changes in der API
- Tests müssen weiter grün sein
- Performance darf nicht schlechter werden"
```

### 4.3 Context-Management

```markdown
# Wichtige Dateien für jeden Task:

## Für Backend-Tasks:
- CLAUDE.md (immer)
- paper_scraper/core/config.py
- paper_scraper/core/database.py
- Relevante Module in paper_scraper/modules/
- Zugehörige Tests

## Für Frontend-Tasks:
- CLAUDE.md
- frontend/src/lib/api.ts
- frontend/src/types/
- Relevante Komponenten
- Zugehörige Tests

## Für Scoring-Tasks:
- paper_scraper/modules/scoring/
- Prompt Templates
- Langfuse Dashboard (für Prompt-Performance)
```

---

## 5. Checkliste für jede User Story

```markdown
## Implementation Checklist

### Code
- [ ] Feature implementiert
- [ ] Type Hints vollständig
- [ ] Docstrings geschrieben
- [ ] Error Handling implementiert
- [ ] Logging hinzugefügt

### Tests
- [ ] Unit Tests geschrieben
- [ ] Integration Tests (wenn API)
- [ ] Edge Cases getestet
- [ ] Alle Tests grün

### API (wenn applicable)
- [ ] OpenAPI Schema korrekt
- [ ] Request Validation
- [ ] Response Schema
- [ ] Auth/Permission geprüft

### Database (wenn applicable)
- [ ] Migration erstellt
- [ ] Indizes für Performance
- [ ] Constraints definiert

### Dokumentation
- [ ] Code-Kommentare
- [ ] README Update (wenn nötig)
- [ ] API Docs aktuell

### Review
- [ ] Self-Review durchgeführt
- [ ] Code-Style konsistent
- [ ] Keine Security-Issues
- [ ] Performance akzeptabel
```

---

## 6. Nächste Schritte

Siehe `04_ARCHITECTURE_DECISIONS.md` für die detaillierten Architekturentscheidungen und deren Begründungen.
