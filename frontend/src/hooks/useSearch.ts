import { useQuery, useMutation } from '@tanstack/react-query'
import { searchApi } from '@/lib/api'
import type { SearchRequest } from '@/types'

export function useSearch(params: SearchRequest, enabled = true) {
  return useQuery({
    queryKey: ['search', params],
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
    queryKey: ['similarPapers', paperId, limit],
    queryFn: () => searchApi.findSimilar(paperId, { limit }),
    enabled: !!paperId,
  })
}

export function useEmbeddingStats() {
  return useQuery({
    queryKey: ['embeddingStats'],
    queryFn: () => searchApi.getEmbeddingStats(),
  })
}
