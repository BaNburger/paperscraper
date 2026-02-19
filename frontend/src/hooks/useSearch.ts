import { useQuery, useMutation } from '@tanstack/react-query'
import { searchApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import type { SearchRequest } from '@/types'

export function useSearch(params: SearchRequest, enabled = true) {
  return useQuery({
    queryKey: queryKeys.search.query(params),
    queryFn: () => searchApi.search(params),
    enabled: enabled && !!params.query,
  })
}

export function useSearchMutation() {
  return useMutation({
    mutationFn: (params: SearchRequest) => searchApi.search(params),
  })
}

export function useSimilarPapers(paperId: string, limit = 5) {
  return useQuery({
    queryKey: queryKeys.papers.similar(paperId, limit),
    queryFn: () => searchApi.findSimilar(paperId, { limit }),
    enabled: !!paperId,
  })
}

export function useEmbeddingStats() {
  return useQuery({
    queryKey: queryKeys.search.embeddingStats(),
    queryFn: () => searchApi.getEmbeddingStats(),
  })
}
