import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { papersApi, scoringApi } from '@/lib/api'

interface QueryControlOptions {
  enabled?: boolean
  staleTime?: number
}

export function usePapers(
  params: { page?: number; page_size?: number; search?: string },
  options?: QueryControlOptions
) {
  return useQuery({
    queryKey: ['papers', params],
    queryFn: () => papersApi.list(params),
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime,
  })
}

export function usePaper(id: string) {
  return useQuery({
    queryKey: ['paper', id],
    queryFn: () => papersApi.get(id),
    enabled: !!id,
  })
}

export function usePaperScore(paperId: string) {
  return useQuery({
    queryKey: ['paperScore', paperId],
    queryFn: () => scoringApi.getLatestScore(paperId),
    enabled: !!paperId,
  })
}

export function useDeletePaper() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => papersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useIngestByDoi() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (doi: string) => papersApi.ingestByDoi(doi),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useIngestFromOpenAlex() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params: { query: string; max_results?: number }) =>
      papersApi.ingestFromOpenAlex(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useIngestFromPubMed() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params: { query: string; max_results?: number }) =>
      papersApi.ingestFromPubMed(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useIngestFromArxiv() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params: { query: string; max_results?: number; category?: string }) =>
      papersApi.ingestFromArxiv(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useUploadPdf() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => papersApi.uploadPdf(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useScorePaper() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (paperId: string) => scoringApi.scorePaper(paperId),
    onSuccess: (_, paperId) => {
      queryClient.invalidateQueries({ queryKey: ['paperScore', paperId] })
      queryClient.invalidateQueries({ queryKey: ['paper', paperId] })
    },
  })
}

export function useGeneratePitch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (paperId: string) => papersApi.generatePitch(paperId),
    onSuccess: (_, paperId) => {
      queryClient.invalidateQueries({ queryKey: ['paper', paperId] })
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useGenerateSimplifiedAbstract() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (paperId: string) => papersApi.generateSimplifiedAbstract(paperId),
    onSuccess: (_, paperId) => {
      queryClient.invalidateQueries({ queryKey: ['paper', paperId] })
    },
  })
}

export function useRelatedPatents(paperId: string) {
  return useQuery({
    queryKey: ['relatedPatents', paperId],
    queryFn: () => papersApi.getRelatedPatents(paperId),
    enabled: !!paperId,
    staleTime: 5 * 60 * 1000, // 5 minutes - patent data doesn't change often
    retry: false, // Don't retry if EPO is not configured
  })
}

export function useCitationGraph(paperId: string) {
  return useQuery({
    queryKey: ['citationGraph', paperId],
    queryFn: () => papersApi.getCitationGraph(paperId),
    enabled: !!paperId,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useIngestFromSemanticScholar() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params: { query: string; max_results?: number }) =>
      papersApi.ingestFromSemanticScholar(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}
