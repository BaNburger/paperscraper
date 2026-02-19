import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { integrationsApi, libraryApi, papersApi, scoringApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import { invalidateMany, optimisticDeleteById, rollbackOptimisticSnapshots } from '@/lib/query'
import { useIngestionRunPoller } from './useIngestionRuns'

interface QueryControlOptions {
  enabled?: boolean
  staleTime?: number
}

export function usePapers(
  params: { page?: number; page_size?: number; search?: string },
  options?: QueryControlOptions
) {
  return useQuery({
    queryKey: queryKeys.papers.list(params),
    queryFn: () => papersApi.list(params),
    placeholderData: keepPreviousData,
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime,
  })
}

export function usePaper(id: string) {
  return useQuery({
    queryKey: queryKeys.papers.detail(id),
    queryFn: () => papersApi.get(id),
    enabled: !!id,
  })
}

export function usePaperScore(paperId: string) {
  return useQuery({
    queryKey: queryKeys.papers.score(paperId),
    queryFn: () => scoringApi.getLatestScore(paperId),
    enabled: !!paperId,
  })
}

export function useDeletePaper() {
  const queryClient = useQueryClient()
  const papersListKey = queryKeys.papers.listRoot()

  return useMutation({
    mutationFn: (id: string) => papersApi.delete(id),
    onMutate: async (deletedId) => {
      const snapshots = await optimisticDeleteById<{ id: string }>(
        queryClient,
        papersListKey,
        deletedId,
      )
      return { snapshots }
    },
    onError: (_err, _id, context) => {
      rollbackOptimisticSnapshots(queryClient, context?.snapshots)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: papersListKey })
    },
  })
}

export function useIngestByDoi() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (doi: string) => papersApi.ingestByDoi(doi),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.listRoot() })
    },
  })
}

export function useIngestFromOpenAlex() {
  const queryClient = useQueryClient()
  const { waitForRun } = useIngestionRunPoller()

  return useMutation({
    mutationFn: async (params: { query: string; max_results?: number }) => {
      const queued = await papersApi.ingestFromOpenAlex(params)
      return waitForRun(queued.ingest_run_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.listRoot() })
    },
  })
}

export function useIngestFromPubMed() {
  const queryClient = useQueryClient()
  const { waitForRun } = useIngestionRunPoller()

  return useMutation({
    mutationFn: async (params: { query: string; max_results?: number }) => {
      const queued = await papersApi.ingestFromPubMed(params)
      return waitForRun(queued.ingest_run_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.listRoot() })
    },
  })
}

export function useIngestFromArxiv() {
  const queryClient = useQueryClient()
  const { waitForRun } = useIngestionRunPoller()

  return useMutation({
    mutationFn: async (params: { query: string; max_results?: number; category?: string }) => {
      const queued = await papersApi.ingestFromArxiv(params)
      return waitForRun(queued.ingest_run_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.listRoot() })
    },
  })
}

export function useUploadPdf() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => papersApi.uploadPdf(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.listRoot() })
    },
  })
}

export function useScorePaper() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (paperId: string) => scoringApi.scorePaper(paperId),
    onSuccess: (_, paperId) => {
      invalidateMany(queryClient, [
        queryKeys.papers.score(paperId),
        queryKeys.papers.detail(paperId),
      ])
    },
  })
}

export function useGeneratePitch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (paperId: string) => papersApi.generatePitch(paperId),
    onSuccess: (_, paperId) => {
      invalidateMany(queryClient, [
        queryKeys.papers.detail(paperId),
        queryKeys.papers.listRoot(),
      ])
    },
  })
}

export function useGenerateSimplifiedAbstract() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (paperId: string) => papersApi.generateSimplifiedAbstract(paperId),
    onSuccess: (_, paperId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.detail(paperId) })
    },
  })
}

export function useRelatedPatents(paperId: string) {
  return useQuery({
    queryKey: queryKeys.papers.relatedPatents(paperId),
    queryFn: () => papersApi.getRelatedPatents(paperId),
    enabled: !!paperId,
    staleTime: 5 * 60 * 1000, // 5 minutes - patent data doesn't change often
    retry: false, // Don't retry if EPO is not configured
  })
}

export function useCitationGraph(paperId: string) {
  return useQuery({
    queryKey: queryKeys.papers.citationGraph(paperId),
    queryFn: () => papersApi.getCitationGraph(paperId),
    enabled: !!paperId,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useIngestFromSemanticScholar() {
  const queryClient = useQueryClient()
  const { waitForRun } = useIngestionRunPoller()

  return useMutation({
    mutationFn: async (params: { query: string; max_results?: number }) => {
      const queued = await papersApi.ingestFromSemanticScholar(params)
      return waitForRun(queued.ingest_run_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.listRoot() })
    },
  })
}

// Library V2 hooks
export function useLibraryCollections(enabled = true) {
  return useQuery({
    queryKey: queryKeys.papers.libraryCollections(),
    queryFn: () => libraryApi.listCollections(),
    enabled,
    retry: false,
  })
}

export function useCreateLibraryCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string; parent_id?: string }) =>
      libraryApi.createCollection(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.libraryCollections() })
    },
  })
}

export function usePaperReader(paperId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.papers.reader(paperId),
    queryFn: async () => {
      try {
        return await libraryApi.getReader(paperId)
      } catch (error: unknown) {
        // Library feature flag can disable endpoint and return 404.
        const status = (error as { response?: { status?: number } })?.response?.status
        if (status === 404) {
          return null
        }
        throw error
      }
    },
    enabled: enabled && !!paperId,
    retry: false,
  })
}

export function useHydratePaperFullText() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (paperId: string) => libraryApi.hydrateFullText(paperId),
    onSuccess: (_, paperId) => {
      invalidateMany(queryClient, [
        queryKeys.papers.reader(paperId),
        queryKeys.papers.highlights(paperId),
        queryKeys.papers.detail(paperId),
      ])
    },
  })
}

export function usePaperHighlights(
  paperId: string,
  options?: { includeInactive?: boolean; enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.papers.highlights(paperId, options?.includeInactive ?? false),
    queryFn: async () => {
      try {
        return await libraryApi.listHighlights(paperId, options?.includeInactive ?? false)
      } catch (error: unknown) {
        const status = (error as { response?: { status?: number } })?.response?.status
        if (status === 404) {
          return { items: [], total: 0 }
        }
        throw error
      }
    },
    enabled: (options?.enabled ?? true) && !!paperId,
    retry: false,
  })
}

export function useGeneratePaperHighlights() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ paperId, targetCount }: { paperId: string; targetCount?: number }) =>
      libraryApi.generateHighlights(paperId, targetCount ?? 8),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.highlights(vars.paperId) })
    },
  })
}

export function useCreatePaperHighlight() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: {
      paperId: string
      chunk_id?: string
      chunk_ref?: string
      quote: string
      insight_summary: string
      confidence?: number
    }) => libraryApi.createHighlight(params.paperId, params),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.highlights(vars.paperId) })
    },
  })
}

export function useDeletePaperHighlight() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ paperId, highlightId }: { paperId: string; highlightId: string }) =>
      libraryApi.deleteHighlight(paperId, highlightId),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.highlights(vars.paperId) })
    },
  })
}

export function useLibraryTags(enabled = true) {
  return useQuery({
    queryKey: queryKeys.papers.libraryTags(),
    queryFn: () => libraryApi.listTags(),
    enabled,
    retry: false,
  })
}

export function useAddPaperTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ paperId, tag }: { paperId: string; tag: string }) =>
      libraryApi.addPaperTag(paperId, tag),
    onSuccess: (_, vars) => {
      invalidateMany(queryClient, [
        queryKeys.papers.libraryTags(),
        queryKeys.papers.detail(vars.paperId),
      ])
    },
  })
}

export function useRemovePaperTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ paperId, tag }: { paperId: string; tag: string }) =>
      libraryApi.removePaperTag(paperId, tag),
    onSuccess: (_, vars) => {
      invalidateMany(queryClient, [
        queryKeys.papers.libraryTags(),
        queryKeys.papers.detail(vars.paperId),
      ])
    },
  })
}

// Zotero hooks
export function useZoteroStatus(enabled = true) {
  return useQuery({
    queryKey: queryKeys.papers.zoteroStatus(),
    queryFn: async () => {
      try {
        return await integrationsApi.getZoteroStatus()
      } catch (error: unknown) {
        const status = (error as { response?: { status?: number } })?.response?.status
        if (status === 404) {
          return null
        }
        throw error
      }
    },
    enabled,
    retry: false,
  })
}

export function useConnectZotero() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: {
      user_id: string
      api_key: string
      base_url?: string
      library_type?: 'users' | 'groups'
    }) => integrationsApi.connectZotero(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.zoteroStatus() })
    },
  })
}

export function useZoteroOutboundSync() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (paperIds?: string[]) => integrationsApi.syncZoteroOutbound(paperIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.papers.zoteroStatus() })
    },
  })
}

export function useZoteroInboundSync() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => integrationsApi.syncZoteroInbound(),
    onSuccess: () => {
      invalidateMany(queryClient, [
        queryKeys.papers.zoteroStatus(),
        ['papers', 'list'],
      ])
    },
  })
}

export function useZoteroSyncRun(runId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.papers.zoteroSyncRun(runId),
    queryFn: () => integrationsApi.getZoteroSyncRun(runId),
    enabled: enabled && !!runId,
    retry: false,
  })
}
