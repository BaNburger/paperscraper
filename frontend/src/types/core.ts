import type { components as OpenApiComponents } from '@/api/generated/openapi'

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
  subscription_tier: OpenApiComponents['schemas']['SubscriptionTier']
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
  role: UserRole
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
export type UserRole = OpenApiComponents['schemas']['UserRole']
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

export interface ScoringAuthorProfile {
  name: string
  orcid?: string
  github_username?: string
  github_public_repos?: number
  github_followers?: number
  github_top_languages: string[]
  github_popular_repos: string[]
  orcid_current_employment?: string
  orcid_past_affiliations: string[]
  orcid_funding_count?: number
  orcid_peer_review_count?: number
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
  author_profiles?: ScoringAuthorProfile[]
}

export interface ScoreResponse {
  scores: PaperScore
  paper: Paper
}

// Project domain (research groups)
export interface Project {
  id: string
  organization_id: string
  name: string
  description?: string
  institution_name?: string
  openalex_institution_id?: string
  pi_name?: string
  openalex_author_id?: string
  paper_count: number
  cluster_count: number
  sync_status: 'idle' | 'importing' | 'clustering' | 'ready' | 'failed'
  last_synced_at?: string
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

export interface ResearchCluster {
  id: string
  label: string
  description?: string
  keywords: string[]
  paper_count: number
  top_papers: ClusterPaper[]
}

export interface ClusterPaper {
  id: string
  title: string
  authors_display: string
  publication_date?: string
  citations_count?: number
  similarity_score?: number
}

export interface ClusterDetail {
  id: string
  label: string
  description?: string
  keywords: string[]
  paper_count: number
  papers: ClusterPaper[]
}

export interface InstitutionSearchResult {
  openalex_id: string
  display_name: string
  country_code?: string
  type?: string
  works_count: number
  cited_by_count: number
}

export interface AuthorSearchResult {
  openalex_id: string
  display_name: string
  works_count: number
  cited_by_count: number
  last_known_institution?: string
}

export interface CreateProject {
  name: string
  description?: string
  openalex_institution_id?: string
  openalex_author_id?: string
  institution_name?: string
  pi_name?: string
  max_papers?: number
}

export interface SyncResponse {
  project_id: string
  status: string
  message: string
}

// Search types
export type SearchMode = OpenApiComponents['schemas']['SearchMode']
export type SearchRequest = OpenApiComponents['schemas']['SearchRequest']
export type SearchResultItem = OpenApiComponents['schemas']['SearchResultItem']
export type SearchResponse = OpenApiComponents['schemas']['SearchResponse']
export type SimilarPapersResponse = OpenApiComponents['schemas']['SimilarPapersResponse']
export type IngestionJobResponse = OpenApiComponents['schemas']['IngestJobResponse']
export type IngestionRunResponse = OpenApiComponents['schemas']['IngestRunResponse']

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

