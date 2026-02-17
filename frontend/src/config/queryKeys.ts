/**
 * Central typed React Query key registry.
 *
 * Keep all key tuples here so invalidation/fetch keys stay in sync.
 */
export const queryKeys = {
  projects: {
    list: () => ['projects'] as const,
    detail: (id: string) => ['project', id] as const,
    clusters: (id: string) => ['projectClusters', id] as const,
    cluster: (projectId: string, clusterId: string) =>
      ['projectCluster', projectId, clusterId] as const,
    institutions: (query: string) => ['institutionSearch', query] as const,
    authors: (query: string) => ['authorSearch', query] as const,
  },
}
