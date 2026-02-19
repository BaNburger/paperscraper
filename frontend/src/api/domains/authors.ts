import type {
  AuthorProfile,
  AuthorDetail,
  AuthorListResponse,
  AuthorContact,
  AuthorContactStats,
  CreateContactRequest,
  EnrichmentResult,
} from '@/types/core'

import { api } from '@/api/http/client'

export const authorsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    search?: string
  }): Promise<AuthorListResponse> => {
    const response = await api.get<AuthorListResponse>('/authors/', { params })
    return response.data
  },

  getProfile: async (authorId: string): Promise<AuthorProfile> => {
    const response = await api.get<AuthorProfile>(`/authors/${authorId}`)
    return response.data
  },

  getDetail: async (authorId: string): Promise<AuthorDetail> => {
    const response = await api.get<AuthorDetail>(`/authors/${authorId}/detail`)
    return response.data
  },

  createContact: async (authorId: string, data: CreateContactRequest): Promise<AuthorContact> => {
    const response = await api.post<AuthorContact>(`/authors/${authorId}/contacts`, data)
    return response.data
  },

  updateContact: async (
    authorId: string,
    contactId: string,
    data: Partial<CreateContactRequest>
  ): Promise<AuthorContact> => {
    const response = await api.patch<AuthorContact>(`/authors/${authorId}/contacts/${contactId}`, data)
    return response.data
  },

  deleteContact: async (authorId: string, contactId: string): Promise<void> => {
    await api.delete(`/authors/${authorId}/contacts/${contactId}`)
  },

  getContactStats: async (authorId: string): Promise<AuthorContactStats> => {
    const response = await api.get<AuthorContactStats>(`/authors/${authorId}/contacts/stats`)
    return response.data
  },

  enrichAuthor: async (
    authorId: string,
    params?: { source?: string; force_update?: boolean }
  ): Promise<EnrichmentResult> => {
    const response = await api.post<EnrichmentResult>(`/authors/${authorId}/enrich`, params || {})
    return response.data
  },
}
