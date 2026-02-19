import { api } from '@/api/http/client'
import type { TrendTopicListResponse, TrendTopic, TrendSnapshot, TrendDashboard, TrendPaperListResponse } from '@/types/domains'

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

  update: async (
    id: string,
    data: { name?: string; description?: string; color?: string; is_active?: boolean }
  ): Promise<TrendTopic> => {
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
