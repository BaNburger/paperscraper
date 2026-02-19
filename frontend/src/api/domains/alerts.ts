import type {
  Alert,
  AlertListResponse,
  AlertResultListResponse,
  CreateAlertRequest,
  UpdateAlertRequest,
} from '@/types/core'

import { api } from '@/api/http/client'

export const alertsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    active_only?: boolean
  }): Promise<AlertListResponse> => {
    const response = await api.get<AlertListResponse>('/alerts', { params })
    return response.data
  },

  get: async (id: string): Promise<Alert> => {
    const response = await api.get<Alert>(`/alerts/${id}`)
    return response.data
  },

  create: async (data: CreateAlertRequest): Promise<Alert> => {
    const response = await api.post<Alert>('/alerts', data)
    return response.data
  },

  update: async (id: string, data: UpdateAlertRequest): Promise<Alert> => {
    const response = await api.patch<Alert>(`/alerts/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/alerts/${id}`)
  },

  getResults: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<AlertResultListResponse> => {
    const response = await api.get<AlertResultListResponse>(`/alerts/${id}/results`, { params })
    return response.data
  },

  test: async (id: string): Promise<{
    success: boolean
    message: string
    papers_found: number
    sample_papers: Array<{ id: string; title: string; journal?: string; publication_date?: string }>
  }> => {
    const response = await api.post(`/alerts/${id}/test`)
    return response.data
  },

  trigger: async (id: string): Promise<void> => {
    await api.post(`/alerts/${id}/trigger`)
  },
}
