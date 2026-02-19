import type { SearchRequest, SearchResponse, SimilarPapersResponse } from '@/types/core'

import { api } from '@/api/http/client'

export const searchApi = {
  search: async (data: SearchRequest): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>('/search/', data)
    return response.data
  },

  findSimilar: async (
    paperId: string,
    params?: { limit?: number }
  ): Promise<SimilarPapersResponse> => {
    const response = await api.get<SimilarPapersResponse>(`/search/similar/${paperId}`, { params })
    return response.data
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
