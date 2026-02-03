# Paper Scraper Love - Features & User Stories Documentation

## Application Overview

**Paper Scraper Love** is a comprehensive **Research Paper Analysis and Technology Transfer Platform** designed to help academic institutions and research organizations:

- Discover and analyze research papers with automated scoring
- Manage researcher networks and facilitate collaboration
- Track technology transfer opportunities
- Monitor compliance and maintain audit trails
- Generate analytics and reports

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Supabase, React Query

---

## Features & User Stories by Domain

### 1. Paper Management

#### Features
- **Paper Ingestion**: Automated paper collection from multiple repositories (arXiv, PubMed, etc.)
- **AI-Powered Scoring**: Papers scored on novelty (0-100) and relevance (0-100) with combined scores
- **6-Dimension Innovation Radar**: Papers analyzed on Novelty, Market Need, Technical Feasibility, IP Potential, Team Readiness, Commercialization
- **Status Workflow**: Papers move through stages: New → Interesting → Not Relevant → Contacted → Responded
- **Paper Filtering**: Filter by department, faculty, tags, date range, score thresholds
- **Related Content Discovery**: Similar papers, related patents, key concepts, potential applications
- **Paper Attachments & Remarks**: Add files and collaborative comments with @mentions

#### User Stories
| ID | User Story |
|----|------------|
| P1 | As a TTO manager, I want papers automatically scored so I can quickly identify high-potential research |
| P2 | As a researcher, I want to see the innovation radar chart to understand a paper's commercialization potential |
| P3 | As a team member, I want to filter papers by my department so I only see relevant work |
| P4 | As a TTO staff, I want to change paper status so I can track our review progress |
| P5 | As a user, I want to see related patents so I can assess IP landscape |
| P6 | As a team, I want to add remarks/comments on papers so we can collaborate on evaluation |
| P7 | As a manager, I want to see the full status change history for audit purposes |

---

### 2. Kanban Board (Paper Review Workflow)

#### Features
- **5-Column Kanban Board**: New Papers, Interesting, Not Relevant, Contacted, Responded
- **Drag-and-Drop**: Move papers between columns with visual feedback
- **Filtering & Sorting**: Filter by department, faculty, tags; sort by score, date, etc.
- **Progress Summary**: Track review completion statistics
- **Gamification**: Celebration screen with confetti when goals are achieved

#### User Stories
| ID | User Story |
|----|------------|
| K1 | As a reviewer, I want to drag papers between columns so I can efficiently categorize them |
| K2 | As a manager, I want to see progress summary so I know how many papers have been reviewed |
| K3 | As a user, I want celebration animations when I complete review batches for motivation |
| K4 | As a team, I want to filter the kanban view so we can focus on specific research areas |

---

### 3. Researcher Management

#### Features
- **Researcher Profiles**: Detailed profiles with h-index, publication count, research interests, contact info
- **Impact Scoring**: Automatic calculation of researcher impact metrics
- **Researcher Tags**: Custom tagging system for categorization
- **Notes System**: Add internal notes on researchers
- **AI Summary**: AI-generated researcher summaries
- **Collaborator Network**: View potential collaborators with relevance scores
- **Contact History**: Track last contact dates and communication history
- **Messaging History**: View all messages exchanged with researchers

#### User Stories
| ID | User Story |
|----|------------|
| R1 | As a TTO manager, I want to see researcher profiles with impact metrics so I can identify key contributors |
| R2 | As a user, I want to add notes on researchers so I can track relationship context |
| R3 | As a team, I want AI-generated summaries so I can quickly understand a researcher's focus |
| R4 | As a user, I want to see suggested collaborators so I can facilitate research partnerships |
| R5 | As a manager, I want to tag researchers so I can organize them by expertise or status |

---

### 4. Researcher Groups

#### Features
- **Group Management**: Create and manage groups of researchers
- **Mailing Lists**: Groups can function as mailing lists
- **Speaker Pools**: Groups can be designated as speaker pools for events
- **Smart Suggestions**: AI-suggested group creation based on keywords
- **Keyword-Based Grouping**: Organize groups by research keywords
- **Member Selection**: Easy interface for adding/removing members

#### User Stories
| ID | User Story |
|----|------------|
| G1 | As a TTO manager, I want to create researcher groups so I can organize researchers by expertise |
| G2 | As an admin, I want to create mailing lists so I can send targeted communications |
| G3 | As a user, I want AI to suggest group members based on keywords for efficient group creation |
| G4 | As an event organizer, I want speaker pools so I can quickly find presenters |

---

### 5. Technology Transfer / Messaging

#### Features
- **Conversation Management**: Track all technology transfer conversations
- **Stage-Based Workflow**: Visual conversation flow with stages (Initial Contact, Discovery, Evaluation, etc.)
- **Message Threading**: Full message history with sender identification
- **Next Steps**: AI-suggested next actions for each conversation
- **Resource Sharing**: Attach resources and documents to conversations
- **Transfer Types**: Support for patent, licensing, startup, partnership, and other transfer types
- **Message Templates**: Pre-built templates for common communications
- **Integration Options**: Connect with calendar and email systems
- **@Mentions**: Tag colleagues in conversations

#### User Stories
| ID | User Story |
|----|------------|
| T1 | As a TTO staff, I want to track all conversations with researchers so I maintain context |
| T2 | As a user, I want to see suggested next steps so I know what actions to take |
| T3 | As a manager, I want to visualize conversation stages so I can monitor transfer progress |
| T4 | As a team, I want message templates so we can send consistent communications |
| T5 | As a user, I want to attach resources to conversations for easy reference |
| T6 | As a team, I want @mentions so I can involve colleagues in conversations |

---

### 6. Search & Discovery

#### Features
- **Advanced Search**: Full-text search across papers and researchers
- **Keyboard Navigation**: Arrow key navigation through search results
- **Result Preview Panel**: Side panel showing detailed preview without leaving search
- **Tab-Based Filtering**: Filter results by type (papers, researchers, etc.)
- **Peer Comparison**: Chart comparing search results
- **Quick Actions**: Direct actions from search results

#### User Stories
| ID | User Story |
|----|------------|
| S1 | As a user, I want to search across all content types so I can find relevant information quickly |
| S2 | As a power user, I want keyboard navigation so I can work efficiently |
| S3 | As a user, I want to preview results without leaving search for quick evaluation |
| S4 | As a researcher, I want peer comparison charts to benchmark research |

---

### 7. Reports & Analytics

#### Features
- **Key Metrics Dashboard**: KPIs including total papers scraped, researchers identified, analyses completed
- **Papers Analysis Tab**: Detailed paper metrics and trends
- **Innovation Funnel Tab**: Visualize research-to-commercialization pipeline
- **Benchmarks Tab**: Compare university performance against peers
- **Exports Tab**: Export data in various formats (CSV, Excel)
- **Scheduled Reports**: Schedule recurring report generation
- **Filtering**: Filter report data by various criteria

#### User Stories
| ID | User Story |
|----|------------|
| A1 | As a manager, I want KPI dashboards so I can track team performance |
| A2 | As an admin, I want to see the innovation funnel so I understand our commercialization pipeline |
| A3 | As a user, I want to export data so I can create custom analyses |
| A4 | As a manager, I want scheduled reports delivered automatically |
| A5 | As a leader, I want benchmark comparisons to see how we compare to peer institutions |

---

### 8. Alerts & Notifications

#### Features
- **Alert Timeline**: Chronological view of all alerts
- **Alert Types**: Paper alerts, message alerts, collaboration alerts, transfer alerts
- **Importance Flags**: Priority indicators on alerts
- **Score Badges**: Show relevance/novelty scores on paper alerts
- **Click-Through Navigation**: Navigate directly to relevant content from alerts
- **Alert Settings**: Configure alert preferences (categories, thresholds, channels)

#### User Stories
| ID | User Story |
|----|------------|
| N1 | As a user, I want alerts when new high-scoring papers are discovered |
| N2 | As a manager, I want to configure alert thresholds so I only see relevant notifications |
| N3 | As a user, I want to click alerts to navigate directly to the relevant item |
| N4 | As a user, I want to choose notification channels (email, SMS, in-app) |

---

### 9. User Settings

#### Features
- **Profile Management**: Edit user profile information
- **Appearance Settings**: Theme customization (light/dark mode)
- **Role Display**: Show current user role and permissions
- **Security Settings**: Password and authentication management
- **Language Selection**: Support for 12+ languages (EN, DE, FR, ES, IT, PT, NL, PL, SV, FI, DA, NO)
- **Personal Knowledge Areas**: Define areas of expertise for personalized recommendations

#### User Stories
| ID | User Story |
|----|------------|
| U1 | As a user, I want to customize my profile information |
| U2 | As a user, I want to switch between light and dark themes |
| U3 | As a user, I want to set my preferred language |
| U4 | As a user, I want to define my knowledge areas for better recommendations |

---

### 10. Organization Settings

#### Features
- **Organization Theme**: Branding and visual customization
- **User Management**: Manage team members and their roles
- **Role-Based Access**: Admin, Manager, Member, Researcher, TTO Manager, TTO Staff roles
- **Billing Management**: View and manage billing information
- **API Integrations**: Configure third-party integrations

#### User Stories
| ID | User Story |
|----|------------|
| O1 | As an admin, I want to manage users and their roles for access control |
| O2 | As an admin, I want to configure organization branding |
| O3 | As an admin, I want to manage billing information |
| O4 | As an admin, I want to configure API integrations with external systems |

---

### 11. Model Settings (AI/LLM Configuration)

#### Features
- **Model Configuration**: Select and configure AI models for analysis
- **Performance Metrics**: View model performance statistics
- **Usage Statistics**: Track model usage and costs
- **API Key Management**: Manage LLM API keys
- **Data Ownership Settings**: Configure data handling preferences
- **Model Hosting Information**: View hosting details (self-hosted, OpenAI, Anthropic, etc.)

#### User Stories
| ID | User Story |
|----|------------|
| M1 | As an admin, I want to select which AI model to use for paper analysis |
| M2 | As an admin, I want to see model usage statistics to manage costs |
| M3 | As an admin, I want to configure data ownership for compliance |
| M4 | As a user, I want to know where my data is being processed |

---

### 12. Repository Settings

#### Features
- **Repository Sources**: Configure external paper repositories (arXiv, PubMed, etc.)
- **Sync Management**: Trigger and monitor repository synchronization
- **Source Configuration**: Add, edit, and remove data sources
- **Sync Status**: View last sync time and status

#### User Stories
| ID | User Story |
|----|------------|
| RS1 | As an admin, I want to configure which repositories to scrape |
| RS2 | As an admin, I want to manually trigger repository sync |
| RS3 | As a user, I want to see when repositories were last updated |

---

### 13. Developer Settings

#### Features
- **API Key Management**: Generate and manage API keys
- **MCP Server Configuration**: Configure Model Context Protocol servers
- **MCP Playground**: Test MCP server connections
- **Webhook Configuration**: Set up webhooks for integrations
- **Webhook Playground**: Test webhook endpoints

#### User Stories
| ID | User Story |
|----|------------|
| D1 | As a developer, I want API keys so I can integrate with external systems |
| D2 | As an admin, I want to configure MCP servers for AI integrations |
| D3 | As a developer, I want to test webhooks before deployment |

---

### 14. Compliance & Governance

#### Features
- **Compliance Dashboard**: Overview of compliance status
- **Audit Logs**: Complete audit trail of all system actions
- **Model Hosting Transparency**: Clear information about where AI processing occurs
- **Role-Based Access Control**: Granular permissions by role

#### User Stories
| ID | User Story |
|----|------------|
| C1 | As a compliance officer, I want audit logs of all actions for compliance reporting |
| C2 | As an admin, I want to see where data is being processed for GDPR compliance |
| C3 | As a manager, I want role-based access control to limit data exposure |

---

### 15. Keyboard Shortcuts & Accessibility

#### Features
- **Command Menu**: Global command palette (Cmd+K / Ctrl+K)
- **Keyboard Navigation**: Navigate through all major features with keyboard
- **Shortcut Reference**: View all available shortcuts
- **Accessibility Settings**: Configure accessibility preferences
- **WCAG Compliance**: Built on Radix UI for accessibility

#### User Stories
| ID | User Story |
|----|------------|
| KB1 | As a power user, I want a command palette for quick navigation |
| KB2 | As a user, I want keyboard shortcuts for common actions |
| KB3 | As a user with accessibility needs, I want the app to work with screen readers |

---

### 16. Gamification & Engagement

#### Features
- **Badge System**: Achievement badges for milestones
- **Success Animations**: Celebration effects when achieving goals
- **Progress Tracking**: Visual progress indicators
- **Patent Achievement Animations**: Special animations for patent discoveries
- **Trophy Animations**: Recognition for top performance

#### User Stories
| ID | User Story |
|----|------------|
| GA1 | As a user, I want badges to recognize my achievements |
| GA2 | As a user, I want celebration animations to make work more engaging |
| GA3 | As a manager, I want to see team progress for motivation |

---

### 17. Research Submission

#### Features
- **Submit Research Page**: Researchers can submit their own findings
- **My Research Page**: Track personal research submissions
- **Research Analysis**: Get AI analysis on submitted research
- **Commercialization Scoring**: Assess commercial potential of submissions

#### User Stories
| ID | User Story |
|----|------------|
| SUB1 | As a researcher, I want to submit my research for TTO review |
| SUB2 | As a researcher, I want to track the status of my submissions |
| SUB3 | As a researcher, I want AI analysis of my research's commercial potential |

---

### 18. Knowledge Management

#### Features
- **Personal Knowledge Sources**: Add personal knowledge for better AI recommendations
- **Organization Knowledge Upload**: Upload institutional knowledge
- **Source Type Selection**: Categorize knowledge sources
- **Knowledge Source Management**: Edit and remove sources

#### User Stories
| ID | User Story |
|----|------------|
| KM1 | As a user, I want to add my knowledge sources for personalized recommendations |
| KM2 | As an admin, I want to upload organizational knowledge for team-wide use |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Feature Domains** | 18 |
| **Total User Stories** | 64 |
| **Database Tables** | 18 |
| **React Components** | 80+ |
| **Pages/Routes** | 24 |

---

## Data Entities

| Entity | Description |
|--------|-------------|
| Papers | Research papers with scores, status, keywords, and related content |
| Researchers | Faculty/staff profiles with metrics and contact info |
| Researcher Groups | Collections of researchers (mailing lists, speaker pools) |
| Transfer Conversations | Technology transfer communications with stages |
| Alerts | System notifications across multiple categories |
| Users | Platform users with roles and preferences |

---

## User Roles

| Role | Description |
|------|-------------|
| Admin | Full system access, user management, settings |
| Manager | Team oversight, reports, paper management |
| Member | Standard access to papers, researchers, alerts |
| Researcher | Research submission, personal profile |
| TTO Manager | Technology transfer oversight |
| TTO Staff | Technology transfer operations |
