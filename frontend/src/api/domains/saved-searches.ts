import type {
  SavedSearch,
  SavedSearchListResponse,
  CreateSavedSearchRequest,
  UpdateSavedSearchRequest,
  SearchResponse,
} from '@/types/core'

import { api } from '@/api/http/client'

export const savedSearchesApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    include_public?: boolean
  }): Promise<SavedSearchListResponse> => {
    const response = await api.get<SavedSearchListResponse>('/saved-searches', { params })
    return response.data
  },

  get: async (id: string): Promise<SavedSearch> => {
    const response = await api.get<SavedSearch>(`/saved-searches/${id}`)
    return response.data
  },

  getByShareToken: async (shareToken: string): Promise<SavedSearch> => {
    const response = await api.get<SavedSearch>(`/saved-searches/shared/${shareToken}`)
    return response.data
  },

  create: async (data: CreateSavedSearchRequest): Promise<SavedSearch> => {
    const response = await api.post<SavedSearch>('/saved-searches', data)
    return response.data
  },

  update: async (id: string, data: UpdateSavedSearchRequest): Promise<SavedSearch> => {
    const response = await api.patch<SavedSearch>(`/saved-searches/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/saved-searches/${id}`)
  },

  generateShareLink: async (id: string): Promise<{ share_token: string; share_url: string }> => {
    const response = await api.post<{ share_token: string; share_url: string }>(
      `/saved-searches/${id}/share`
    )
    return response.data
  },

  revokeShareLink: async (id: string): Promise<void> => {
    await api.delete(`/saved-searches/${id}/share`)
  },

  run: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>(`/saved-searches/${id}/run`, null, { params })
    return response.data
  },
}
