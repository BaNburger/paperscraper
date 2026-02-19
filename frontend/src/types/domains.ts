import type { components as OpenApiComponents } from '@/api/generated/openapi'
import type { DiscoveryFrequency } from '@/types/core'

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

export type DiscoveryRunResponse = OpenApiComponents['schemas']['DiscoveryRunResponse']

export interface DiscoveryRunListResponse {
  items: DiscoveryRunResponse[]
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
  runs: DiscoveryRunResponse[]
  total_papers_imported: number
  total_papers_added_to_project: number
  message: string
}
