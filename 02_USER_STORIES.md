# Paper Scraper - Priorisierte User Stories

## Übersicht

Diese User Stories sind basierend auf den existierenden Feature Requests, dem Business Plan und den Scoring-Dimensionen strukturiert. Die Priorisierung folgt dem RICE-Framework (Reach, Impact, Confidence, Effort) mit Anpassungen für die initiale MVP-Phase.

---

## 1. Epic-Struktur

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 0: Foundation                           │
│         Technische Basis, Auth, Datenbank-Setup                 │
│                    [Sprint 1-2]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 1: Paper Ingestion                      │
│         Paper-Import, PDF-Parsing, Metadaten                    │
│                    [Sprint 2-3]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 2: AI Scoring Core                      │
│      5-Dimensionales Scoring, One-Line-Pitch, Summaries         │
│                    [Sprint 3-5]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 3: KanBan Pipeline                      │
│         Projekte, Stages, Drag&Drop, Rejection Tracking         │
│                    [Sprint 4-6]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 4: Search & Discovery                   │
│         Semantic Search, Filter, Alerts                         │
│                    [Sprint 5-7]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 5: Author Intelligence                  │
│         Autorenprofile, Kontakt-Tracking, Outreach              │
│                    [Sprint 7-9]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPIC 6: Analytics & Reporting                │
│         Dashboard, Trends, Export                               │
│                    [Sprint 9-11]                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Detaillierte User Stories

### EPIC 0: Foundation (Must-Have)

#### US-0.1: Projekt-Setup
**Als** Entwickler
**möchte ich** ein vollständig konfiguriertes Entwicklungsumfeld
**damit** ich sofort mit der Implementierung beginnen kann.

**Akzeptanzkriterien:**
- [ ] Git Repository mit .gitignore, README, LICENSE
- [ ] Docker Compose für lokale Entwicklung (PostgreSQL, Redis, MinIO)
- [ ] FastAPI Grundgerüst mit Pydantic Settings
- [ ] Alembic für Datenbankmigrationen konfiguriert
- [ ] pytest Setup mit async Support
- [ ] Pre-commit Hooks (ruff, mypy)
- [ ] GitHub Actions CI Pipeline

**Story Points:** 5
**Sprint:** 1

---

#### US-0.2: Benutzerauthentifizierung
**Als** Benutzer
**möchte ich** mich sicher anmelden können
**damit** meine Daten geschützt sind.

**Akzeptanzkriterien:**
- [ ] JWT-basierte Authentifizierung
- [ ] Login/Logout Endpoints
- [ ] Password Hashing (bcrypt)
- [ ] Refresh Token Mechanismus
- [ ] Rate Limiting auf Auth-Endpoints
- [ ] Optional: Magic Link Login

**Story Points:** 8
**Sprint:** 1

---

#### US-0.3: Multi-Tenancy Grundlagen
**Als** Organisation
**möchte ich** meine Daten isoliert von anderen Organisationen haben
**damit** Vertraulichkeit gewährleistet ist.

**Akzeptanzkriterien:**
- [ ] Organization Model mit Subscription Tier
- [ ] User-Organization Beziehung
- [ ] Tenant-ID in allen relevanten Tabellen
- [ ] Middleware für automatische Tenant-Filterung
- [ ] Row-Level Security Tests

**Story Points:** 5
**Sprint:** 2

---

### EPIC 1: Paper Ingestion

#### US-1.1: Manuelle Paper-Eingabe via DOI
**Als** TTO-Manager
**möchte ich** Papers über ihre DOI hinzufügen können
**damit** ich schnell spezifische Publikationen importieren kann.

**RICE:** 300 (10×10×10)/3 = High Priority

**Akzeptanzkriterien:**
- [ ] DOI-Eingabefeld im Frontend
- [ ] Backend-Endpoint für DOI-Import
- [ ] Automatische Metadaten-Abfrage (Crossref API)
- [ ] Autor-Extraktion und -Normalisierung
- [ ] Duplikat-Erkennung
- [ ] Fehlerbehandlung für ungültige DOIs

**Story Points:** 8
**Sprint:** 2

---

#### US-1.2: PubMed/arXiv Integration
**Als** Forscher
**möchte ich** Papers aus PubMed und arXiv importieren
**damit** ich meine Literaturrecherche vereinfachen kann.

**RICE:** 216 (9×8×9)/3 = High Priority

**Akzeptanzkriterien:**
- [ ] PubMed API Integration (E-Utilities)
- [ ] arXiv API Integration
- [ ] Batch-Import via Suchanfrage
- [ ] Scheduled Import (täglich/wöchentlich)
- [ ] Konfigurierbare Suchfilter
- [ ] Progress-Anzeige bei Batch-Import

**Story Points:** 13
**Sprint:** 2-3

---

#### US-1.3: PDF Upload und Parsing
**Als** Benutzer
**möchte ich** PDFs hochladen können
**damit** auch nicht-indexierte Papers analysiert werden können.

**RICE:** 180 (9×8×10)/4 = Medium Priority

**Akzeptanzkriterien:**
- [ ] PDF Upload Endpoint (max 50MB)
- [ ] PDF-Text-Extraktion (PyMuPDF)
- [ ] Automatische Metadaten-Extraktion (Titel, Autoren)
- [ ] S3-kompatible Speicherung
- [ ] PDF Viewer Integration (optional)

**Story Points:** 8
**Sprint:** 3

---

#### US-1.4: Full-Text Link auf Paper-Details
**Als** Benutzer der ein Paper analysiert
**möchte ich** einen direkten Link zum Volltext in einem neuen Tab haben
**damit** ich den Kontext nicht verliere.

**RICE:** 300 (10×3×10)/1 = Quick Win

**Akzeptanzkriterien:**
- [ ] Link-Button auf Paper-Detail-Seite
- [ ] Öffnet in neuem Tab
- [ ] Fallback wenn kein Volltext verfügbar

**Story Points:** 1
**Sprint:** 2

---

### EPIC 2: AI Scoring Core

#### US-2.1: Novelty Scoring
**Als** TTO-Manager
**möchte ich** eine KI-basierte Neuheitsbewertung jedes Papers sehen
**damit** ich echte Innovationen von inkrementellen Verbesserungen unterscheiden kann.

**RICE:** 135 (10×9×9)/6 = Critical

**Akzeptanzkriterien:**
- [ ] Novelty Score (0-10) pro Paper
- [ ] Textuelle Erklärung der Bewertung
- [ ] Evidenz-Zitate aus dem Paper
- [ ] Vergleich mit ähnlichen Papers (Embeddings)
- [ ] Confidence Score

**Story Points:** 13
**Sprint:** 3

---

#### US-2.2: IP-Potential Scoring
**Als** TTO-Manager
**möchte ich** eine Einschätzung des Patentierbarkeitspotentials
**damit** ich fundierte Entscheidungen über Patentanmeldungen treffen kann.

**RICE:** 145.8 (basierend auf existierendem Feature Request)

**Akzeptanzkriterien:**
- [ ] IP Score (0-10)
- [ ] Prior Art Suche (vereinfacht)
- [ ] Freedom-to-Operate Indikator
- [ ] White Space Identifikation
- [ ] Empfehlung (Patent/License/Spinoff)

**Story Points:** 13
**Sprint:** 4

---

#### US-2.3: Marketability Scoring
**Als** VC-Analyst
**möchte ich** das Marktpotential einer Technologie einschätzen können
**damit** ich Investment-Entscheidungen treffen kann.

**RICE:** 81 (basierend auf Feature Request)

**Akzeptanzkriterien:**
- [ ] Marketability Score (0-10)
- [ ] Geschätzte Marktgröße
- [ ] Ziel-Industrien
- [ ] Aktuelle Marktsignale (News, Trends)
- [ ] Wettbewerber-Hinweise

**Story Points:** 13
**Sprint:** 4

---

#### US-2.4: Feasibility & Commercialization Scoring
**Als** Innovationsmanager
**möchte ich** die Umsetzbarkeit und Kommerzialisierungsreife bewerten
**damit** ich realistische Projektpläne erstellen kann.

**Akzeptanzkriterien:**
- [ ] TRL-Level Einschätzung (1-9)
- [ ] Time-to-Market Schätzung
- [ ] Entwicklungskosten-Indikation
- [ ] Markteintrittsbarrieren
- [ ] Kommerzialisierungspfad-Empfehlung

**Story Points:** 13
**Sprint:** 5

---

#### US-2.5: One-Line-Pitch Generator
**Als** Benutzer der Papers scannt
**möchte ich** unter jedem Paper-Titel einen prägnanten One-Liner sehen
**damit** ich schneller durch große Mengen navigieren kann.

**RICE:** 300 (10×9×10)/3 = Critical

**Akzeptanzkriterien:**
- [ ] Max. 15 Wörter pro Pitch
- [ ] Fokus auf Kernwert/Innovation
- [ ] Auf Paper-Listen und Detailseiten sichtbar
- [ ] Generierung bei Import
- [ ] Manuell editierbar

**Story Points:** 5
**Sprint:** 3

---

#### US-2.6: Vereinfachte Abstract-Zusammenfassung
**Als** Benutzer ohne PhD
**möchte ich** das Abstract in einfacher Sprache lesen können
**damit** ich Papers ohne Fachexpertise verstehen kann.

**RICE:** 216 (9×8×9)/3 = High Priority

**Akzeptanzkriterien:**
- [ ] Toggle zwischen Original/Vereinfacht
- [ ] Lesbarkeit auf Abitur-Niveau
- [ ] Erhalt der Kernaussagen
- [ ] On-demand Generierung
- [ ] Caching der Ergebnisse

**Story Points:** 5
**Sprint:** 3

---

#### US-2.7: Detaillierte Score-Aufschlüsselung
**Als** TTO-Managerin
**möchte ich** für jede KI-Bewertung eine detaillierte Aufschlüsselung sehen
**damit** ich die Ergebnisse nachvollziehen und Dritten erklären kann.

**RICE:** 162 (basierend auf Feature Request)

**Akzeptanzkriterien:**
- [ ] Aufklappbare Dimension-Details
- [ ] Evidenz-Zitate pro Dimension
- [ ] Confidence-Indikator pro Dimension
- [ ] Export als PDF möglich
- [ ] Vergleich mit Benchmark

**Story Points:** 8
**Sprint:** 5

---

### EPIC 3: KanBan Pipeline

#### US-3.1: Projekt-Erstellung
**Als** Team-Lead
**möchte ich** Projekte für verschiedene Scouting-Initiativen erstellen
**damit** ich meine Arbeit organisieren kann.

**Akzeptanzkriterien:**
- [ ] Projekt mit Name, Beschreibung
- [ ] Konfigurierbare Stages (Inbox, Screening, Evaluation, Outreach, Archived)
- [ ] Custom Scoring-Gewichtungen pro Projekt
- [ ] Team-Mitglieder-Zuweisung

**Story Points:** 8
**Sprint:** 4

---

#### US-3.2: Drag & Drop KanBan Board
**Als** TTO-Mitarbeiter
**möchte ich** Papers per Drag & Drop durch die Pipeline bewegen
**damit** ich meinen Workflow effizient gestalten kann.

**RICE:** 112.5 (9×10×10)/8 = Critical

**Akzeptanzkriterien:**
- [ ] Visuelle KanBan-Spalten
- [ ] Drag & Drop zwischen Stages
- [ ] Paper-Karten mit Score, One-Liner, Autoren
- [ ] Filter nach Assignee, Score, Tags
- [ ] Bulk-Aktionen

**Story Points:** 13
**Sprint:** 4-5

---

#### US-3.3: Verpflichtende Rejection-Begründung
**Als** Manager
**möchte ich** dass bei Ablehnungen immer eine Begründung angegeben wird
**damit** wir aus Entscheidungen lernen können.

**RICE:** 400 (10×8×10)/2 = Critical

**Akzeptanzkriterien:**
- [ ] Modal bei Ablehnung/Archivierung
- [ ] Pflichtfeld für Begründung
- [ ] Vordefinierte Kategorien + Freitext
- [ ] Begründung in Paper-Historie sichtbar
- [ ] Analytics über Ablehnungsgründe

**Story Points:** 3
**Sprint:** 4

---

#### US-3.4: Paper-Zuweisung an Teammitglieder
**Als** Team-Lead
**möchte ich** Papers bestimmten Teammitgliedern zuweisen können
**damit** Verantwortlichkeiten klar sind.

**Akzeptanzkriterien:**
- [ ] Assignee-Dropdown auf Paper-Karte
- [ ] Benachrichtigung bei Zuweisung
- [ ] Filter nach "Mir zugewiesen"
- [ ] Workload-Übersicht

**Story Points:** 5
**Sprint:** 5

---

#### US-3.5: Paper-Notizen und Kommentare
**Als** Analyst
**möchte ich** Notizen zu Papers hinzufügen können
**damit** ich meine Gedanken dokumentieren kann.

**Akzeptanzkriterien:**
- [ ] Notiz-Input auf Paper-Detail
- [ ] Chronologische Notiz-Historie
- [ ] @mentions für Teammitglieder
- [ ] Rich Text (Markdown)

**Story Points:** 5
**Sprint:** 5

---

### EPIC 4: Search & Discovery

#### US-4.1: Volltextsuche
**Als** Benutzer
**möchte ich** Papers mit Stichworten durchsuchen können
**damit** ich relevante Publikationen finde.

**Akzeptanzkriterien:**
- [ ] Suchfeld in Header
- [ ] Suche in Titel, Abstract, Autoren
- [ ] Fuzzy Matching für Tippfehler
- [ ] Highlighting der Treffer
- [ ] Schnelle Ergebnisse (<500ms)

**Story Points:** 8
**Sprint:** 5

---

#### US-4.2: Semantische Suche
**Als** Forscher
**möchte ich** in natürlicher Sprache suchen können
**damit** ich konzeptionell ähnliche Papers finde.

**RICE:** 121.5 (basierend auf Feature Request)

**Akzeptanzkriterien:**
- [ ] Natural Language Query Input
- [ ] Embedding-basierte Similaritätssuche
- [ ] Top-K ähnliche Papers
- [ ] Erklärung der Ähnlichkeit
- [ ] Kombinierbar mit Filtern

**Story Points:** 8
**Sprint:** 6

---

#### US-4.3: Erweiterte Filter
**Als** Power-User
**möchte ich** Papers nach verschiedenen Kriterien filtern
**damit** ich gezielt suchen kann.

**Akzeptanzkriterien:**
- [ ] Filter nach: Score-Range, Datum, Quelle, Tags
- [ ] Dimension-spezifische Filter (z.B. "Novelty > 7")
- [ ] Filter speichern als "Saved Search"
- [ ] URL-basierte Filter (teilbar)

**Story Points:** 8
**Sprint:** 6

---

#### US-4.4: Automatische Alerts
**Als** Scout
**möchte ich** benachrichtigt werden wenn neue relevante Papers erscheinen
**damit** ich nichts verpasse.

**Akzeptanzkriterien:**
- [ ] Alert-Konfiguration (Saved Search + Threshold)
- [ ] Email-Benachrichtigung
- [ ] Tägliche/Wöchentliche Digest-Option
- [ ] In-App Notification Center
- [ ] Alert-Pause möglich

**Story Points:** 8
**Sprint:** 7

---

#### US-4.5: Paper-Klassifikation nach Typ
**Als** Analyst
**möchte ich** Papers nach Typ filtern können (Review, Experiment, Methodology, etc.)
**damit** ich irrelevante Publikationstypen ausschließen kann.

**RICE:** 121.5 (9×9×10)/6 = High Priority

**Akzeptanzkriterien:**
- [ ] Automatische Klassifikation bei Import
- [ ] Typen: Original Research, Review, Methodology, Dataset, Tool/Software
- [ ] Filter in Suche
- [ ] Tag auf Paper-Karte sichtbar

**Story Points:** 5
**Sprint:** 6

---

### EPIC 5: Author Intelligence

#### US-5.1: Erstautor-Hervorhebung
**Als** Benutzer der Papers analysiert
**möchte ich** den Erstautor klar hervorgehoben sehen
**damit** ich die relevante Kontaktperson schnell finde.

**RICE:** 200 (10×2×10)/1 = Quick Win

**Akzeptanzkriterien:**
- [ ] Erstautor visuell hervorgehoben (Badge)
- [ ] Letztautor ebenfalls markiert (PI-Indikator)
- [ ] Auf Paper-Karten und Detailseite

**Story Points:** 2
**Sprint:** 4

---

#### US-5.2: Autor-Profile mit Metriken
**Als** Scout
**möchte ich** ein Profil jedes Autors sehen
**damit** ich deren Expertise einschätzen kann.

**RICE:** 160 (9×8×10)/6 = Medium Priority

**Akzeptanzkriterien:**
- [ ] ORCID-Integration
- [ ] H-Index, Zitationszahl
- [ ] Publikationsliste
- [ ] Affiliationen (aktuell + historisch)
- [ ] Relevanz-Score für aktuelles Projekt

**Story Points:** 13
**Sprint:** 7

---

#### US-5.3: Letzter Kontakt-Zeitpunkt
**Als** Team-Mitglied
**möchte ich** sehen wann jemand zuletzt einen Forscher kontaktiert hat
**damit** wir keine doppelten Anfragen senden.

**RICE:** 240 (8×9×10)/3 = High Priority

**Akzeptanzkriterien:**
- [ ] "Last Contact" Datum auf Autor-Profil
- [ ] Manuell setzbar
- [ ] Optional: Integration mit Email-Client
- [ ] Team-weit sichtbar

**Story Points:** 5
**Sprint:** 8

---

#### US-5.4: Clustered Outreach
**Als** Scout
**möchte ich** Kontaktanfragen nach meinen interessanten Papers clustern
**damit** ich effizient kommunizieren kann.

**RICE:** 116 (9×9×10)/7 = Medium Priority

**Akzeptanzkriterien:**
- [ ] Gruppierung von Autoren nach Paper-Cluster
- [ ] Email-Template Generator
- [ ] Bulk-Outreach Workflow
- [ ] Tracking von Responses

**Story Points:** 13
**Sprint:** 8-9

---

### EPIC 6: Analytics & Reporting

#### US-6.1: Dashboard
**Als** Manager
**möchte ich** eine Übersicht über die Aktivitäten meines Teams
**damit** ich den Fortschritt verfolgen kann.

**Akzeptanzkriterien:**
- [ ] Papers pro Stage
- [ ] Durchschnittliche Scores
- [ ] Team-Aktivität (Papers reviewed, moved, etc.)
- [ ] Zeitraum-Filter

**Story Points:** 8
**Sprint:** 9

---

#### US-6.2: Paper-Dashboard (wachsend)
**Als** Analyst
**möchte ich** ein visuelles Dashboard pro Paper sehen
**damit** ich alle Informationen auf einen Blick habe.

**RICE:** 126.25 (10×9×10)/8 = High Priority

**Akzeptanzkriterien:**
- [ ] Radar-Chart mit 5 Dimensionen
- [ ] Key Metrics auf einen Blick
- [ ] Score-Entwicklung über Zeit (bei Re-Scoring)
- [ ] Aktions-Buttons integriert

**Story Points:** 8
**Sprint:** 9

---

#### US-6.3: Trend-Analyse
**Als** Stratege
**möchte ich** Forschungstrends in meinem Bereich erkennen
**damit** ich Schwerpunkte setzen kann.

**Akzeptanzkriterien:**
- [ ] Themen-Clustering über Zeit
- [ ] Aufstrebende Themen identifizieren
- [ ] Export als Report

**Story Points:** 13
**Sprint:** 10

---

#### US-6.4: Export-Funktionen
**Als** Benutzer
**möchte ich** Daten exportieren können
**damit** ich sie in anderen Tools verwenden kann.

**Akzeptanzkriterien:**
- [ ] CSV Export für Paper-Listen
- [ ] PDF Export für einzelne Papers
- [ ] BibTeX Export
- [ ] API für Custom Integrations

**Story Points:** 5
**Sprint:** 10

---

## 3. Priorisierte Backlog-Übersicht

### MVP (Sprints 1-6) - Must Have

| ID | User Story | RICE | Story Points |
|----|------------|------|--------------|
| US-0.1 | Projekt-Setup | - | 5 |
| US-0.2 | Authentifizierung | - | 8 |
| US-0.3 | Multi-Tenancy | - | 5 |
| US-1.1 | DOI Import | 300 | 8 |
| US-1.2 | PubMed/arXiv Integration | 216 | 13 |
| US-1.4 | Full-Text Link | 300 | 1 |
| US-2.1 | Novelty Scoring | 135 | 13 |
| US-2.5 | One-Line-Pitch | 300 | 5 |
| US-2.6 | Vereinfachte Zusammenfassung | 216 | 5 |
| US-3.1 | Projekt-Erstellung | - | 8 |
| US-3.2 | KanBan Board | 112.5 | 13 |
| US-3.3 | Rejection-Begründung | 400 | 3 |
| US-4.1 | Volltextsuche | - | 8 |
| US-5.1 | Erstautor-Hervorhebung | 200 | 2 |
| **Total** | | | **97 SP** |

### Post-MVP (Sprints 7-11) - Should Have

| ID | User Story | RICE | Story Points |
|----|------------|------|--------------|
| US-1.3 | PDF Upload | 180 | 8 |
| US-2.2 | IP-Potential Scoring | 145.8 | 13 |
| US-2.3 | Marketability Scoring | 81 | 13 |
| US-2.4 | Feasibility Scoring | - | 13 |
| US-2.7 | Score-Aufschlüsselung | 162 | 8 |
| US-3.4 | Zuweisung | - | 5 |
| US-3.5 | Notizen | - | 5 |
| US-4.2 | Semantische Suche | 121.5 | 8 |
| US-4.3 | Erweiterte Filter | - | 8 |
| US-4.4 | Alerts | - | 8 |
| US-4.5 | Paper-Klassifikation | 121.5 | 5 |
| US-5.2 | Autor-Profile | 160 | 13 |
| US-5.3 | Letzter Kontakt | 240 | 5 |
| US-6.1 | Dashboard | - | 8 |
| US-6.2 | Paper-Dashboard | 126.25 | 8 |
| US-6.4 | Export | - | 5 |
| **Total** | | | **133 SP** |

### Future (Nach MVP) - Nice to Have

| ID | User Story | RICE | Story Points |
|----|------------|------|--------------|
| US-5.4 | Clustered Outreach | 116 | 13 |
| US-6.3 | Trend-Analyse | - | 13 |
| - | BCG Uptake Matrix | 2025 | 13 |
| - | Patent-Paper Matching | 90 | 13 |
| - | Enterprise SSO | 25.7 | 8 |
| - | Chatbot mit RAG | 72 | 21 |
| - | Researcher-Feedback Loop | 100 | 13 |
| - | SDG/Mission Alignment | 90 | 8 |

---

## 4. Sprint-Plan Übersicht

```
Sprint 1 (Woche 1-2):   Foundation + Setup           [18 SP]
Sprint 2 (Woche 3-4):   Paper Ingestion Basics       [22 SP]
Sprint 3 (Woche 5-6):   AI Scoring MVP               [23 SP]
Sprint 4 (Woche 7-8):   KanBan Core                  [26 SP]
Sprint 5 (Woche 9-10):  Search + Scoring Complete    [24 SP]
Sprint 6 (Woche 11-12): Polish + Bug Fixing          [Buffer]
──────────────────────────────────────────────────────────────
                                        MVP Release (~12 Wochen)
──────────────────────────────────────────────────────────────
Sprint 7-8:             Author Intelligence
Sprint 9-10:            Analytics + Alerts
Sprint 11:              Enterprise Features
```

---

## 5. Definition of Done

Eine User Story gilt als "Done" wenn:

- [ ] Alle Akzeptanzkriterien erfüllt
- [ ] Code reviewed (mind. 1 Reviewer)
- [ ] Unit Tests geschrieben und grün
- [ ] Integration Tests für API Endpoints
- [ ] API-Dokumentation aktualisiert (OpenAPI)
- [ ] Keine kritischen Sentry-Errors
- [ ] Performance akzeptabel (<2s für UI, <5s für Scoring)
- [ ] Feature Flag vorhanden (wenn applicable)
- [ ] Demo-fähig für Stakeholder

---

## 6. Nächste Schritte

Siehe `03_CLAUDE_CODE_GUIDE.md` für die detaillierte Anleitung zur Implementierung mit Claude Code.
