import type {
  Paper,
  PaperDetail,
  PaperListResponse,
  PaperScore,
  ScoreResponse,
  Project,
  ProjectListResponse,
  ResearchCluster,
  ClusterPaper,
  ClusterDetail,
  InstitutionSearchResult,
  AuthorSearchResult,
  CreateProject,
  SyncResponse,
  SearchRequest,
  SearchResponse,
  AuthorProfile,
  AuthorDetail,
  AuthorListResponse,
  AuthorContact,
  AuthorContactStats,
  CreateContactRequest,
  EnrichmentResult,
  DashboardSummary,
  TeamOverview,
  PaperAnalytics,
  FunnelAnalytics,
  BenchmarkAnalytics,
  ExportFormat,
  SavedSearch,
  SavedSearchListResponse,
  CreateSavedSearchRequest,
  UpdateSavedSearchRequest,
  Alert,
  AlertListResponse,
  AlertResultListResponse,
  CreateAlertRequest,
  UpdateAlertRequest,
  ClassificationResponse,
  Group,
  GroupDetail,
  GroupListResponse,
  CreateGroupRequest,
  UpdateGroupRequest,
  SuggestMembersResponse,
  Conversation,
  ConversationDetail,
  ConversationListResponse,
  CreateConversationRequest,
  ConversationMessage,
  ConversationResource,
  MessageTemplate,
  NextStepsResponse,
  Submission,
  SubmissionDetail,
  SubmissionListResponse,
  CreateSubmissionRequest,
  UpdateSubmissionRequest,
  SubmissionReviewRequest,
  SubmissionAttachment,
  SubmissionScore,
  BadgeListResponse,
  UserBadgeListResponse,
  UserStats,
  KnowledgeSource,
  KnowledgeSourceListResponse,
  CreateKnowledgeSourceRequest,
  UpdateKnowledgeSourceRequest,
  ModelConfiguration,
  ModelConfigurationListResponse,
  CreateModelConfigurationRequest,
  UpdateModelConfigurationRequest,
  UsageAggregation,
  ScheduledReport,
  ScheduledReportListResponse,
  CreateScheduledReportRequest,
  UpdateScheduledReportRequest,
  RelatedPatentsResponse,
  CitationGraphResponse,
  NotificationListResponse,
  LibraryCollection,
  LibraryCollectionItem,
  ReaderPayload,
  PaperHighlight,
  PaperTag,
  ZoteroConnectionStatus,
  ZoteroSyncRun,
  TrendTopic,
  TrendTopicListResponse,
  TrendSnapshot,
  TrendDashboard,
  TrendPaperListResponse,
  DiscoveryProfileListResponse,
  DiscoveryRunListResponse,
  DiscoveryRunResponse,
  DiscoveryTriggerResponse,
} from '@/types'

import { api } from '@/api/http/client'
type IngestionRunStatus = 'queued' | 'running' | 'completed' | 'completed_with_errors' | 'failed'

interface IngestionJobResponse {
  ingest_run_id: string
}

interface IngestionRunResponse {
  id: string
  status: IngestionRunStatus
  stats_json?: Record<string, unknown>
  error_message?: string | null
}

interface IngestionSummaryResult {
  papers_created: number
  papers_skipped: number
  errors: string[]
}

const INGESTION_TERMINAL_STATUSES = new Set<IngestionRunStatus>([
  'completed',
  'completed_with_errors',
  'failed',
])
const INGESTION_POLL_INTERVAL_MS = 1200
const INGESTION_POLL_TIMEOUT_MS = 3 * 60 * 1000

function toInt(value: unknown): number {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return Math.trunc(value)
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number.parseInt(value, 10)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }
  return 0
}

function extractIngestionErrors(run: IngestionRunResponse): string[] {
  const statsErrors = run.stats_json?.errors
  if (Array.isArray(statsErrors)) {
    const normalized = statsErrors.filter((item): item is string => typeof item === 'string')
    if (normalized.length > 0) {
      return normalized
    }
  }
  if (run.status === 'failed' && run.error_message) {
    return [run.error_message]
  }
  return []
}

function summarizeIngestionRun(run: IngestionRunResponse): IngestionSummaryResult {
  return {
    papers_created: toInt(run.stats_json?.papers_created),
    papers_skipped: toInt(
      run.stats_json?.source_records_duplicates ?? run.stats_json?.papers_skipped
    ),
    errors: extractIngestionErrors(run),
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

async function waitForIngestionRun(
  runId: string,
  timeoutMs = INGESTION_POLL_TIMEOUT_MS,
): Promise<IngestionSummaryResult> {
  const startedAt = Date.now()

  while (Date.now() - startedAt < timeoutMs) {
    const response = await api.get<IngestionRunResponse>(`/ingestion/runs/${runId}`)
    const run = response.data
    if (INGESTION_TERMINAL_STATUSES.has(run.status)) {
      return summarizeIngestionRun(run)
    }
    await sleep(INGESTION_POLL_INTERVAL_MS)
  }

  return {
    papers_created: 0,
    papers_skipped: 0,
    errors: ['Timed out waiting for ingestion run completion'],
  }
}

async function queueAndAwaitIngestionRun(
  path: string,
  payload: Record<string, unknown>,
): Promise<IngestionSummaryResult> {
  const response = await api.post<IngestionJobResponse>(path, payload)
  return waitForIngestionRun(response.data.ingest_run_id)
}

// Papers API
export const papersApi = {
  list: async (params: {
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaperListResponse> => {
    const response = await api.get<PaperListResponse>('/papers/', { params })
    return response.data
  },

  get: async (id: string): Promise<PaperDetail> => {
    const response = await api.get<PaperDetail>(`/papers/${id}`)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/papers/${id}`)
  },

  ingestByDoi: async (doi: string): Promise<Paper> => {
    const response = await api.post<Paper>('/papers/ingest/doi', { doi })
    return response.data
  },

  ingestFromOpenAlex: async (params: {
    query: string
    max_results?: number
    filters?: Record<string, string>
  }): Promise<{ papers_created: number; papers_skipped: number; errors: string[] }> => {
    return queueAndAwaitIngestionRun('/ingestion/sources/openalex/runs', params)
  },

  ingestFromPubMed: async (params: {
    query: string
    max_results?: number
  }): Promise<{ papers_created: number; papers_skipped: number; errors: string[] }> => {
    return queueAndAwaitIngestionRun('/ingestion/sources/pubmed/runs', params)
  },

  ingestFromArxiv: async (params: {
    query: string
    max_results?: number
    category?: string
  }): Promise<{ papers_created: number; papers_skipped: number; errors: string[] }> => {
    return queueAndAwaitIngestionRun('/ingestion/sources/arxiv/runs', params)
  },

  uploadPdf: async (file: File): Promise<Paper> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<Paper>('/papers/upload/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  generatePitch: async (paperId: string): Promise<Paper> => {
    const response = await api.post<Paper>(`/papers/${paperId}/generate-pitch`)
    return response.data
  },

  generateSimplifiedAbstract: async (paperId: string): Promise<Paper> => {
    const response = await api.post<Paper>(`/papers/${paperId}/generate-simplified-abstract`)
    return response.data
  },

  ingestFromSemanticScholar: async (params: {
    query: string
    max_results?: number
  }): Promise<{ papers_created: number; papers_skipped: number; errors: string[] }> => {
    return queueAndAwaitIngestionRun('/ingestion/sources/semantic-scholar/runs', params)
  },

  getRelatedPatents: async (paperId: string): Promise<RelatedPatentsResponse> => {
    const response = await api.get<RelatedPatentsResponse>(`/papers/${paperId}/patents`)
    return response.data
  },

  getCitationGraph: async (paperId: string): Promise<CitationGraphResponse> => {
    const response = await api.get<CitationGraphResponse>(`/papers/${paperId}/citations`)
    return response.data
  },
}

// Library V2 API
export const libraryApi = {
  listCollections: async (): Promise<{ items: LibraryCollection[]; total: number }> => {
    const response = await api.get<{ items: LibraryCollection[]; total: number }>('/library/collections')
    return response.data
  },

  createCollection: async (data: {
    name: string
    description?: string
    parent_id?: string
  }): Promise<LibraryCollection> => {
    const response = await api.post<LibraryCollection>('/library/collections', data)
    return response.data
  },

  updateCollection: async (
    collectionId: string,
    data: {
      name?: string
      description?: string
      parent_id?: string | null
    }
  ): Promise<LibraryCollection> => {
    const response = await api.patch<LibraryCollection>(`/library/collections/${collectionId}`, data)
    return response.data
  },

  deleteCollection: async (collectionId: string): Promise<void> => {
    await api.delete(`/library/collections/${collectionId}`)
  },

  addPaperToCollection: async (
    collectionId: string,
    paperId: string
  ): Promise<LibraryCollectionItem> => {
    const response = await api.post<LibraryCollectionItem>(
      `/library/collections/${collectionId}/papers/${paperId}`
    )
    return response.data
  },

  removePaperFromCollection: async (
    collectionId: string,
    paperId: string
  ): Promise<LibraryCollectionItem> => {
    const response = await api.delete<LibraryCollectionItem>(
      `/library/collections/${collectionId}/papers/${paperId}`
    )
    return response.data
  },

  getReader: async (paperId: string): Promise<ReaderPayload> => {
    const response = await api.get<ReaderPayload>(`/library/papers/${paperId}/reader`)
    return response.data
  },

  hydrateFullText: async (
    paperId: string
  ): Promise<{
    paper_id: string
    hydrated: boolean
    source?: string | null
    chunks_created: number
    message: string
  }> => {
    const response = await api.post(`/library/papers/${paperId}/hydrate-fulltext`)
    return response.data
  },

  listHighlights: async (
    paperId: string,
    includeInactive = false
  ): Promise<{ items: PaperHighlight[]; total: number }> => {
    const response = await api.get<{ items: PaperHighlight[]; total: number }>(
      `/library/papers/${paperId}/highlights`,
      { params: { include_inactive: includeInactive } }
    )
    return response.data
  },

  createHighlight: async (
    paperId: string,
    data: {
      chunk_id?: string
      chunk_ref?: string
      quote: string
      insight_summary: string
      confidence?: number
    }
  ): Promise<PaperHighlight> => {
    const response = await api.post<PaperHighlight>(`/library/papers/${paperId}/highlights`, data)
    return response.data
  },

  generateHighlights: async (
    paperId: string,
    targetCount = 8
  ): Promise<{ items: PaperHighlight[]; total: number }> => {
    const response = await api.post<{ items: PaperHighlight[]; total: number }>(
      `/library/papers/${paperId}/highlights/generate`,
      { target_count: targetCount }
    )
    return response.data
  },

  updateHighlight: async (
    paperId: string,
    highlightId: string,
    data: {
      quote?: string
      insight_summary?: string
      confidence?: number
      is_active?: boolean
    }
  ): Promise<PaperHighlight> => {
    const response = await api.patch<PaperHighlight>(
      `/library/papers/${paperId}/highlights/${highlightId}`,
      data
    )
    return response.data
  },

  deleteHighlight: async (paperId: string, highlightId: string): Promise<void> => {
    await api.delete(`/library/papers/${paperId}/highlights/${highlightId}`)
  },

  listTags: async (): Promise<{ items: Array<{ tag: string; usage_count: number }>; total: number }> => {
    const response = await api.get<{ items: Array<{ tag: string; usage_count: number }>; total: number }>(
      '/library/tags'
    )
    return response.data
  },

  addPaperTag: async (paperId: string, tag: string): Promise<PaperTag> => {
    const response = await api.post<PaperTag>(`/library/papers/${paperId}/tags`, { tag })
    return response.data
  },

  removePaperTag: async (paperId: string, tag: string): Promise<{ removed: boolean }> => {
    const response = await api.delete<{ removed: boolean }>(`/library/papers/${paperId}/tags/${tag}`)
    return response.data
  },
}

// Integrations API
export const integrationsApi = {
  connectZotero: async (data: {
    user_id: string
    api_key: string
    base_url?: string
    library_type?: 'users' | 'groups'
  }): Promise<ZoteroConnectionStatus> => {
    const response = await api.post<ZoteroConnectionStatus>('/integrations/zotero/connect', data)
    return response.data
  },

  getZoteroStatus: async (): Promise<ZoteroConnectionStatus> => {
    const response = await api.get<ZoteroConnectionStatus>('/integrations/zotero/status')
    return response.data
  },

  syncZoteroOutbound: async (paperIds?: string[]): Promise<ZoteroSyncRun> => {
    const response = await api.post<ZoteroSyncRun>('/integrations/zotero/sync/outbound', {
      paper_ids: paperIds && paperIds.length ? paperIds : null,
    })
    return response.data
  },

  syncZoteroInbound: async (): Promise<ZoteroSyncRun> => {
    const response = await api.post<ZoteroSyncRun>('/integrations/zotero/sync/inbound')
    return response.data
  },

  getZoteroSyncRun: async (runId: string): Promise<ZoteroSyncRun> => {
    const response = await api.get<ZoteroSyncRun>(`/integrations/zotero/sync-runs/${runId}`)
    return response.data
  },
}

// Scoring API
export const scoringApi = {
  scorePaper: async (paperId: string): Promise<ScoreResponse> => {
    const response = await api.post<ScoreResponse>(`/scoring/papers/${paperId}/score`)
    return response.data
  },

  getScores: async (paperId: string): Promise<PaperScore[]> => {
    const response = await api.get<PaperScore[]>(`/scoring/papers/${paperId}/scores`)
    return response.data
  },

  getLatestScore: async (paperId: string): Promise<PaperScore | null> => {
    try {
      const response = await api.get<PaperScore>(`/scoring/papers/${paperId}/scores/latest`)
      return response.data
    } catch (error) {
      const axiosError = error as AxiosError
      if (axiosError.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  listScores: async (params?: {
    page?: number
    page_size?: number
    min_score?: number
    max_score?: number
  }): Promise<{ items: ScoreResponse[]; total: number; page: number; pages: number }> => {
    const response = await api.get('/scoring/', { params })
    return response.data
  },
}

// Projects API
export const projectsApi = {
  // Search
  searchInstitutions: async (query: string): Promise<InstitutionSearchResult[]> => {
    const response = await api.get<InstitutionSearchResult[]>('/projects/search/institutions', {
      params: { query },
    })
    return response.data
  },

  searchAuthors: async (query: string): Promise<AuthorSearchResult[]> => {
    const response = await api.get<AuthorSearchResult[]>('/projects/search/authors', {
      params: { query },
    })
    return response.data
  },

  // CRUD
  list: async (params?: { page?: number; page_size?: number; search?: string }): Promise<ProjectListResponse> => {
    const response = await api.get<ProjectListResponse>('/projects/', { params })
    return response.data
  },

  get: async (id: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${id}`)
    return response.data
  },

  create: async (data: CreateProject): Promise<Project> => {
    const response = await api.post<Project>('/projects/', data)
    return response.data
  },

  update: async (
    id: string,
    data: { name?: string; description?: string }
  ): Promise<Project> => {
    const response = await api.patch<Project>(`/projects/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`)
  },

  // Sync & Clusters
  sync: async (id: string): Promise<SyncResponse> => {
    const response = await api.post<SyncResponse>(`/projects/${id}/sync`)
    return response.data
  },

  listClusters: async (id: string): Promise<ResearchCluster[]> => {
    const response = await api.get<ResearchCluster[]>(`/projects/${id}/clusters`)
    return response.data
  },

  getCluster: async (projectId: string, clusterId: string): Promise<ClusterDetail> => {
    const response = await api.get<ClusterDetail>(
      `/projects/${projectId}/clusters/${clusterId}`
    )
    return response.data
  },

  updateCluster: async (
    projectId: string,
    clusterId: string,
    data: { label: string }
  ): Promise<void> => {
    await api.patch(`/projects/${projectId}/clusters/${clusterId}`, data)
  },

  listPapers: async (id: string): Promise<ClusterPaper[]> => {
    const response = await api.get<ClusterPaper[]>(`/projects/${id}/papers`)
    return response.data
  },
}

// Search API
export const searchApi = {
  search: async (data: SearchRequest): Promise<SearchResponse> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await api.post<any>('/search/', data)
    const raw = response.data
    // Transform backend flat items to frontend nested SearchResult format
    const results = (raw.items ?? []).map((item: Record<string, unknown>) => {
      // Convert highlights array [{field, snippet}] to {title?, abstract?}
      const highlightsArr = (item.highlights ?? []) as Array<{ field: string; snippet: string }>
      const highlights: Record<string, string> = {}
      for (const h of highlightsArr) {
        highlights[h.field] = h.snippet
      }
      return {
        paper: {
          id: item.id,
          title: item.title,
          abstract: item.abstract,
          doi: item.doi,
          source: item.source,
          journal: item.journal,
          publication_date: item.publication_date,
          keywords: item.keywords,
          citations_count: item.citations_count,
          has_embedding: item.has_embedding,
          created_at: item.created_at,
        },
        relevance_score: item.relevance_score ?? 0,
        highlights,
        latest_score: item.score ?? null,
      }
    })
    return {
      results,
      total: raw.total,
      page: raw.page,
      page_size: raw.page_size,
      pages: raw.pages,
      query: raw.query,
      mode: raw.mode,
    }
  },

  findSimilar: async (
    paperId: string,
    params?: { limit?: number }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ): Promise<any> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await api.get<any>(`/search/similar/${paperId}`, { params })
    const raw = response.data
    // Transform backend SimilarPapersResponse to frontend expected format
    const results = (raw.similar_papers ?? []).map((item: Record<string, unknown>) => ({
      paper: {
        id: item.id,
        title: item.title,
        abstract: item.abstract,
        doi: item.doi,
        source: item.source,
        journal: item.journal,
        publication_date: item.publication_date,
        keywords: item.keywords,
      },
      relevance_score: item.similarity_score ?? 0,
      highlights: {},
    }))
    return {
      paper_id: raw.paper_id,
      similar: { results, total: raw.total_found },
    }
  },

  getEmbeddingStats: async (): Promise<{
    total_papers: number
    with_embedding: number
    without_embedding: number
    embedding_coverage: number
  }> => {
    const response = await api.get('/search/embeddings/stats')
    return response.data
  },
}

// Authors API
export const authorsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    search?: string
  }): Promise<AuthorListResponse> => {
    const response = await api.get<AuthorListResponse>('/authors/', { params })
    return response.data
  },

  getProfile: async (authorId: string): Promise<AuthorProfile> => {
    const response = await api.get<AuthorProfile>(`/authors/${authorId}`)
    return response.data
  },

  getDetail: async (authorId: string): Promise<AuthorDetail> => {
    const response = await api.get<AuthorDetail>(`/authors/${authorId}/detail`)
    return response.data
  },

  createContact: async (authorId: string, data: CreateContactRequest): Promise<AuthorContact> => {
    const response = await api.post<AuthorContact>(`/authors/${authorId}/contacts`, data)
    return response.data
  },

  updateContact: async (
    authorId: string,
    contactId: string,
    data: Partial<CreateContactRequest>
  ): Promise<AuthorContact> => {
    const response = await api.patch<AuthorContact>(`/authors/${authorId}/contacts/${contactId}`, data)
    return response.data
  },

  deleteContact: async (authorId: string, contactId: string): Promise<void> => {
    await api.delete(`/authors/${authorId}/contacts/${contactId}`)
  },

  getContactStats: async (authorId: string): Promise<AuthorContactStats> => {
    const response = await api.get<AuthorContactStats>(`/authors/${authorId}/contacts/stats`)
    return response.data
  },

  enrichAuthor: async (
    authorId: string,
    params?: { source?: string; force_update?: boolean }
  ): Promise<EnrichmentResult> => {
    const response = await api.post<EnrichmentResult>(`/authors/${authorId}/enrich`, params || {})
    return response.data
  },
}

// Analytics API
export const analyticsApi = {
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>('/analytics/dashboard')
    return response.data
  },

  getTeamOverview: async (): Promise<TeamOverview> => {
    const response = await api.get<TeamOverview>('/analytics/team')
    return response.data
  },

  getPaperAnalytics: async (params?: { days?: number }): Promise<PaperAnalytics> => {
    const response = await api.get<PaperAnalytics>('/analytics/papers', { params })
    return response.data
  },

  getFunnelAnalytics: async (params?: {
    project_id?: string
    start_date?: string
    end_date?: string
  }): Promise<FunnelAnalytics> => {
    const response = await api.get<FunnelAnalytics>('/analytics/funnel', { params })
    return response.data
  },

  getBenchmarks: async (): Promise<BenchmarkAnalytics> => {
    const response = await api.get<BenchmarkAnalytics>('/analytics/benchmarks')
    return response.data
  },
}

// Scheduled Reports API
export const reportsApi = {
  listScheduledReports: async (params?: {
    page?: number
    page_size?: number
    is_active?: boolean
  }): Promise<ScheduledReportListResponse> => {
    const response = await api.get<ScheduledReportListResponse>('/reports/scheduled', { params })
    return response.data
  },

  getScheduledReport: async (reportId: string): Promise<ScheduledReport> => {
    const response = await api.get<ScheduledReport>(`/reports/scheduled/${reportId}`)
    return response.data
  },

  createScheduledReport: async (data: CreateScheduledReportRequest): Promise<ScheduledReport> => {
    const response = await api.post<ScheduledReport>('/reports/scheduled', data)
    return response.data
  },

  updateScheduledReport: async (
    reportId: string,
    data: UpdateScheduledReportRequest
  ): Promise<ScheduledReport> => {
    const response = await api.patch<ScheduledReport>(`/reports/scheduled/${reportId}`, data)
    return response.data
  },

  deleteScheduledReport: async (reportId: string): Promise<void> => {
    await api.delete(`/reports/scheduled/${reportId}`)
  },

  runScheduledReport: async (reportId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<{ success: boolean; message: string }>(
      `/reports/scheduled/${reportId}/run`
    )
    return response.data
  },
}

// Export API
export const exportApi = {
  exportCsv: async (params?: {
    paper_ids?: string[]
    include_scores?: boolean
    include_authors?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/csv', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportBibtex: async (params?: {
    paper_ids?: string[]
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/bibtex', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportPdf: async (params?: {
    paper_ids?: string[]
    include_scores?: boolean
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/pdf', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportRis: async (params?: {
    paper_ids?: string[]
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/ris', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportCslJson: async (params?: {
    paper_ids?: string[]
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/csljson', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  batchExport: async (
    paperIds: string[],
    format: ExportFormat,
    options?: {
      include_scores?: boolean
      include_authors?: boolean
    }
  ): Promise<Blob> => {
    const response = await api.post(
      '/export/batch',
      { paper_ids: paperIds },
      {
        params: { format, ...options },
        responseType: 'blob',
      }
    )
    return response.data
  },

  // Helper to trigger download
  downloadFile: (blob: Blob, filename: string): void => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

// Saved Searches API
export const savedSearchesApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    include_public?: boolean
  }): Promise<SavedSearchListResponse> => {
    const response = await api.get<SavedSearchListResponse>('/saved-searches', { params })
    return response.data
  },

  get: async (id: string): Promise<SavedSearch> => {
    const response = await api.get<SavedSearch>(`/saved-searches/${id}`)
    return response.data
  },

  getByShareToken: async (shareToken: string): Promise<SavedSearch> => {
    const response = await api.get<SavedSearch>(`/saved-searches/shared/${shareToken}`)
    return response.data
  },

  create: async (data: CreateSavedSearchRequest): Promise<SavedSearch> => {
    const response = await api.post<SavedSearch>('/saved-searches', data)
    return response.data
  },

  update: async (id: string, data: UpdateSavedSearchRequest): Promise<SavedSearch> => {
    const response = await api.patch<SavedSearch>(`/saved-searches/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/saved-searches/${id}`)
  },

  generateShareLink: async (id: string): Promise<{ share_token: string; share_url: string }> => {
    const response = await api.post<{ share_token: string; share_url: string }>(
      `/saved-searches/${id}/share`
    )
    return response.data
  },

  revokeShareLink: async (id: string): Promise<void> => {
    await api.delete(`/saved-searches/${id}/share`)
  },

  run: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>(`/saved-searches/${id}/run`, null, { params })
    return response.data
  },
}

// Alerts API
export const alertsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    active_only?: boolean
  }): Promise<AlertListResponse> => {
    const response = await api.get<AlertListResponse>('/alerts', { params })
    return response.data
  },

  get: async (id: string): Promise<Alert> => {
    const response = await api.get<Alert>(`/alerts/${id}`)
    return response.data
  },

  create: async (data: CreateAlertRequest): Promise<Alert> => {
    const response = await api.post<Alert>('/alerts', data)
    return response.data
  },

  update: async (id: string, data: UpdateAlertRequest): Promise<Alert> => {
    const response = await api.patch<Alert>(`/alerts/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/alerts/${id}`)
  },

  getResults: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<AlertResultListResponse> => {
    const response = await api.get<AlertResultListResponse>(`/alerts/${id}/results`, { params })
    return response.data
  },

  test: async (id: string): Promise<{
    success: boolean
    message: string
    papers_found: number
    sample_papers: Array<{ id: string; title: string; journal?: string; publication_date?: string }>
  }> => {
    const response = await api.post(`/alerts/${id}/test`)
    return response.data
  },

  trigger: async (id: string): Promise<void> => {
    await api.post(`/alerts/${id}/trigger`)
  },
}

// Classification API (extension of scoring)
export const classificationApi = {
  classifyPaper: async (paperId: string): Promise<ClassificationResponse> => {
    const response = await api.post<ClassificationResponse>(`/scoring/papers/${paperId}/classify`)
    return response.data
  },

  batchClassify: async (paperIds: string[]): Promise<{
    total: number
    succeeded: number
    failed: number
    results: ClassificationResponse[]
    errors: Array<{ paper_id: string; error: string }>
  }> => {
    const response = await api.post('/scoring/classification/batch', paperIds)
    return response.data
  },

  getUnclassified: async (limit?: number): Promise<{
    count: number
    papers: Array<{ id: string; title: string; source: string; created_at: string }>
  }> => {
    const response = await api.get('/scoring/classification/unclassified', {
      params: { limit },
    })
    return response.data
  },
}

// Groups API
export const groupsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    type?: string
  }): Promise<GroupListResponse> => {
    const response = await api.get<GroupListResponse>('/groups/', { params })
    return response.data
  },

  get: async (id: string): Promise<GroupDetail> => {
    const response = await api.get<GroupDetail>(`/groups/${id}`)
    return response.data
  },

  create: async (data: CreateGroupRequest): Promise<Group> => {
    const response = await api.post<Group>('/groups/', data)
    return response.data
  },

  update: async (id: string, data: UpdateGroupRequest): Promise<Group> => {
    const response = await api.patch<Group>(`/groups/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/groups/${id}`)
  },

  addMembers: async (groupId: string, researcherIds: string[]): Promise<{ added: number }> => {
    const response = await api.post<{ added: number }>(`/groups/${groupId}/members`, {
      researcher_ids: researcherIds,
    })
    return response.data
  },

  removeMember: async (groupId: string, researcherId: string): Promise<void> => {
    await api.delete(`/groups/${groupId}/members/${researcherId}`)
  },

  suggestMembers: async (keywords: string[], targetSize?: number): Promise<SuggestMembersResponse> => {
    const response = await api.post<SuggestMembersResponse>('/groups/suggest-members', {
      keywords,
      target_size: targetSize || 10,
    })
    return response.data
  },

  exportCsv: async (groupId: string): Promise<Blob> => {
    const response = await api.get(`/groups/${groupId}/export`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// Transfer API
export const transferApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    stage?: string
    search?: string
  }): Promise<ConversationListResponse> => {
    const response = await api.get<ConversationListResponse>('/transfer/', { params })
    return response.data
  },

  get: async (id: string): Promise<ConversationDetail> => {
    const response = await api.get<ConversationDetail>(`/transfer/${id}`)
    return response.data
  },

  create: async (data: CreateConversationRequest): Promise<Conversation> => {
    const response = await api.post<Conversation>('/transfer/', data)
    return response.data
  },

  updateStage: async (id: string, stage: string, notes?: string): Promise<Conversation> => {
    const response = await api.patch<Conversation>(`/transfer/${id}`, { stage, notes })
    return response.data
  },

  sendMessage: async (conversationId: string, content: string, mentions?: string[]): Promise<ConversationMessage> => {
    const response = await api.post<ConversationMessage>(`/transfer/${conversationId}/messages`, {
      content,
      mentions: mentions || [],
    })
    return response.data
  },

  sendMessageFromTemplate: async (
    conversationId: string,
    templateId: string,
    mentions?: string[]
  ): Promise<ConversationMessage> => {
    const response = await api.post<ConversationMessage>(
      `/transfer/${conversationId}/messages/from-template`,
      { template_id: templateId, mentions: mentions || [] }
    )
    return response.data
  },

  addResource: async (
    conversationId: string,
    data: { name: string; url?: string; file_path?: string; resource_type: string }
  ): Promise<ConversationResource> => {
    const response = await api.post<ConversationResource>(`/transfer/${conversationId}/resources`, data)
    return response.data
  },

  uploadResource: async (conversationId: string, file: File): Promise<ConversationResource> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<ConversationResource>(
      `/transfer/${conversationId}/resources/upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  getNextSteps: async (conversationId: string): Promise<NextStepsResponse> => {
    const response = await api.get<NextStepsResponse>(`/transfer/${conversationId}/next-steps`)
    return response.data
  },

  listTemplates: async (stage?: string): Promise<MessageTemplate[]> => {
    const response = await api.get<MessageTemplate[]>('/transfer/templates/', {
      params: stage ? { stage } : undefined,
    })
    return response.data
  },
}

// Submissions API
export const submissionsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<SubmissionListResponse> => {
    const response = await api.get<SubmissionListResponse>('/submissions/', { params })
    return response.data
  },

  listMy: async (params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<SubmissionListResponse> => {
    const response = await api.get<SubmissionListResponse>('/submissions/my', { params })
    return response.data
  },

  get: async (id: string): Promise<SubmissionDetail> => {
    const response = await api.get<SubmissionDetail>(`/submissions/${id}`)
    return response.data
  },

  create: async (data: CreateSubmissionRequest): Promise<Submission> => {
    const response = await api.post<Submission>('/submissions/', data)
    return response.data
  },

  update: async (id: string, data: UpdateSubmissionRequest): Promise<Submission> => {
    const response = await api.patch<Submission>(`/submissions/${id}`, data)
    return response.data
  },

  submit: async (id: string): Promise<Submission> => {
    const response = await api.post<Submission>(`/submissions/${id}/submit`)
    return response.data
  },

  review: async (id: string, data: SubmissionReviewRequest): Promise<Submission> => {
    const response = await api.patch<Submission>(`/submissions/${id}/review`, data)
    return response.data
  },

  analyze: async (id: string): Promise<SubmissionScore> => {
    const response = await api.post<SubmissionScore>(`/submissions/${id}/analyze`)
    return response.data
  },

  convert: async (id: string): Promise<Paper> => {
    const response = await api.post<Paper>(`/submissions/${id}/convert`)
    return response.data
  },

  uploadAttachment: async (
    submissionId: string,
    file: File,
    attachmentType: string
  ): Promise<SubmissionAttachment> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('attachment_type', attachmentType)
    const response = await api.post<SubmissionAttachment>(
      `/submissions/${submissionId}/attachments`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },
}

// Badges API
export const badgesApi = {
  list: async (): Promise<BadgeListResponse> => {
    const response = await api.get<BadgeListResponse>('/badges/')
    return response.data
  },

  myBadges: async (): Promise<UserBadgeListResponse> => {
    const response = await api.get<UserBadgeListResponse>('/badges/me')
    return response.data
  },

  myStats: async (): Promise<UserStats> => {
    const response = await api.get<UserStats>('/badges/me/stats')
    return response.data
  },

  checkBadges: async (): Promise<UserBadgeListResponse> => {
    const response = await api.post<UserBadgeListResponse>('/badges/me/check')
    return response.data
  },
}

// Knowledge API
export const knowledgeApi = {
  listPersonal: async (): Promise<KnowledgeSourceListResponse> => {
    const response = await api.get<KnowledgeSourceListResponse>('/knowledge/personal')
    return response.data
  },

  createPersonal: async (data: CreateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.post<KnowledgeSource>('/knowledge/personal', data)
    return response.data
  },

  updatePersonal: async (id: string, data: UpdateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.patch<KnowledgeSource>(`/knowledge/personal/${id}`, data)
    return response.data
  },

  deletePersonal: async (id: string): Promise<void> => {
    await api.delete(`/knowledge/personal/${id}`)
  },

  listOrganization: async (): Promise<KnowledgeSourceListResponse> => {
    const response = await api.get<KnowledgeSourceListResponse>('/knowledge/organization')
    return response.data
  },

  createOrganization: async (data: CreateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.post<KnowledgeSource>('/knowledge/organization', data)
    return response.data
  },

  updateOrganization: async (id: string, data: UpdateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.patch<KnowledgeSource>(`/knowledge/organization/${id}`, data)
    return response.data
  },

  deleteOrganization: async (id: string): Promise<void> => {
    await api.delete(`/knowledge/organization/${id}`)
  },
}

// Model Settings API
export const modelSettingsApi = {
  listModels: async (): Promise<ModelConfigurationListResponse> => {
    const response = await api.get<ModelConfigurationListResponse>('/settings/models')
    return response.data
  },

  createModel: async (data: CreateModelConfigurationRequest): Promise<ModelConfiguration> => {
    const response = await api.post<ModelConfiguration>('/settings/models', data)
    return response.data
  },

  updateModel: async (id: string, data: UpdateModelConfigurationRequest): Promise<ModelConfiguration> => {
    const response = await api.patch<ModelConfiguration>(`/settings/models/${id}`, data)
    return response.data
  },

  deleteModel: async (id: string): Promise<void> => {
    await api.delete(`/settings/models/${id}`)
  },

  getUsage: async (days?: number): Promise<UsageAggregation> => {
    const response = await api.get<UsageAggregation>('/settings/models/usage', {
      params: days ? { days } : undefined,
    })
    return response.data
  },
}

// Developer API
import type {
  APIKeyCreated,
  APIKeyListResponse,
  CreateAPIKeyRequest,
  Webhook,
  WebhookListResponse,
  CreateWebhookRequest,
  UpdateWebhookRequest,
  WebhookTestResult,
  RepositorySource,
  RepositorySourceListResponse,
  CreateRepositorySourceRequest,
  UpdateRepositorySourceRequest,
  RepositorySyncTriggerResponse,
  RetentionPolicy,
  RetentionPolicyListResponse,
  CreateRetentionPolicyRequest,
  UpdateRetentionPolicyRequest,
  ApplyRetentionRequest,
  ApplyRetentionResponse,
  RetentionLogListResponse,
  AuditLogSummary,
  AuditLogListResponse,
  SOC2StatusResponse,
  SOC2EvidenceResponse,
  DataProcessingInfo,
} from '@/types'

export const developerApi = {
  // API Keys
  listApiKeys: async (): Promise<APIKeyListResponse> => {
    const response = await api.get<APIKeyListResponse>('/developer/api-keys/')
    return response.data
  },

  createApiKey: async (data: CreateAPIKeyRequest): Promise<APIKeyCreated> => {
    const response = await api.post<APIKeyCreated>('/developer/api-keys/', data)
    return response.data
  },

  revokeApiKey: async (id: string): Promise<void> => {
    await api.delete(`/developer/api-keys/${id}/`)
  },

  // Webhooks
  listWebhooks: async (): Promise<WebhookListResponse> => {
    const response = await api.get<WebhookListResponse>('/developer/webhooks/')
    return response.data
  },

  createWebhook: async (data: CreateWebhookRequest): Promise<Webhook> => {
    const response = await api.post<Webhook>('/developer/webhooks/', data)
    return response.data
  },

  updateWebhook: async (id: string, data: UpdateWebhookRequest): Promise<Webhook> => {
    const response = await api.patch<Webhook>(`/developer/webhooks/${id}/`, data)
    return response.data
  },

  testWebhook: async (id: string): Promise<WebhookTestResult> => {
    const response = await api.post<WebhookTestResult>(`/developer/webhooks/${id}/test/`)
    return response.data
  },

  deleteWebhook: async (id: string): Promise<void> => {
    await api.delete(`/developer/webhooks/${id}/`)
  },

  // Repository Sources
  listRepositories: async (): Promise<RepositorySourceListResponse> => {
    const response = await api.get<RepositorySourceListResponse>('/developer/repositories/')
    return response.data
  },

  getRepository: async (id: string): Promise<RepositorySource> => {
    const response = await api.get<RepositorySource>(`/developer/repositories/${id}/`)
    return response.data
  },

  createRepository: async (data: CreateRepositorySourceRequest): Promise<RepositorySource> => {
    const response = await api.post<RepositorySource>('/developer/repositories/', data)
    return response.data
  },

  updateRepository: async (id: string, data: UpdateRepositorySourceRequest): Promise<RepositorySource> => {
    const response = await api.patch<RepositorySource>(`/developer/repositories/${id}/`, data)
    return response.data
  },

  syncRepository: async (id: string): Promise<RepositorySyncTriggerResponse> => {
    const response = await api.post<RepositorySyncTriggerResponse>(`/developer/repositories/${id}/sync/`)
    return response.data
  },

  deleteRepository: async (id: string): Promise<void> => {
    await api.delete(`/developer/repositories/${id}/`)
  },
}

// Compliance API
export const complianceApi = {
  // Audit Logs
  searchAuditLogs: async (params?: {
    page?: number
    page_size?: number
    action?: string
    user_id?: string
    resource_type?: string
    start_date?: string
    end_date?: string
  }): Promise<AuditLogListResponse> => {
    const response = await api.get<AuditLogListResponse>('/compliance/audit-logs', { params })
    return response.data
  },

  exportAuditLogs: async (params?: {
    start_date?: string
    end_date?: string
    actions?: string
  }): Promise<Blob> => {
    const response = await api.get('/compliance/audit-logs/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  getAuditLogSummary: async (params?: {
    start_date?: string
    end_date?: string
  }): Promise<AuditLogSummary> => {
    const response = await api.get<AuditLogSummary>('/compliance/audit-logs/summary', { params })
    return response.data
  },

  // Retention Policies
  listRetentionPolicies: async (): Promise<RetentionPolicyListResponse> => {
    const response = await api.get<RetentionPolicyListResponse>('/compliance/retention')
    return response.data
  },

  createRetentionPolicy: async (data: CreateRetentionPolicyRequest): Promise<RetentionPolicy> => {
    const response = await api.post<RetentionPolicy>('/compliance/retention', data)
    return response.data
  },

  updateRetentionPolicy: async (
    policyId: string,
    data: UpdateRetentionPolicyRequest
  ): Promise<RetentionPolicy> => {
    const response = await api.patch<RetentionPolicy>(`/compliance/retention/${policyId}`, data)
    return response.data
  },

  deleteRetentionPolicy: async (policyId: string): Promise<void> => {
    await api.delete(`/compliance/retention/${policyId}`)
  },

  applyRetentionPolicies: async (data: ApplyRetentionRequest): Promise<ApplyRetentionResponse> => {
    const response = await api.post<ApplyRetentionResponse>('/compliance/retention/apply', data)
    return response.data
  },

  listRetentionLogs: async (params?: {
    page?: number
    page_size?: number
  }): Promise<RetentionLogListResponse> => {
    const response = await api.get<RetentionLogListResponse>('/compliance/retention/logs', { params })
    return response.data
  },

  // SOC2
  getSOC2Status: async (): Promise<SOC2StatusResponse> => {
    const response = await api.get<SOC2StatusResponse>('/compliance/soc2/status')
    return response.data
  },

  getSOC2Evidence: async (controlId: string): Promise<SOC2EvidenceResponse> => {
    const response = await api.get<SOC2EvidenceResponse>(`/compliance/soc2/evidence/${controlId}`)
    return response.data
  },

  exportSOC2Report: async (includeEvidence?: boolean): Promise<{ report: SOC2StatusResponse; generated_at: string; organization_id: string }> => {
    const response = await api.post('/compliance/soc2/export', null, {
      params: { include_evidence: includeEvidence ?? true },
    })
    return response.data
  },

  // Data Processing
  getDataProcessingInfo: async (): Promise<DataProcessingInfo> => {
    const response = await api.get<DataProcessingInfo>('/compliance/data-processing')
    return response.data
  },
}

// Notifications API
export const notificationsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    unread_only?: boolean
  }): Promise<NotificationListResponse> => {
    const response = await api.get<NotificationListResponse>('/notifications', { params })
    return response.data
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get<{ unread_count: number }>('/notifications/unread-count')
    return response.data
  },

  markAsRead: async (notificationIds: string[]): Promise<{ updated: number }> => {
    const response = await api.post<{ updated: number }>('/notifications/mark-read', {
      notification_ids: notificationIds,
    })
    return response.data
  },

  markAllAsRead: async (): Promise<{ updated: number }> => {
    const response = await api.post<{ updated: number }>('/notifications/mark-all-read')
    return response.data
  },
}

// =============================================================================
// Trend Radar API
// =============================================================================

export const trendsApi = {
  list: async (params?: { include_inactive?: boolean }): Promise<TrendTopicListResponse> => {
    const response = await api.get<TrendTopicListResponse>('/trends/', { params })
    return response.data
  },

  get: async (id: string): Promise<TrendTopic> => {
    const response = await api.get<TrendTopic>(`/trends/${id}`)
    return response.data
  },

  create: async (data: { name: string; description: string; color?: string }): Promise<TrendTopic> => {
    const response = await api.post<TrendTopic>('/trends/', data)
    return response.data
  },

  update: async (id: string, data: { name?: string; description?: string; color?: string; is_active?: boolean }): Promise<TrendTopic> => {
    const response = await api.patch<TrendTopic>(`/trends/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/trends/${id}`)
  },

  analyze: async (id: string, params?: { min_similarity?: number; max_papers?: number }): Promise<TrendSnapshot> => {
    const response = await api.post<TrendSnapshot>(`/trends/${id}/analyze`, null, { params })
    return response.data
  },

  getDashboard: async (id: string): Promise<TrendDashboard> => {
    const response = await api.get<TrendDashboard>(`/trends/${id}/dashboard`)
    return response.data
  },

  getPapers: async (id: string, params?: { page?: number; page_size?: number }): Promise<TrendPaperListResponse> => {
    const response = await api.get<TrendPaperListResponse>(`/trends/${id}/papers`, { params })
    return response.data
  },
}

// Discovery API
export const discoveryApi = {
  listProfiles: async (): Promise<DiscoveryProfileListResponse> => {
    const response = await api.get<DiscoveryProfileListResponse>('/discovery/profiles/')
    return response.data
  },

  triggerRun: async (savedSearchId: string): Promise<DiscoveryTriggerResponse> => {
    const response = await api.post<DiscoveryTriggerResponse>(`/discovery/${savedSearchId}/run/`)
    return response.data
  },

  listRuns: async (savedSearchId: string, params?: { page?: number; page_size?: number }): Promise<DiscoveryRunListResponse> => {
    const response = await api.get<DiscoveryRunListResponse>(`/discovery/${savedSearchId}/runs/`, { params })
    return response.data
  },

  getRun: async (runId: string): Promise<DiscoveryRunResponse> => {
    const response = await api.get<DiscoveryRunResponse>(`/discovery/runs/${runId}`)
    return response.data
  },
}
