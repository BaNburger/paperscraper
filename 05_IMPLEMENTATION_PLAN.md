# Paper Scraper - Implementierungsplan

## Executive Summary

Dieser Plan definiert den Weg vom aktuellen Stand (existierende Dokumentation) zum lauffähigen MVP. Der Fokus liegt auf pragmatischer Umsetzung mit Claude Code als primärem Entwicklungswerkzeug.

**Ziel:** MVP in 12 Wochen (6 Sprints à 2 Wochen)

---

## 1. Meilensteine & Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PAPER SCRAPER ROADMAP                            │
└─────────────────────────────────────────────────────────────────────────────┘

Woche:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16
        │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
        ├───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┤
        │ S1    │ S2    │ S3    │ S4    │ S5    │ S6    │ S7    │ S8    │
        │Found. │Ingest │Score  │KanBan │Search │Polish │Author │Analyt.│
        │       │       │       │       │       │       │       │       │
        └───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘
              │               │               │               │
              ▼               ▼               ▼               ▼
           M1: API        M2: Core       M3: MVP         M4: Full
           Running        Scoring        Release         Product

M1 (Woche 4):  Backend-API lauffähig, Auth, Paper-Import via DOI
M2 (Woche 8):  Novelty Scoring, KanBan-Board funktional
M3 (Woche 12): MVP Release - vollständiges Scoring, Search, Export
M4 (Woche 16): Author Intelligence, Analytics Dashboard
```

---

## 2. Sprint-Detailplanung

### Sprint 1: Foundation (Woche 1-2)

**Ziel:** Entwicklungsumgebung und Core-Infrastruktur aufsetzen

| Task | Beschreibung | Zeit | Abhängigkeiten |
|------|--------------|------|----------------|
| T1.1 | Repository Setup (Git, CI/CD) | 2h | - |
| T1.2 | Docker Compose (PostgreSQL, Redis, MinIO) | 4h | T1.1 |
| T1.3 | FastAPI Grundgerüst + Pydantic Settings | 4h | T1.1 |
| T1.4 | SQLAlchemy Async Setup + Alembic | 4h | T1.2 |
| T1.5 | Auth-Modul (JWT, User, Organization) | 8h | T1.4 |
| T1.6 | API Security (Rate Limiting, CORS) | 4h | T1.3 |
| T1.7 | Tests Setup (pytest-asyncio, fixtures) | 4h | T1.4 |
| T1.8 | Frontend Scaffolding (Vite, React, Tailwind) | 4h | - |

**Deliverables:**
- [ ] `docker-compose up` startet alle Services
- [ ] `/api/v1/auth/register` und `/auth/login` funktionieren
- [ ] JWT-geschützte Route `/api/v1/auth/me`
- [ ] Frontend zeigt Login-Page

**Claude Code Sessions:**
```
Session 1: "Erstelle das Backend-Projekt nach CLAUDE.md Spezifikation"
Session 2: "Implementiere Auth-Modul mit JWT und Organization"
Session 3: "Setup Frontend mit Vite + React + TailwindCSS + Shadcn"
```

---

### Sprint 2: Paper Ingestion (Woche 3-4)

**Ziel:** Papers können importiert und gespeichert werden

| Task | Beschreibung | Zeit | Abhängigkeiten |
|------|--------------|------|----------------|
| T2.1 | Paper/Author Models + Migration | 4h | S1 |
| T2.2 | Crossref API Integration | 6h | T2.1 |
| T2.3 | DOI Import Endpoint | 4h | T2.2 |
| T2.4 | PubMed API Integration | 8h | T2.1 |
| T2.5 | arXiv API Integration | 6h | T2.1 |
| T2.6 | Celery Setup + Batch Import Task | 6h | T2.4, T2.5 |
| T2.7 | Paper List/Detail Frontend | 8h | T2.3 |
| T2.8 | PDF Upload + S3 Storage | 6h | T2.1 |

**Deliverables:**
- [ ] Paper via DOI importieren
- [ ] Batch-Import aus PubMed/arXiv
- [ ] Paper-Liste im Frontend mit Pagination
- [ ] Paper-Detail-View mit Metadaten

**Claude Code Sessions:**
```
Session 1: "Erstelle Paper-Models und Crossref-Integration"
Session 2: "Implementiere PubMed und arXiv Connectors"
Session 3: "Erstelle Paper-Liste und Detail-View im Frontend"
```

---

### Sprint 3: AI Scoring Core (Woche 5-6)

**Ziel:** Papers können nach Novelty bewertet werden

| Task | Beschreibung | Zeit | Abhängigkeiten |
|------|--------------|------|----------------|
| T3.1 | LLM Client Abstraktion | 4h | - |
| T3.2 | Embedding-Generierung + pgvector | 6h | T3.1 |
| T3.3 | Novelty Scoring Dimension | 8h | T3.2 |
| T3.4 | Scoring Orchestrator | 6h | T3.3 |
| T3.5 | One-Line-Pitch Generator | 4h | T3.1 |
| T3.6 | Simplified Abstract Generator | 4h | T3.1 |
| T3.7 | Score Display im Frontend | 6h | T3.4 |
| T3.8 | Langfuse Integration | 4h | T3.4 |

**Deliverables:**
- [ ] Papers erhalten Novelty Score (0-10)
- [ ] Jedes Paper hat One-Line-Pitch
- [ ] Score mit Erklärung im Frontend sichtbar
- [ ] LLM-Kosten trackbar in Langfuse

**Prompt Templates:**

```jinja2
{# novelty.jinja2 #}
Du bist ein Experte für die Bewertung wissenschaftlicher Neuheit.

Analysiere folgendes Paper:
Titel: {{ paper.title }}
Abstract: {{ paper.abstract }}

Ähnliche existierende Papers:
{% for similar in similar_papers %}
- {{ similar.title }} ({{ similar.publication_date }})
{% endfor %}

Bewerte die technologische Neuheit auf einer Skala von 0-10:
- 0-2: Inkrementelle Verbesserung bekannter Methoden
- 3-4: Neue Kombination existierender Ansätze
- 5-6: Signifikante Erweiterung des State-of-the-Art
- 7-8: Neuartiger Ansatz mit Potenzial für Durchbruch
- 9-10: Fundamentale Innovation, paradigmenwechselnd

Antworte im JSON-Format:
{
  "score": <0-10>,
  "explanation": "<2-3 Sätze Begründung>",
  "evidence": ["<Zitat aus Abstract 1>", "<Zitat 2>"],
  "confidence": <0.0-1.0>
}
```

---

### Sprint 4: KanBan Pipeline (Woche 7-8)

**Ziel:** Papers können durch Pipeline bewegt werden

| Task | Beschreibung | Zeit | Abhängigkeiten |
|------|--------------|------|----------------|
| T4.1 | Project/Status Models + Migration | 4h | S2 |
| T4.2 | Project CRUD Endpoints | 4h | T4.1 |
| T4.3 | KanBan Board Backend | 6h | T4.2 |
| T4.4 | Drag & Drop KanBan Frontend | 12h | T4.3 |
| T4.5 | Rejection Reason Modal | 4h | T4.4 |
| T4.6 | Paper Assignment | 4h | T4.4 |
| T4.7 | Notes & Comments | 6h | T4.4 |

**Deliverables:**
- [ ] Projekte erstellen und konfigurieren
- [ ] Papers per Drag & Drop zwischen Stages bewegen
- [ ] Ablehnungsgrund bei Archivierung erforderlich
- [ ] Notizen zu Papers hinzufügen

**Frontend-Komponenten:**
```typescript
// components/kanban/KanbanBoard.tsx
// components/kanban/KanbanColumn.tsx
// components/kanban/PaperCard.tsx
// components/kanban/RejectionModal.tsx
// components/kanban/NotesPanel.tsx
```

---

### Sprint 5: Search & Remaining Scores (Woche 9-10)

**Ziel:** Vollständiges Scoring und Suche funktional

| Task | Beschreibung | Zeit | Abhängigkeiten |
|------|--------------|------|----------------|
| T5.1 | IP-Potential Scoring | 8h | S3 |
| T5.2 | Marketability Scoring | 8h | S3 |
| T5.3 | Feasibility Scoring | 6h | S3 |
| T5.4 | Commercialization Scoring | 6h | S3 |
| T5.5 | Volltextsuche (pg_trgm) | 4h | - |
| T5.6 | Semantische Suche (Embeddings) | 6h | T3.2 |
| T5.7 | Filter-Panel im Frontend | 6h | T5.5, T5.6 |
| T5.8 | Score Radar Chart | 4h | T5.1-T5.4 |

**Deliverables:**
- [ ] Alle 5 Scoring-Dimensionen funktional
- [ ] Volltextsuche über Titel/Abstract
- [ ] Semantische Suche ("Papers ähnlich zu X")
- [ ] Filter nach Score-Ranges

---

### Sprint 6: Polish & MVP Release (Woche 11-12)

**Ziel:** MVP produktionsreif machen

| Task | Beschreibung | Zeit | Abhängigkeiten |
|------|--------------|------|----------------|
| T6.1 | Bug Fixing (Backlog) | 12h | S1-S5 |
| T6.2 | Performance Optimierung | 8h | - |
| T6.3 | Error Handling & Logging | 6h | - |
| T6.4 | Export (CSV, BibTeX) | 6h | - |
| T6.5 | Email Notifications Setup | 4h | - |
| T6.6 | Deployment Documentation | 4h | - |
| T6.7 | User Documentation | 6h | - |
| T6.8 | Security Audit | 4h | - |

**Deliverables:**
- [ ] Keine kritischen Bugs
- [ ] Response-Zeiten < 2s
- [ ] Export funktioniert
- [ ] Deployment Guide
- [ ] Erste Nutzer können onboarden

---

## 3. MVP Feature Matrix

| Feature | Sprint | Status | Priority |
|---------|--------|--------|----------|
| **Core** | | | |
| User Registration/Login | S1 | 🔵 Planned | P0 |
| Organization Management | S1 | 🔵 Planned | P0 |
| **Paper Ingestion** | | | |
| DOI Import | S2 | 🔵 Planned | P0 |
| PubMed Integration | S2 | 🔵 Planned | P0 |
| arXiv Integration | S2 | 🔵 Planned | P1 |
| PDF Upload | S2 | 🔵 Planned | P1 |
| **AI Scoring** | | | |
| Novelty Score | S3 | 🔵 Planned | P0 |
| One-Line-Pitch | S3 | 🔵 Planned | P0 |
| IP-Potential Score | S5 | 🔵 Planned | P1 |
| Marketability Score | S5 | 🔵 Planned | P1 |
| Feasibility Score | S5 | 🔵 Planned | P1 |
| Commercialization Score | S5 | 🔵 Planned | P2 |
| **Pipeline** | | | |
| Project Creation | S4 | 🔵 Planned | P0 |
| KanBan Board | S4 | 🔵 Planned | P0 |
| Rejection Tracking | S4 | 🔵 Planned | P0 |
| Notes/Comments | S4 | 🔵 Planned | P1 |
| **Search** | | | |
| Fulltext Search | S5 | 🔵 Planned | P0 |
| Semantic Search | S5 | 🔵 Planned | P1 |
| Filters | S5 | 🔵 Planned | P1 |
| **Export** | | | |
| CSV Export | S6 | 🔵 Planned | P1 |
| BibTeX Export | S6 | 🔵 Planned | P2 |

---

## 4. Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| LLM API Kosten explodieren | Mittel | Hoch | Caching, Rate Limits, Budget-Alerts |
| Scoring-Qualität unzureichend | Mittel | Hoch | Iteratives Prompt-Engineering, Langfuse |
| PubMed/arXiv API Changes | Niedrig | Mittel | Abstraktion, Backup-Quellen |
| Performance-Probleme | Mittel | Mittel | Early Load Testing, pgvector Tuning |
| Scope Creep | Hoch | Mittel | Strikte MVP-Definition, Backlog |
| Team-Kapazität | Mittel | Hoch | Fokus auf Core-Features, Claude Code |

---

## 5. Entwicklungs-Metriken

### Velocity-Tracking

| Sprint | Geplante SP | Completed SP | Velocity |
|--------|-------------|--------------|----------|
| S1 | 34 | - | - |
| S2 | 48 | - | - |
| S3 | 42 | - | - |
| S4 | 46 | - | - |
| S5 | 48 | - | - |
| S6 | 50 | - | - |

### Qualitäts-Metriken

| Metrik | Ziel | Messung |
|--------|------|---------|
| Test Coverage | >80% | pytest-cov |
| API Response Time | <500ms (p95) | Prometheus |
| Scoring Accuracy | >85% F1 | Manual Validation |
| Bug Escape Rate | <10% | Post-Release Bugs |

---

## 6. Claude Code Session-Plan

### Pro Sprint: 8-12 Sessions

| Session-Typ | Dauer | Fokus |
|-------------|-------|-------|
| Feature-Implementierung | 60-90min | Neuer Code |
| Bug Fixing | 30-60min | Probleme lösen |
| Refactoring | 45-60min | Code-Qualität |
| Testing | 30-45min | Test-Abdeckung |

### Best Practices

```markdown
## Vor jeder Session

1. CLAUDE.md aktuell halten
2. Relevante Dateien identifizieren
3. Klare Task-Definition

## Während der Session

1. Inkrementelle Änderungen
2. Nach jedem Feature: Tests
3. Code-Review vor Commit

## Nach der Session

1. Änderungen committen
2. CI/CD prüfen
3. Dokumentation updaten
```

---

## 7. Deployment-Plan

### Entwicklung (Tag 1)
```bash
docker-compose up -d
# API: http://localhost:8000
# Frontend: http://localhost:3000
# Flower: http://localhost:5555
```

### Staging (Woche 6)
- Supabase Projekt erstellen
- Vercel/Netlify für Frontend
- Railway/Render für Backend
- Upstash für Redis

### Produktion (Woche 12)
- Separate Supabase Instanz
- CDN für Static Assets
- Monitoring (Sentry, Langfuse)
- Backup-Strategie

---

## 8. Post-MVP Roadmap

### Q1 nach MVP: Author Intelligence
- Autor-Profile mit Metriken
- Kontakt-Tracking
- Outreach-Automation

### Q2 nach MVP: Analytics & Alerts
- Dashboard
- Trend-Analyse
- Automatische Alerts

### Q3 nach MVP: Enterprise Features
- SSO Integration
- API für externe Tools
- Custom Scoring Weights
- White-Label Option

---

## 9. Checkliste: Start der Entwicklung

### Vor Sprint 1

- [ ] Repository erstellt und zugänglich
- [ ] CLAUDE.md finalisiert
- [ ] Docker lokal installiert
- [ ] OpenAI API Key bereit
- [ ] Supabase Account (optional für MVP)
- [ ] Langfuse Account erstellt
- [ ] Entwickler-Workstation eingerichtet

### Definition of Ready (pro Story)

- [ ] Akzeptanzkriterien klar
- [ ] Abhängigkeiten identifiziert
- [ ] Story Points geschätzt
- [ ] Keine offenen Fragen
- [ ] Design/Mockup (wenn UI)

### Definition of Done (pro Story)

- [ ] Code implementiert + reviewed
- [ ] Tests grün (Unit + Integration)
- [ ] Dokumentation aktualisiert
- [ ] In Staging deployed
- [ ] Stakeholder-Demo bestanden

---

## 10. Zusammenfassung

| Aspekt | Detail |
|--------|--------|
| **Timeline** | 12 Wochen bis MVP |
| **Sprints** | 6 Sprints à 2 Wochen |
| **Story Points Total** | ~268 SP |
| **Velocity-Annahme** | ~45 SP/Sprint |
| **Core Features MVP** | Auth, Import, Scoring, KanBan, Search |
| **Tech Stack** | FastAPI, PostgreSQL+pgvector, React, OpenAI |
| **Entwicklungs-Tool** | Claude Code |

---

**Nächster Schritt:** Sprint 1 starten mit Task T1.1 (Repository Setup)

```bash
# Erste Claude Code Session starten
cd ~/projects
mkdir paper_scraper
cd paper_scraper
# Claude Code Session: "Erstelle das Backend-Projekt nach CLAUDE.md"
```
