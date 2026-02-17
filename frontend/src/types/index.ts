// Auth types
export interface OrganizationBranding {
  logo_url?: string
  primary_color?: string
  accent_color?: string
  favicon_url?: string
}

export interface Organization {
  id: string
  name: string
  type: string
  subscription_tier: 'free' | 'pro' | 'enterprise'
  settings: Record<string, unknown>
  branding: OrganizationBranding
  created_at: string
  updated_at: string
}

export interface UpdateBrandingRequest {
  primary_color?: string
  accent_color?: string
}

export interface User {
  id: string
  email: string
  full_name: string | null
  role: 'admin' | 'member' | 'viewer'
  organization_id: string
  preferences: Record<string, unknown>
  is_active: boolean
  onboarding_completed: boolean
  onboarding_completed_at: string | null
  created_at: string
  updated_at: string
  organization: Organization
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  organization_name: string
}

// Team Invitation types
export type UserRole = 'admin' | 'manager' | 'member' | 'viewer'
export type InvitationStatus = 'pending' | 'accepted' | 'declined' | 'expired'

export interface InvitationInfo {
  email: string
  organization_name: string
  inviter_name: string | null
  role: UserRole
  expires_at: string
}

export interface AcceptInviteRequest {
  token: string
  password: string
  full_name?: string
}

export interface TeamInvitation {
  id: string
  organization_id: string
  email: string
  role: UserRole
  status: InvitationStatus
  expires_at: string
  created_at: string
}

export interface UserListItem {
  id: string
  email: string
  full_name: string | null
  role: UserRole
  is_active: boolean
  email_verified: boolean
  created_at: string
  updated_at: string
}

export interface OrganizationUsers {
  users: UserListItem[]
  total: number
  pending_invitations: number
}

// Paper types
export type PaperSource =
  | 'doi'
  | 'openalex'
  | 'pubmed'
  | 'arxiv'
  | 'crossref'
  | 'semantic_scholar'
  | 'manual'
  | 'pdf'

export interface Author {
  id: string
  name: string
  orcid?: string
  openalex_id?: string
  affiliations: string[]
  h_index?: number
  citation_count?: number
  works_count?: number
}

export interface PaperAuthor {
  author: Author
  position: number
  is_corresponding: boolean
}

export interface Paper {
  id: string
  organization_id: string
  doi?: string
  source: PaperSource
  source_id?: string
  title: string
  abstract?: string
  publication_date?: string
  journal?: string
  volume?: string
  issue?: string
  pages?: string
  keywords: string[]
  references_count?: number
  citations_count?: number
  one_line_pitch?: string
  simplified_abstract?: string
  has_pdf: boolean
  has_embedding: boolean
  created_at: string
  updated_at: string
}

export interface PaperDetail extends Paper {
  authors: PaperAuthor[]
  mesh_terms: string[]
}

export interface PaperListResponse {
  items: Paper[]
  total: number
  page: number
  page_size: number
  pages: number
}

// Library V2 types
export interface LibraryCollection {
  id: string
  organization_id: string
  name: string
  description?: string | null
  parent_id?: string | null
  created_by?: string | null
  created_at: string
  updated_at: string
  item_count: number
}

export interface LibraryCollectionItem {
  collection_id: string
  paper_id: string
  added: boolean
}

export interface ReaderChunk {
  id: string
  chunk_index: number
  page_number?: number | null
  text: string
  char_start: number
  char_end: number
}

export interface FullTextStatus {
  available: boolean
  source?: string | null
  chunk_count: number
  hydrated_at?: string | null
}

export interface ReaderPayload {
  paper_id: string
  title: string
  status: FullTextStatus
  chunks: ReaderChunk[]
}

export type HighlightSource = 'ai' | 'manual' | 'zotero'

export interface PaperHighlight {
  id: string
  organization_id: string
  paper_id: string
  chunk_id?: string | null
  chunk_ref: string
  quote: string
  insight_summary: string
  confidence: number
  source: HighlightSource
  generation_id: string
  is_active: boolean
  created_by?: string | null
  created_at: string
  updated_at: string
}

export interface PaperTag {
  id: string
  organization_id: string
  paper_id: string
  tag: string
  created_by?: string | null
  created_at: string
}

export interface ZoteroConnectionStatus {
  connected: boolean
  status: 'connected' | 'disconnected' | 'error'
  user_id?: string | null
  base_url?: string | null
  library_type?: string | null
  last_error?: string | null
  last_synced_at?: string | null
}

export interface ZoteroSyncRun {
  id: string
  organization_id: string
  direction: 'outbound' | 'inbound'
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  started_at: string
  completed_at?: string | null
  stats_json: Record<string, unknown>
  error_message?: string | null
}

// Scoring types
export interface JstorReference {
  title: string
  authors?: string
  year?: number
  doi?: string
  journal?: string
  jstor_url?: string
}

export interface PaperScore {
  id: string
  paper_id: string
  organization_id: string
  novelty: number
  novelty_reasoning: string
  ip_potential: number
  ip_potential_reasoning: string
  marketability: number
  marketability_reasoning: string
  feasibility: number
  feasibility_reasoning: string
  commercialization: number
  commercialization_reasoning: string
  team_readiness: number
  team_readiness_reasoning: string
  overall_score: number
  confidence: number
  model_version: string
  created_at: string
  jstor_references?: JstorReference[]
}

export interface ScoreResponse {
  scores: PaperScore
  paper: Paper
}

// Project types
export interface ProjectStage {
  id: string
  name: string
  color: string
  order: number
}

export interface Project {
  id: string
  organization_id: string
  name: string
  description?: string
  stages: ProjectStage[]
  scoring_weights: Record<string, number>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface PaperProjectStatus {
  paper_id: string
  project_id: string
  stage: string
  priority: number
  tags: string[]
  notes?: string
  assigned_to?: string
  rejection_reason?: string
  rejection_notes?: string
  added_at: string
  updated_at: string
}

export interface KanbanPaper extends Paper {
  status: PaperProjectStatus
  latest_score?: PaperScore
}

export interface KanbanColumn {
  stage: ProjectStage
  papers: KanbanPaper[]
  count: number
}

export interface KanbanBoard {
  project: Project
  columns: KanbanColumn[]
}

// Backend API response types (different from frontend types)
export interface BackendKanbanPaper {
  status: PaperProjectStatus
  paper: Paper
  assigned_to?: { id: string; email: string; full_name?: string }
  latest_score?: PaperScore
}

export interface BackendKanbanStage {
  name: string
  label: string
  order: number
  paper_count: number
  papers: BackendKanbanPaper[]
}

export interface BackendKanbanResponse {
  project: Project
  stages: BackendKanbanStage[]
  total_papers: number
}

export interface ProjectStatistics {
  total_papers: number
  by_stage: Record<string, number>
  by_priority: Record<string, number>
  rejection_reasons: Record<string, number>
  average_score?: number
}

// Search types
export type SearchMode = 'fulltext' | 'semantic' | 'hybrid'

export interface SearchRequest {
  query: string
  mode?: SearchMode
  page?: number
  page_size?: number
  sources?: PaperSource[]
  min_score?: number
  max_score?: number
  date_from?: string
  date_to?: string
  has_embedding?: boolean
  has_score?: boolean
  semantic_weight?: number
}

export interface SearchResultHighlight {
  title?: string
  abstract?: string
}

export interface SearchResult {
  paper: Paper
  relevance_score: number
  highlights: SearchResultHighlight
  latest_score?: PaperScore
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  page_size: number
  pages: number
  query: string
  mode: SearchMode
}

// Pagination types
export interface PaginationParams {
  page: number
  page_size: number
}

// Author types (extended for Sprint 10)
export type ContactType = 'email' | 'phone' | 'linkedin' | 'meeting' | 'conference' | 'other'
export type ContactOutcome = 'successful' | 'no_response' | 'declined' | 'follow_up_needed' | 'in_progress'

export interface AuthorContact {
  id: string
  author_id: string
  organization_id: string
  contacted_by_id?: string
  contact_type: ContactType
  contact_date: string
  subject?: string
  notes?: string
  outcome?: ContactOutcome
  follow_up_date?: string
  paper_id?: string
  created_at: string
  updated_at: string
  contacted_by_name?: string
  contacted_by_email?: string
}

export interface AuthorProfile extends Author {
  created_at: string
  updated_at: string
  paper_count: number
  recent_contacts_count: number
  last_contact_date?: string
}

export interface AuthorPaperSummary {
  id: string
  title: string
  doi?: string
  publication_date?: string
  journal?: string
  is_corresponding: boolean
}

export interface AuthorDetail extends AuthorProfile {
  papers: AuthorPaperSummary[]
  contacts: AuthorContact[]
}

export interface AuthorListResponse {
  items: AuthorProfile[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AuthorContactStats {
  author_id: string
  total_contacts: number
  contacts_by_type: Record<string, number>
  contacts_by_outcome: Record<string, number>
  last_contact_date?: string
  next_follow_up?: string
}

export interface CreateContactRequest {
  contact_type: ContactType
  contact_date?: string
  subject?: string
  notes?: string
  outcome?: ContactOutcome
  follow_up_date?: string
  paper_id?: string
}

export interface EnrichmentResult {
  author_id: string
  source: string
  updated_fields: string[]
  success: boolean
  message?: string
}

// Analytics types
export interface TimeSeriesDataPoint {
  date: string
  count: number
}

export interface SourceDistribution {
  source: string
  count: number
  percentage: number
}

export interface ScoreDistributionBucket {
  range_start: number
  range_end: number
  count: number
}

export interface UserActivityStats {
  user_id: string
  email: string
  full_name: string | null
  papers_imported: number
  papers_scored: number
  notes_created: number
  last_active: string | null
}

export interface TeamOverview {
  total_users: number
  active_users_last_7_days: number
  active_users_last_30_days: number
  total_papers: number
  total_scores: number
  total_projects: number
  user_activity: UserActivityStats[]
}

export interface PaperImportTrends {
  daily: TimeSeriesDataPoint[]
  weekly: TimeSeriesDataPoint[]
  monthly: TimeSeriesDataPoint[]
  by_source: SourceDistribution[]
}

export interface ScoringStats {
  total_scored: number
  total_unscored: number
  average_overall_score: number | null
  average_novelty: number | null
  average_ip_potential: number | null
  average_marketability: number | null
  average_feasibility: number | null
  average_commercialization: number | null
  average_team_readiness: number | null
  score_distribution: ScoreDistributionBucket[]
}

export interface TopPaper {
  id: string
  title: string
  doi: string | null
  source: string
  overall_score: number | null
  created_at: string
}

export interface PaperAnalytics {
  import_trends: PaperImportTrends
  scoring_stats: ScoringStats
  top_papers: TopPaper[]
  papers_with_embeddings: number
  papers_without_embeddings: number
  embedding_coverage_percent: number
}

export interface DashboardSummary {
  total_papers: number
  papers_this_week: number
  papers_this_month: number
  scored_papers: number
  average_score: number | null
  total_projects: number
  active_projects: number
  total_users: number
  active_users: number
  import_trend: TimeSeriesDataPoint[]
  scoring_trend: TimeSeriesDataPoint[]
}

// Innovation Funnel types
export interface FunnelStage {
  stage: string
  label: string
  count: number
  percentage: number
}

export interface FunnelAnalytics {
  stages: FunnelStage[]
  total_papers: number
  conversion_rates: Record<string, number>
  period_start: string | null
  period_end: string | null
  project_id: string | null
}

// Benchmark types
export interface BenchmarkMetric {
  metric: string
  label: string
  org_value: number
  benchmark_value: number
  unit: string
  higher_is_better: boolean
}

export interface BenchmarkAnalytics {
  metrics: BenchmarkMetric[]
  org_percentile: number | null
  benchmark_data_points: number
}

// Scheduled Reports types
export type ReportType = 'dashboard_summary' | 'paper_trends' | 'team_activity'
export type ReportFormat = 'pdf' | 'csv'
export type ReportSchedule = 'daily' | 'weekly' | 'monthly'

export interface ScheduledReport {
  id: string
  name: string
  report_type: ReportType
  schedule: ReportSchedule
  recipients: string[]
  filters: Record<string, unknown>
  format: ReportFormat
  is_active: boolean
  last_sent_at: string | null
  created_at: string
  updated_at: string
}

export interface ScheduledReportListResponse {
  items: ScheduledReport[]
  total: number
  page: number
  page_size: number
}

export interface CreateScheduledReportRequest {
  name: string
  report_type: ReportType
  schedule: ReportSchedule
  recipients: string[]
  filters?: Record<string, unknown>
  format?: ReportFormat
  is_active?: boolean
}

export interface UpdateScheduledReportRequest {
  name?: string
  schedule?: ReportSchedule
  recipients?: string[]
  filters?: Record<string, unknown>
  format?: ReportFormat
  is_active?: boolean
}

// Export types
export type ExportFormat = 'csv' | 'pdf' | 'bibtex' | 'ris' | 'csljson'

// Saved Searches types
export type AlertFrequency = 'immediately' | 'daily' | 'weekly'
export type DiscoveryFrequency = 'daily' | 'weekly'

export interface SavedSearchCreator {
  id: string
  email: string
  full_name: string | null
}

export interface SavedSearch {
  id: string
  name: string
  description: string | null
  query: string
  mode: string
  filters: Record<string, unknown>
  is_public: boolean
  share_token: string | null
  share_url: string | null
  alert_enabled: boolean
  alert_frequency: AlertFrequency | null
  last_alert_at: string | null
  // Discovery fields
  semantic_description: string | null
  target_project_id: string | null
  target_project_name: string | null
  auto_import_enabled: boolean
  import_sources: string[]
  max_import_per_run: number
  discovery_frequency: DiscoveryFrequency | null
  last_discovery_at: string | null
  // Usage
  run_count: number
  last_run_at: string | null
  created_at: string
  updated_at: string
  created_by: SavedSearchCreator | null
}

export interface SavedSearchListResponse {
  items: SavedSearch[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface CreateSavedSearchRequest {
  name: string
  description?: string
  query: string
  mode?: SearchMode
  filters?: Record<string, unknown>
  is_public?: boolean
  alert_enabled?: boolean
  alert_frequency?: AlertFrequency
  // Discovery fields
  semantic_description?: string
  target_project_id?: string
  auto_import_enabled?: boolean
  import_sources?: string[]
  max_import_per_run?: number
  discovery_frequency?: DiscoveryFrequency
}

export interface UpdateSavedSearchRequest {
  name?: string
  description?: string
  query?: string
  mode?: SearchMode
  filters?: Record<string, unknown>
  is_public?: boolean
  alert_enabled?: boolean
  alert_frequency?: AlertFrequency
  // Discovery fields
  semantic_description?: string
  target_project_id?: string | null
  auto_import_enabled?: boolean
  import_sources?: string[]
  max_import_per_run?: number
  discovery_frequency?: DiscoveryFrequency | null
}

// Alerts types
export type AlertChannel = 'email' | 'in_app'
export type AlertStatus = 'pending' | 'sent' | 'failed' | 'skipped'

export interface SavedSearchBrief {
  id: string
  name: string
  query: string
}

export interface Alert {
  id: string
  name: string
  description: string | null
  channel: string
  frequency: string
  min_results: number
  is_active: boolean
  last_triggered_at: string | null
  trigger_count: number
  saved_search: SavedSearchBrief | null
  created_at: string
  updated_at: string
}

export interface AlertListResponse {
  items: Alert[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AlertResult {
  id: string
  alert_id: string
  status: AlertStatus
  papers_found: number
  new_papers: number
  paper_ids: string[]
  delivered_at: string | null
  error_message: string | null
  created_at: string
}

export interface AlertResultListResponse {
  items: AlertResult[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface CreateAlertRequest {
  name: string
  description?: string
  saved_search_id: string
  channel?: AlertChannel
  frequency?: AlertFrequency
  min_results?: number
}

export interface UpdateAlertRequest {
  name?: string
  description?: string
  channel?: AlertChannel
  frequency?: AlertFrequency
  min_results?: number
  is_active?: boolean
}

// Paper Classification
export type PaperType =
  | 'original_research'
  | 'review'
  | 'case_study'
  | 'methodology'
  | 'theoretical'
  | 'commentary'
  | 'preprint'
  | 'other'

export interface ClassificationResponse {
  paper_id: string
  paper_type: PaperType
  confidence: number
  reasoning: string
  indicators: string[]
}

// User Settings types
export interface UpdateUserRequest {
  full_name?: string
  preferences?: Record<string, unknown>
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface UpdateOrganizationRequest {
  name?: string
  type?: string
  settings?: Record<string, unknown>
}

// =============================================================================
// Groups types
// =============================================================================
export type GroupType = 'custom' | 'mailing_list' | 'speaker_pool'

export interface GroupMember {
  researcher_id: string
  researcher_name: string
  researcher_email: string | null
  h_index: number | null
  added_at: string
}

export interface Group {
  id: string
  organization_id: string
  name: string
  description: string | null
  type: GroupType
  keywords: string[]
  created_by: string | null
  created_at: string
  member_count: number
}

export interface GroupDetail extends Group {
  members: GroupMember[]
}

export interface GroupListResponse {
  items: Group[]
  total: number
  page: number
  page_size: number
}

export interface CreateGroupRequest {
  name: string
  description?: string
  type?: GroupType
  keywords?: string[]
}

export interface UpdateGroupRequest {
  name?: string
  description?: string
  type?: GroupType
  keywords?: string[]
}

export interface SuggestedMember {
  researcher_id: string
  name: string
  relevance_score: number
  matching_keywords: string[]
  affiliations: string[]
}

export interface SuggestMembersResponse {
  suggestions: SuggestedMember[]
  query_keywords: string[]
}

// =============================================================================
// Transfer types
// =============================================================================
export type TransferType = 'patent' | 'licensing' | 'startup' | 'partnership' | 'other'
export type TransferStage =
  | 'initial_contact'
  | 'discovery'
  | 'evaluation'
  | 'negotiation'
  | 'closed_won'
  | 'closed_lost'

export interface Conversation {
  id: string
  organization_id: string
  paper_id: string | null
  researcher_id: string | null
  type: TransferType
  stage: TransferStage
  title: string
  created_by: string | null
  created_at: string
  updated_at: string
  message_count: number
  resource_count: number
}

export interface ConversationMessage {
  id: string
  conversation_id: string
  sender_id: string | null
  content: string
  mentions: string[]
  created_at: string
  sender_name: string | null
}

export interface ConversationResource {
  id: string
  conversation_id: string
  name: string
  url: string | null
  file_path: string | null
  resource_type: string
  created_at: string
}

export interface StageChange {
  id: string
  conversation_id: string
  from_stage: TransferStage
  to_stage: TransferStage
  changed_by: string | null
  notes: string | null
  changed_at: string
  changed_by_name: string | null
}

export interface ConversationDetail extends Conversation {
  messages: ConversationMessage[]
  resources: ConversationResource[]
  stage_history: StageChange[]
  creator_name: string | null
  paper_title: string | null
  researcher_name: string | null
}

export interface ConversationListResponse {
  items: Conversation[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface CreateConversationRequest {
  title: string
  type: TransferType
  paper_id?: string
  researcher_id?: string
}

export interface MessageTemplate {
  id: string
  organization_id: string
  name: string
  subject: string | null
  content: string
  stage: TransferStage | null
  created_at: string
}

export interface NextStep {
  action: string
  priority: string
  rationale: string
}

export interface NextStepsResponse {
  conversation_id: string
  steps: NextStep[]
  summary: string
}

// =============================================================================
// Submissions types
// =============================================================================
export type SubmissionStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'converted'
export type AttachmentType = 'pdf' | 'supplementary' | 'patent_draft' | 'presentation' | 'other'

export interface SubmissionUser {
  id: string
  full_name: string | null
  email: string
}

export interface SubmissionAttachment {
  id: string
  filename: string
  file_size: number
  mime_type: string
  attachment_type: AttachmentType
  created_at: string
}

export interface SubmissionScore {
  id: string
  novelty: number
  ip_potential: number
  marketability: number
  feasibility: number
  commercialization: number
  overall_score: number
  overall_confidence: number
  analysis_summary: string | null
  dimension_details: Record<string, unknown>
  model_version: string
  created_at: string
}

export interface Submission {
  id: string
  organization_id: string
  title: string
  abstract: string | null
  research_field: string | null
  keywords: string[]
  status: SubmissionStatus
  doi: string | null
  publication_venue: string | null
  commercial_potential: string | null
  prior_art_notes: string | null
  ip_disclosure: string | null
  review_notes: string | null
  review_decision: string | null
  reviewed_at: string | null
  converted_paper_id: string | null
  submitted_at: string | null
  created_at: string
  updated_at: string
  submitted_by: SubmissionUser | null
  reviewed_by: SubmissionUser | null
}

export interface SubmissionDetail extends Submission {
  attachments: SubmissionAttachment[]
  scores: SubmissionScore[]
}

export interface SubmissionListResponse {
  items: Submission[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface CreateSubmissionRequest {
  title: string
  abstract?: string
  research_field?: string
  keywords?: string[]
  doi?: string
  publication_venue?: string
  commercial_potential?: string
  prior_art_notes?: string
  ip_disclosure?: string
}

export interface UpdateSubmissionRequest {
  title?: string
  abstract?: string
  research_field?: string
  keywords?: string[]
  doi?: string
  publication_venue?: string
  commercial_potential?: string
  prior_art_notes?: string
  ip_disclosure?: string
}

export interface SubmissionReviewRequest {
  decision: 'approved' | 'rejected'
  notes?: string
}

// =============================================================================
// Badges types
// =============================================================================
export type BadgeCategory = 'import' | 'scoring' | 'collaboration' | 'exploration' | 'milestone'
export type BadgeTier = 'bronze' | 'silver' | 'gold' | 'platinum'

export interface Badge {
  id: string
  name: string
  description: string
  icon: string
  category: BadgeCategory
  tier: BadgeTier
  threshold: number
  points: number
}

export interface UserBadge {
  id: string
  badge_id: string
  badge: Badge
  earned_at: string
  progress: number
}

export interface BadgeListResponse {
  items: Badge[]
  total: number
}

export interface UserBadgeListResponse {
  items: UserBadge[]
  total: number
  total_points: number
}

export interface UserStats {
  papers_imported: number
  papers_scored: number
  searches_performed: number
  projects_created: number
  notes_created: number
  authors_contacted: number
  badges_earned: number
  total_points: number
  level: number
  level_progress: number
}

// =============================================================================
// Knowledge types
// =============================================================================
export type KnowledgeScope = 'personal' | 'organization'
export type KnowledgeType = 'research_focus' | 'industry_context' | 'evaluation_criteria' | 'domain_expertise' | 'custom'

export interface KnowledgeSource {
  id: string
  organization_id: string
  user_id: string | null
  title: string
  content: string
  type: KnowledgeType
  scope: KnowledgeScope
  tags: string[]
  created_at: string
  updated_at: string
}

export interface KnowledgeSourceListResponse {
  items: KnowledgeSource[]
  total: number
}

export interface CreateKnowledgeSourceRequest {
  title: string
  content: string
  type?: KnowledgeType
  tags?: string[]
}

export interface UpdateKnowledgeSourceRequest {
  title?: string
  content?: string
  type?: KnowledgeType
  tags?: string[]
}

// =============================================================================
// Model Settings types
// =============================================================================
export interface ModelConfiguration {
  id: string
  organization_id: string
  provider: string
  model_name: string
  is_default: boolean
  has_api_key: boolean
  hosting_info: Record<string, unknown>
  max_tokens: number
  temperature: number
  workflow: string | null
  created_at: string
  updated_at: string
}

export interface ModelConfigurationListResponse {
  items: ModelConfiguration[]
  total: number
}

export interface CreateModelConfigurationRequest {
  provider: string
  model_name: string
  is_default?: boolean
  api_key?: string
  hosting_info?: Record<string, unknown>
  max_tokens?: number
  temperature?: number
  workflow?: string | null
}

export interface UpdateModelConfigurationRequest {
  provider?: string
  model_name?: string
  is_default?: boolean
  api_key?: string
  hosting_info?: Record<string, unknown>
  max_tokens?: number
  temperature?: number
  workflow?: string | null
}

export interface UsageAggregation {
  total_requests: number
  total_input_tokens: number
  total_output_tokens: number
  total_tokens: number
  total_cost_usd: number
  by_operation: Record<string, { requests: number; tokens: number; cost_usd: number }>
  by_model: Record<string, { requests: number; tokens: number; cost_usd: number }>
  by_day: Array<{ date: string; requests: number; tokens: number; cost_usd: number }>
}

// =============================================================================
// Developer API types
// =============================================================================

export interface APIKey {
  id: string
  name: string
  key_prefix: string
  permissions: string[]
  expires_at: string | null
  last_used_at: string | null
  is_active: boolean
  created_at: string
  created_by_id: string | null
}

export interface APIKeyCreated extends APIKey {
  key: string
}

export interface APIKeyListResponse {
  items: APIKey[]
  total: number
}

export interface CreateAPIKeyRequest {
  name: string
  permissions?: string[]
  expires_at?: string
}

export type WebhookEvent =
  | 'paper.created'
  | 'paper.updated'
  | 'paper.deleted'
  | 'paper.scored'
  | 'submission.created'
  | 'submission.reviewed'
  | 'project.paper_moved'
  | 'author.contacted'
  | 'alert.triggered'

export interface Webhook {
  id: string
  name: string
  url: string
  events: WebhookEvent[]
  headers: Record<string, string>
  is_active: boolean
  last_triggered_at: string | null
  failure_count: number
  created_at: string
  updated_at: string
  created_by_id: string | null
}

export interface WebhookListResponse {
  items: Webhook[]
  total: number
}

export interface CreateWebhookRequest {
  name: string
  url: string
  events: WebhookEvent[]
  headers?: Record<string, string>
}

export interface UpdateWebhookRequest {
  name?: string
  url?: string
  events?: WebhookEvent[]
  headers?: Record<string, string>
  is_active?: boolean
}

export interface WebhookTestResult {
  success: boolean
  status_code: number | null
  response_time_ms: number | null
  error: string | null
}

export type RepositoryProvider =
  | 'openalex'
  | 'pubmed'
  | 'arxiv'
  | 'crossref'
  | 'semantic_scholar'

export interface RepositorySourceConfig {
  query?: string
  filters?: Record<string, string>
  max_results?: number
}

export interface RepositorySource {
  id: string
  name: string
  provider: RepositoryProvider
  config: RepositorySourceConfig
  schedule: string | null
  is_active: boolean
  last_sync_at: string | null
  last_sync_result: Record<string, unknown> | null
  papers_synced: number
  created_at: string
  updated_at: string
  created_by_id: string | null
}

export interface RepositorySourceListResponse {
  items: RepositorySource[]
  total: number
}

export interface CreateRepositorySourceRequest {
  name: string
  provider: RepositoryProvider
  config?: RepositorySourceConfig
  schedule?: string
}

export interface UpdateRepositorySourceRequest {
  name?: string
  config?: RepositorySourceConfig
  schedule?: string
  is_active?: boolean
}

export interface RepositorySyncTriggerResponse {
  message: string
  source_id: string
  job_id: string | null
}

// API Error types
export interface ApiErrorDetail {
  msg: string
  type: string
  loc?: string[]
}

export interface ApiErrorResponse {
  detail?: string | ApiErrorDetail[]
  message?: string
  error?: string
}

export interface ApiError {
  response?: {
    data?: ApiErrorResponse
    status?: number
  }
  message?: string
}

/**
 * Extracts a user-friendly error message from an API error.
 * Handles various error formats from FastAPI and custom exceptions.
 */
export function getApiErrorMessage(error: unknown, fallback: string = 'An error occurred'): string {
  const err = error as ApiError

  // Check for response data with detail string
  if (typeof err?.response?.data?.detail === 'string') {
    return err.response.data.detail
  }

  // Check for response data with message
  if (err?.response?.data?.message) {
    return err.response.data.message
  }

  // Check for validation errors (array of details)
  if (Array.isArray(err?.response?.data?.detail)) {
    return err.response.data.detail.map(d => d.msg).join(', ')
  }

  // Check for generic error message
  if (err?.message) {
    return err.message
  }

  return fallback
}

// =============================================================================
// Compliance types
// =============================================================================

export type RetentionAction = 'archive' | 'anonymize' | 'delete'
export type RetentionEntityType = 'papers' | 'audit_logs' | 'conversations' | 'submissions' | 'alerts' | 'knowledge'
export type SOC2ControlStatus = 'implemented' | 'in_progress' | 'pending' | 'not_applicable'

export interface RetentionPolicy {
  id: string
  organization_id: string
  entity_type: RetentionEntityType
  retention_days: number
  action: RetentionAction
  is_active: boolean
  last_applied_at: string | null
  records_affected: number
  description: string | null
  created_at: string
  updated_at: string
}

export interface RetentionPolicyListResponse {
  items: RetentionPolicy[]
  total: number
}

export interface CreateRetentionPolicyRequest {
  entity_type: RetentionEntityType
  retention_days: number
  action?: RetentionAction
  description?: string
  is_active?: boolean
}

export interface UpdateRetentionPolicyRequest {
  retention_days?: number
  action?: RetentionAction
  description?: string
  is_active?: boolean
}

export interface ApplyRetentionRequest {
  dry_run?: boolean
  entity_types?: RetentionEntityType[]
}

export interface ApplyRetentionResult {
  entity_type: string
  action: string
  records_affected: number
  is_dry_run: boolean
  status: string
}

export interface ApplyRetentionResponse {
  results: ApplyRetentionResult[]
  total_affected: number
  is_dry_run: boolean
}

export interface RetentionLog {
  id: string
  organization_id: string
  policy_id: string | null
  entity_type: string
  action: string
  records_affected: number
  is_dry_run: boolean
  status: string
  error_message: string | null
  started_at: string
  completed_at: string | null
}

export interface RetentionLogListResponse {
  items: RetentionLog[]
  total: number
  page: number
  page_size: number
}

export interface AuditLogSummary {
  total_logs: number
  logs_by_action: Record<string, number>
  logs_by_resource_type: Record<string, number>
  logs_by_user: Array<{ user_id: string; count: number }>
  time_range: { earliest: string | null; latest: string | null }
}

export interface SOC2Control {
  id: string
  description: string
  status: SOC2ControlStatus
  evidence_url: string | null
  notes: string | null
  last_reviewed: string | null
}

export interface SOC2ControlCategory {
  code: string
  name: string
  controls: SOC2Control[]
}

export interface SOC2StatusResponse {
  categories: SOC2ControlCategory[]
  summary: {
    total_controls: number
    status_counts: Record<string, number>
    compliance_percentage: number
    last_updated: string
  }
}

export interface SOC2EvidenceResponse {
  control_id: string
  evidence_items: Array<{
    type: string
    name: string
    url: string | null
    uploaded_at: string | null
  }>
}

export interface DataProcessingProcessor {
  name: string
  purpose: string
  data_types: string[]
  location: string
}

export interface DataProcessingCategory {
  category: string
  types: string[]
  purpose: string
  legal_basis: string
}

export interface DataProcessingInfo {
  hosting_info: Record<string, unknown>
  data_locations: string[]
  processors: DataProcessingProcessor[]
  retention_policies: RetentionPolicy[]
  data_categories: DataProcessingCategory[]
  legal_basis: {
    processing_grounds: string
    dpo_contact: string
    data_subject_rights: string[]
  }
}

// =============================================================================
// Patent types (EPO OPS)
// =============================================================================
export interface Patent {
  patent_number: string
  title: string
  abstract?: string
  applicant?: string
  filing_date?: string
  publication_date?: string
  espacenet_url: string
  relevance_score?: number
}

export interface RelatedPatentsResponse {
  patents: Patent[]
  query: string
  total: number
}

// =============================================================================
// Citation Graph types (Semantic Scholar)
// =============================================================================
export interface CitationNode {
  paper_id: string
  title: string
  year?: number
  citation_count?: number
  is_root: boolean
}

export interface CitationEdge {
  source: string
  target: string
  type: 'cites' | 'cited_by'
}

export interface CitationGraphResponse {
  nodes: CitationNode[]
  edges: CitationEdge[]
  root_paper_id: string
}

export interface AuditLog {
  id: string
  user_id: string | null
  organization_id: string | null
  action: string
  resource_type: string | null
  resource_id: string | null
  details: Record<string, unknown>
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLog[]
  total: number
  page: number
  page_size: number
  pages: number
}

// Notification types
export type NotificationType = 'alert' | 'badge' | 'system'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message: string | null
  is_read: boolean
  resource_type: string | null
  resource_id: string | null
  created_at: string
}

export interface NotificationListResponse {
  items: NotificationItem[]
  total: number
  page: number
  page_size: number
  pages: number
  unread_count: number
}

export interface MarkReadRequest {
  notification_ids: string[]
}

// =============================================================================
// Trend Radar types
// =============================================================================

export interface TrendTopic {
  id: string
  organization_id: string
  created_by_id: string | null
  name: string
  description: string
  color: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  matched_papers_count: number
  avg_overall_score: number | null
  patent_count: number
  last_analyzed_at: string | null
}

export interface TrendTopicListResponse {
  items: TrendTopic[]
  total: number
}

export interface PatentResult {
  patent_number: string
  title: string
  abstract: string | null
  applicant: string | null
  filing_date: string | null
  publication_date: string | null
  espacenet_url: string
}

export interface KeywordCount {
  keyword: string
  count: number
}

export interface TrendTimelinePoint {
  date: string
  count: number
}

export interface TrendSnapshot {
  id: string
  trend_topic_id: string
  matched_papers_count: number
  avg_novelty: number | null
  avg_ip_potential: number | null
  avg_marketability: number | null
  avg_feasibility: number | null
  avg_commercialization: number | null
  avg_team_readiness: number | null
  avg_overall_score: number | null
  patent_count: number
  patent_results: PatentResult[]
  summary: string | null
  key_insights: string[]
  top_keywords: KeywordCount[]
  timeline_data: TrendTimelinePoint[]
  created_at: string
}

export interface TrendPaper {
  id: string
  title: string
  abstract: string | null
  doi: string | null
  journal: string | null
  publication_date: string | null
  relevance_score: number
  overall_score: number | null
  novelty: number | null
  ip_potential: number | null
}

export interface TrendPaperListResponse {
  items: TrendPaper[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface TrendDashboard {
  topic: TrendTopic
  snapshot: TrendSnapshot | null
  top_papers: TrendPaper[]
}

// Discovery types
export type DiscoveryRunStatus = 'running' | 'completed' | 'completed_with_errors' | 'failed'

export interface DiscoveryRun {
  id: string
  saved_search_id: string
  organization_id: string
  status: DiscoveryRunStatus
  source: string
  papers_found: number
  papers_imported: number
  papers_skipped: number
  papers_added_to_project: number
  error_message: string | null
  started_at: string
  completed_at: string | null
  created_at: string
}

export interface DiscoveryRunListResponse {
  items: DiscoveryRun[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface DiscoveryProfileSummary {
  id: string
  name: string
  query: string
  semantic_description: string | null
  import_sources: string[]
  target_project_id: string | null
  target_project_name: string | null
  discovery_frequency: DiscoveryFrequency | null
  max_import_per_run: number
  last_discovery_at: string | null
  auto_import_enabled: boolean
  created_at: string
  last_run_status: DiscoveryRunStatus | null
  total_papers_imported: number
}

export interface DiscoveryProfileListResponse {
  items: DiscoveryProfileSummary[]
  total: number
}

export interface DiscoveryTriggerResponse {
  saved_search_id: string
  runs: DiscoveryRun[]
  total_papers_imported: number
  total_papers_added_to_project: number
  message: string
}
