# Paper Scraper - Claude Code Execution List

> **Purpose**: Sequential task list for Claude Code implementation. Execute one block at a time.
> **Source**: Consolidated from Lovable prototype (FEATURES_AND_USER_STORIES.md) + existing backend

---

## Status Overview

| Phase | Sprints | Focus | Status |
|-------|---------|-------|--------|
| Phase 1 | 1-6 | Foundation, Papers, Scoring, KanBan, Search, Frontend MVP | ✅ Complete |
| Phase 2 | 7-12 | Production Hardening, Ingestion, Scoring Enhancements, Authors, Analytics | ✅ Complete |
| Phase 3 | 13-15 | User Management, Email, UX Polish, Deployment | ✅ Complete |
| **Phase 4** | **16-19** | **Lovable Prototype Features** | 🔲 Pending |
| **Phase 5** | **20-22** | **Advanced Features & Integration** | 🔲 Pending |

---

## Phase 4: Lovable Prototype Features (Sprints 16-19)

### Sprint 16: Researcher Groups & Collaboration

**User Stories**: G1-G4 (Researcher Groups)

```
TASK 16.1: Researcher Groups Model
- Create modules/groups/models.py
  - ResearcherGroup(id, name, description, type, keywords, org_id, created_by)
  - GroupType enum: CUSTOM, MAILING_LIST, SPEAKER_POOL
  - GroupMember(group_id, researcher_id, added_at, added_by)
- Migration: alembic revision --autogenerate -m "add_researcher_groups"
- AC: Groups can be mailing lists or speaker pools

TASK 16.2: Researcher Groups CRUD API
- Create modules/groups/schemas.py, service.py, router.py
- Endpoints:
  - GET /api/v1/groups/ - list groups (filter by type)
  - POST /api/v1/groups/ - create group
  - GET /api/v1/groups/{id} - get group with members
  - PATCH /api/v1/groups/{id} - update group
  - DELETE /api/v1/groups/{id} - delete group
  - POST /api/v1/groups/{id}/members - add members (bulk)
  - DELETE /api/v1/groups/{id}/members/{researcher_id} - remove member
- AC: Group membership tracked per org

TASK 16.3: Smart Group Suggestions (AI)
- Create modules/groups/prompts/suggest_members.jinja2
- POST /api/v1/groups/suggest-members
  - Input: keywords, target_size
  - Output: researcher IDs with relevance scores
- Use researcher embeddings for similarity
- AC: AI suggests members based on research keywords

TASK 16.4: Group Export & Email Integration
- GET /api/v1/groups/{id}/export - export member list (CSV)
- POST /api/v1/groups/{id}/send-email - send to mailing list
- Store email templates per group type
- AC: Groups function as mailing lists
```

### Sprint 17: Technology Transfer Conversations

**User Stories**: T1-T6 (Technology Transfer / Messaging)

```
TASK 17.1: Transfer Conversation Model
- Create modules/transfer/models.py
  - TransferConversation(id, paper_id, researcher_id, org_id, type, stage, created_at)
  - TransferType enum: PATENT, LICENSING, STARTUP, PARTNERSHIP, OTHER
  - TransferStage enum: INITIAL_CONTACT, DISCOVERY, EVALUATION, NEGOTIATION, CLOSED_WON, CLOSED_LOST
  - ConversationMessage(id, conversation_id, sender_id, content, created_at, mentions)
  - ConversationResource(id, conversation_id, name, url, type)
- Migration with proper indexes
- AC: Full conversation history per transfer opportunity

TASK 17.2: Conversation CRUD API
- Create modules/transfer/schemas.py, service.py, router.py
- Endpoints:
  - GET /api/v1/transfer/ - list conversations (filter by stage, type)
  - POST /api/v1/transfer/ - create conversation
  - GET /api/v1/transfer/{id} - get with messages & resources
  - PATCH /api/v1/transfer/{id} - update stage
  - POST /api/v1/transfer/{id}/messages - add message
  - POST /api/v1/transfer/{id}/resources - attach resource
- AC: Stage transitions logged for audit

TASK 17.3: AI-Suggested Next Steps
- Create modules/transfer/prompts/next_steps.jinja2
- GET /api/v1/transfer/{id}/next-steps
  - Analyze conversation history
  - Return 3-5 actionable next steps
- AC: Context-aware suggestions based on stage

TASK 17.4: Message Templates
- Create modules/transfer/models.py: MessageTemplate
- GET /api/v1/transfer/templates - list templates
- POST /api/v1/transfer/templates - create template
- POST /api/v1/transfer/{id}/messages/from-template - use template
- Variables: {researcher_name}, {paper_title}, {org_name}
- AC: Templates speed up outreach
```

### Sprint 18: Research Submission Portal

**User Stories**: SUB1-SUB3 (Research Submission)

```
TASK 18.1: Research Submission Model
- Create modules/submissions/models.py
  - ResearchSubmission(id, researcher_id, org_id, title, abstract, status, submitted_at)
  - SubmissionStatus enum: DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED
  - SubmissionAttachment(id, submission_id, file_path, file_type)
- Researchers can submit their own work for TTO review
- AC: Separate from scraped papers pipeline

TASK 18.2: Submission CRUD API
- Create modules/submissions/schemas.py, service.py, router.py
- Endpoints:
  - GET /api/v1/submissions/my - researcher's own submissions
  - POST /api/v1/submissions/ - create submission
  - GET /api/v1/submissions/{id} - get submission
  - PATCH /api/v1/submissions/{id} - update (draft only)
  - POST /api/v1/submissions/{id}/submit - submit for review
  - POST /api/v1/submissions/{id}/attachments - upload files
- TTO endpoints:
  - GET /api/v1/submissions/ - all submissions (TTO role)
  - PATCH /api/v1/submissions/{id}/review - approve/reject
- AC: Role-based access (researcher vs TTO)

TASK 18.3: Submission Scoring
- Reuse scoring orchestrator for submissions
- POST /api/v1/submissions/{id}/analyze
- Generate 6-dimension radar chart
- Store scores like regular papers
- AC: Same AI analysis as scraped papers

TASK 18.4: Submission-to-Paper Conversion
- POST /api/v1/submissions/{id}/convert-to-paper
- Creates Paper record from approved submission
- Links submission to resulting paper
- AC: Approved submissions enter main pipeline
```

### Sprint 19: Gamification & Knowledge Management

**User Stories**: GA1-GA3 (Gamification), KM1-KM2 (Knowledge Management)

```
TASK 19.1: Badge & Achievement System
- Create modules/gamification/models.py
  - Badge(id, name, description, icon, criteria_type, criteria_value)
  - UserBadge(user_id, badge_id, earned_at)
  - BadgeCriteria enum: PAPERS_REVIEWED, PAPERS_CONTACTED, TRANSFERS_COMPLETED, STREAK_DAYS
- Seed badges: First Review, Power Reviewer (50), Transfer Champion, 7-Day Streak
- AC: Badges awarded automatically on criteria match

TASK 19.2: Achievement Tracking API
- Create modules/gamification/service.py, router.py
- Background job: check_achievements() runs on relevant events
- Endpoints:
  - GET /api/v1/users/me/badges - user's earned badges
  - GET /api/v1/badges - all available badges
  - GET /api/v1/users/me/stats - review count, streak, etc.
- AC: Real-time badge awards with notification

TASK 19.3: Knowledge Sources Model
- Create modules/knowledge/models.py
  - KnowledgeSource(id, user_id, org_id, name, type, content, embedding)
  - SourceType enum: PERSONAL, ORGANIZATION
  - SourceContentType enum: TEXT, URL, FILE
- User-level and org-level knowledge
- AC: Knowledge enhances AI recommendations

TASK 19.4: Knowledge Management API
- Create modules/knowledge/schemas.py, service.py, router.py
- Endpoints:
  - GET /api/v1/knowledge/personal - user's sources
  - POST /api/v1/knowledge/personal - add personal source
  - DELETE /api/v1/knowledge/personal/{id} - remove source
  - GET /api/v1/knowledge/organization - org sources (admin)
  - POST /api/v1/knowledge/organization - add org source (admin)
- Embed on create for RAG retrieval
- AC: Knowledge used in AI prompts for personalization
```

---

## Phase 5: Advanced Features & Integration (Sprints 20-22)

### Sprint 20: 6-Dimension Innovation Radar Enhancement

**User Stories**: P2, M1-M4 (Enhanced Scoring)

```
TASK 20.1: Expand Scoring Dimensions
- Current: Novelty, Relevance, IP Potential, Marketability, Feasibility
- Add: Team Readiness dimension
- Create modules/scoring/prompts/team_readiness.jinja2
  - Evaluate author track record
  - Assess collaboration network
  - Check institutional support signals
- Update ScoringOrchestrator to include 6th dimension
- AC: Complete 6-dimension radar chart

TASK 20.2: Model Configuration Settings
- Create modules/settings/models.py: ModelConfiguration
  - Fields: provider, model_name, api_key_encrypted, is_default, usage_limit
  - Providers: OPENAI, ANTHROPIC, AZURE, LOCAL
- Endpoints:
  - GET /api/v1/settings/models - list configured models
  - POST /api/v1/settings/models - add model config (admin)
  - PATCH /api/v1/settings/models/{id} - update config
  - DELETE /api/v1/settings/models/{id} - remove config
- AC: Multi-model support per organization

TASK 20.3: Usage Tracking & Cost Management
- Create modules/settings/models.py: ModelUsage
  - Fields: model_id, user_id, tokens_input, tokens_output, cost, timestamp
- Track every AI call
- Endpoints:
  - GET /api/v1/settings/models/usage - usage stats (filterable)
  - GET /api/v1/settings/models/usage/summary - aggregated costs
- AC: Cost visibility per model, user, time period

TASK 20.4: Data Ownership & Hosting Info
- GET /api/v1/settings/models/{id}/hosting-info
  - Return: provider, region, data_retention, compliance_certs
- Store per-model hosting metadata
- AC: GDPR compliance visibility
```

### Sprint 21: Developer & Repository Settings

**User Stories**: D1-D3 (Developer), RS1-RS3 (Repository)

```
TASK 21.1: API Key Management
- Create modules/developer/models.py: APIKey
  - Fields: id, org_id, name, key_hash, permissions, last_used, expires_at
- Endpoints:
  - GET /api/v1/developer/api-keys - list keys (admin)
  - POST /api/v1/developer/api-keys - generate key
  - DELETE /api/v1/developer/api-keys/{id} - revoke key
- Key shown only on creation
- AC: Secure API key lifecycle

TASK 21.2: Webhook Configuration
- Create modules/developer/models.py: Webhook
  - Fields: id, org_id, url, events, secret, is_active
  - Events: paper.created, paper.scored, transfer.stage_changed
- Endpoints:
  - GET /api/v1/developer/webhooks - list webhooks
  - POST /api/v1/developer/webhooks - create webhook
  - POST /api/v1/developer/webhooks/{id}/test - send test payload
  - DELETE /api/v1/developer/webhooks/{id} - remove webhook
- Fire webhooks on events
- AC: External system integration

TASK 21.3: Repository Source Management
- Create modules/repositories/models.py: RepositorySource
  - Fields: id, org_id, type, config, is_active, last_sync, sync_frequency
  - Types: OPENALEX, PUBMED, ARXIV, CROSSREF, CUSTOM
- Endpoints:
  - GET /api/v1/repositories/ - list sources
  - POST /api/v1/repositories/ - add source
  - PATCH /api/v1/repositories/{id} - update config
  - POST /api/v1/repositories/{id}/sync - trigger manual sync
  - GET /api/v1/repositories/{id}/status - sync status
- AC: Configurable data sources per org

TASK 21.4: Scheduled Sync Jobs
- Create jobs/repository_sync.py
- Cron-based sync per repository source
- Respect rate limits per source
- Log sync results
- AC: Automated paper ingestion
```

### Sprint 22: Compliance & Governance Enhancement

**User Stories**: C1-C3 (Compliance)

```
TASK 22.1: Enhanced Audit Logging
- Expand modules/audit/models.py
- Log all sensitive operations:
  - User auth events
  - Paper status changes
  - Transfer stage changes
  - Settings modifications
  - Data exports
- Endpoints:
  - GET /api/v1/compliance/audit-logs - searchable logs
  - GET /api/v1/compliance/audit-logs/export - export logs
- AC: Complete audit trail for compliance

TASK 22.2: Compliance Dashboard Data
- GET /api/v1/compliance/dashboard
  - Return: data_processing_summary, model_hosting_summary, access_summary
- Aggregate stats for compliance officers
- AC: Quick compliance health check

TASK 22.3: Data Retention Policies
- Create modules/compliance/models.py: RetentionPolicy
  - Fields: entity_type, retention_days, action (ARCHIVE/DELETE)
- Background job: enforce_retention_policies()
- Endpoints:
  - GET /api/v1/compliance/retention - list policies
  - POST /api/v1/compliance/retention - create policy (admin)
- AC: Automated data lifecycle management

TASK 22.4: RBAC Permissions Matrix
- Expand auth module with granular permissions
- Permission types: papers:read, papers:write, settings:admin, compliance:view
- GET /api/v1/auth/permissions - current user's permissions
- GET /api/v1/auth/roles - available roles with permissions
- Middleware: require_permission("papers:write")
- AC: Fine-grained access control
```

---

## Quick Reference: New User Stories (Lovable)

| ID | Story | Sprint | Domain |
|----|-------|--------|--------|
| G1-G4 | Researcher Groups | 16 | Groups |
| T1-T6 | Technology Transfer Conversations | 17 | Transfer |
| SUB1-SUB3 | Research Submission Portal | 18 | Submissions |
| GA1-GA3 | Gamification & Badges | 19 | Gamification |
| KM1-KM2 | Knowledge Management | 19 | Knowledge |
| M1-M4 | Model Settings & Usage | 20 | Settings |
| D1-D3 | Developer API & Webhooks | 21 | Developer |
| RS1-RS3 | Repository Management | 21 | Repositories |
| C1-C3 | Compliance & Governance | 22 | Compliance |

---

## Execution Pattern

For each TASK, Claude Code should:

```bash
1. Read existing related code (check for similar patterns)
2. Create module directory if new: modules/{feature}/
3. Create models.py with SQLAlchemy models
4. Generate migration: alembic revision --autogenerate -m "description"
5. Create schemas.py with Pydantic models
6. Create service.py with business logic
7. Create router.py with FastAPI endpoints
8. Register router in api/v1/router.py
9. Write tests in tests/test_{feature}.py
10. Run tests: pytest tests/ -v
11. Update CLAUDE.md with new endpoints
```

---

## Files to Create Per Sprint

### Sprint 16 (Groups)
```
paper_scraper/modules/groups/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
├── router.py
└── prompts/
    └── suggest_members.jinja2
tests/test_groups.py
```

### Sprint 17 (Transfer)
```
paper_scraper/modules/transfer/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
├── router.py
└── prompts/
    └── next_steps.jinja2
tests/test_transfer.py
```

### Sprint 18 (Submissions)
```
paper_scraper/modules/submissions/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
tests/test_submissions.py
```

### Sprint 19 (Gamification + Knowledge)
```
paper_scraper/modules/gamification/
├── __init__.py
├── models.py
├── service.py
└── router.py
paper_scraper/modules/knowledge/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
tests/test_gamification.py
tests/test_knowledge.py
```

### Sprint 20 (Model Settings)
```
paper_scraper/modules/scoring/prompts/team_readiness.jinja2
paper_scraper/modules/settings/
├── models.py (extend)
├── schemas.py (extend)
└── router.py (extend)
```

### Sprint 21 (Developer + Repositories)
```
paper_scraper/modules/developer/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
paper_scraper/modules/repositories/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
paper_scraper/jobs/repository_sync.py
```

### Sprint 22 (Compliance)
```
paper_scraper/modules/compliance/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
└── router.py
paper_scraper/jobs/retention_enforcement.py
```

---

## Post-Implementation Updates

After each sprint:
- [ ] `05_IMPLEMENTATION_PLAN.md` - Mark sprint complete
- [ ] `CLAUDE.md` - Add new API endpoints
- [ ] `alembic/versions/` - New migrations committed
- [ ] Tests passing with >80% coverage for new code
