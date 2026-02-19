import type { ClassificationResponse } from '@/types/core'

import { api } from '@/api/http/client'

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
