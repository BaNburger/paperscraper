import type {
  KnowledgeSource,
  KnowledgeSourceListResponse,
  CreateKnowledgeSourceRequest,
  UpdateKnowledgeSourceRequest,
} from '@/types/domains'

import { api } from '@/api/http/client'

export const knowledgeApi = {
  listPersonal: async (): Promise<KnowledgeSourceListResponse> => {
    const response = await api.get<KnowledgeSourceListResponse>('/knowledge/personal')
    return response.data
  },

  createPersonal: async (data: CreateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.post<KnowledgeSource>('/knowledge/personal', data)
    return response.data
  },

  updatePersonal: async (id: string, data: UpdateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.patch<KnowledgeSource>(`/knowledge/personal/${id}`, data)
    return response.data
  },

  deletePersonal: async (id: string): Promise<void> => {
    await api.delete(`/knowledge/personal/${id}`)
  },

  listOrganization: async (): Promise<KnowledgeSourceListResponse> => {
    const response = await api.get<KnowledgeSourceListResponse>('/knowledge/organization')
    return response.data
  },

  createOrganization: async (data: CreateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.post<KnowledgeSource>('/knowledge/organization', data)
    return response.data
  },

  updateOrganization: async (id: string, data: UpdateKnowledgeSourceRequest): Promise<KnowledgeSource> => {
    const response = await api.patch<KnowledgeSource>(`/knowledge/organization/${id}`, data)
    return response.data
  },

  deleteOrganization: async (id: string): Promise<void> => {
    await api.delete(`/knowledge/organization/${id}`)
  },
}
