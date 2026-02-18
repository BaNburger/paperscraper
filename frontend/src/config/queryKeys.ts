/**
 * Central typed React Query key registry.
 *
 * Keep all key tuples here so invalidation/fetch keys stay in sync.
 */
export const queryKeys = {
  auth: {
    me: () => ['auth', 'me'] as const,
    permissions: () => ['auth', 'permissions'] as const,
    roles: () => ['auth', 'roles'] as const,
    organizationUsers: () => ['auth', 'organization-users'] as const,
    pendingInvitations: () => ['auth', 'pending-invitations'] as const,
  },
  papers: {
    list: (params?: { page?: number; page_size?: number; search?: string }) =>
      ['papers', 'list', params ?? {}] as const,
    detail: (id: string) => ['papers', 'detail', id] as const,
    score: (paperId: string) => ['papers', 'score', paperId] as const,
    relatedPatents: (paperId: string) => ['papers', 'related-patents', paperId] as const,
    citationGraph: (paperId: string) => ['papers', 'citation-graph', paperId] as const,
    reader: (paperId: string) => ['papers', 'reader', paperId] as const,
    highlights: (paperId: string, includeInactive = false) =>
      ['papers', 'highlights', paperId, includeInactive] as const,
    libraryCollections: () => ['papers', 'library-collections'] as const,
    libraryTags: () => ['papers', 'library-tags'] as const,
    zoteroStatus: () => ['papers', 'zotero-status'] as const,
    zoteroSyncRun: (runId: string) => ['papers', 'zotero-sync-run', runId] as const,
    similar: (paperId: string, limit: number) => ['papers', 'similar', paperId, limit] as const,
  },
  search: {
    query: (params: object) => ['search', params] as const,
    embeddingStats: () => ['search', 'embedding-stats'] as const,
  },
  projects: {
    list: () => ['projects'] as const,
    detail: (id: string) => ['project', id] as const,
    clusters: (id: string) => ['projectClusters', id] as const,
    cluster: (projectId: string, clusterId: string) =>
      ['projectCluster', projectId, clusterId] as const,
    institutions: (query: string) => ['institutionSearch', query] as const,
    authors: (query: string) => ['authorSearch', query] as const,
  },
  authors: {
    list: (params?: { page?: number; page_size?: number; search?: string }) =>
      ['authors', 'list', params ?? {}] as const,
    profile: (authorId: string) => ['authors', 'profile', authorId] as const,
    detail: (authorId: string) => ['authors', 'detail', authorId] as const,
    contactStats: (authorId: string) => ['authors', 'contact-stats', authorId] as const,
  },
  analytics: {
    dashboard: () => ['analytics', 'dashboard'] as const,
    team: () => ['analytics', 'team'] as const,
    papers: (days: number) => ['analytics', 'papers', days] as const,
    funnel: (params?: object) => ['analytics', 'funnel', params ?? {}] as const,
    benchmarks: () => ['analytics', 'benchmarks'] as const,
  },
  reports: {
    scheduled: (params?: { page?: number; page_size?: number; is_active?: boolean }) =>
      ['reports', 'scheduled', params ?? {}] as const,
    scheduledDetail: (reportId: string) => ['reports', 'scheduled', reportId] as const,
  },
  savedSearches: {
    list: (params?: { page?: number; page_size?: number; include_public?: boolean }) =>
      ['saved-searches', 'list', params ?? {}] as const,
    detail: (id: string) => ['saved-searches', 'detail', id] as const,
    shared: (shareToken: string) => ['saved-searches', 'shared', shareToken] as const,
  },
  alerts: {
    list: (params?: { page?: number; page_size?: number; active_only?: boolean }) =>
      ['alerts', 'list', params ?? {}] as const,
    detail: (id: string) => ['alerts', 'detail', id] as const,
    results: (alertId: string, params?: { page?: number; page_size?: number }) =>
      ['alerts', 'results', alertId, params ?? {}] as const,
  },
  groups: {
    list: (params?: { page?: number; page_size?: number; type?: string }) =>
      ['groups', 'list', params ?? {}] as const,
    detail: (id: string) => ['groups', 'detail', id] as const,
  },
  transfer: {
    conversations: (params?: object) => ['transfer', 'conversations', params ?? {}] as const,
    conversation: (id: string) => ['transfer', 'conversation', id] as const,
    nextSteps: (conversationId: string) => ['transfer', 'next-steps', conversationId] as const,
    templates: (stage?: string) => ['transfer', 'templates', stage ?? 'all'] as const,
  },
  submissions: {
    list: (params?: object) => ['submissions', 'list', params ?? {}] as const,
    myList: (params?: object) => ['submissions', 'my-list', params ?? {}] as const,
    detail: (id: string) => ['submissions', 'detail', id] as const,
  },
  badges: {
    all: () => ['badges', 'all'] as const,
    mine: () => ['badges', 'mine'] as const,
    stats: () => ['badges', 'stats'] as const,
  },
  knowledge: {
    personal: () => ['knowledge', 'personal'] as const,
    organization: () => ['knowledge', 'organization'] as const,
  },
  models: {
    configurations: () => ['models', 'configurations'] as const,
    usage: (days: number) => ['models', 'usage', days] as const,
  },
  developer: {
    apiKeys: () => ['developer', 'api-keys'] as const,
    webhooks: () => ['developer', 'webhooks'] as const,
    repositories: () => ['developer', 'repositories'] as const,
    repository: (id: string) => ['developer', 'repositories', id] as const,
  },
  compliance: {
    auditLogs: (page: number, action?: string) => ['compliance', 'audit-logs', page, action ?? 'all'] as const,
    auditSummary: () => ['compliance', 'audit-logs-summary'] as const,
    retentionPolicies: () => ['compliance', 'retention-policies'] as const,
    retentionLogs: () => ['compliance', 'retention-logs'] as const,
    dataProcessing: () => ['compliance', 'data-processing'] as const,
    soc2Status: () => ['compliance', 'soc2-status'] as const,
  },
  notifications: {
    list: (limit: number) => ['notifications', 'list', limit] as const,
    unreadCount: () => ['notifications', 'unread-count'] as const,
    all: () => ['notifications'] as const,
  },
  trends: {
    list: (includeInactive: boolean) => ['trends', 'list', includeInactive] as const,
    dashboard: (id: string) => ['trends', 'dashboard', id] as const,
    papers: (id: string, page: number, pageSize: number) =>
      ['trends', 'papers', id, page, pageSize] as const,
  },
  discovery: {
    profiles: () => ['discovery', 'profiles'] as const,
    runs: (savedSearchId: string) => ['discovery', 'runs', savedSearchId] as const,
  },
}
