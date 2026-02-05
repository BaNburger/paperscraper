// Auth types
export interface Organization {
  id: string
  name: string
  type: string
  subscription_tier: 'free' | 'pro' | 'enterprise'
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
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

// Scoring types
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

// Export types
export type ExportFormat = 'csv' | 'pdf' | 'bibtex'

// Saved Searches types
export type AlertFrequency = 'immediately' | 'daily' | 'weekly'

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
}

export interface UpdateModelConfigurationRequest {
  provider?: string
  model_name?: string
  is_default?: boolean
  api_key?: string
  hosting_info?: Record<string, unknown>
  max_tokens?: number
  temperature?: number
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
