import type { PaperScore, ScoreResponse } from '@/types/core'

import { api } from '@/api/http/client'

type HttpError = {
  response?: {
    status?: number
  }
}

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
      const httpError = error as HttpError
      if (httpError.response?.status === 404) {
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
