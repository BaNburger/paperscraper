import type {
  Group,
  GroupDetail,
  GroupListResponse,
  CreateGroupRequest,
  UpdateGroupRequest,
  SuggestMembersResponse,
} from '@/types/domains'

import { api } from '@/api/http/client'

export const groupsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    type?: string
  }): Promise<GroupListResponse> => {
    const response = await api.get<GroupListResponse>('/groups/', { params })
    return response.data
  },

  get: async (id: string): Promise<GroupDetail> => {
    const response = await api.get<GroupDetail>(`/groups/${id}`)
    return response.data
  },

  create: async (data: CreateGroupRequest): Promise<Group> => {
    const response = await api.post<Group>('/groups/', data)
    return response.data
  },

  update: async (id: string, data: UpdateGroupRequest): Promise<Group> => {
    const response = await api.patch<Group>(`/groups/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/groups/${id}`)
  },

  addMembers: async (groupId: string, researcherIds: string[]): Promise<{ added: number }> => {
    const response = await api.post<{ added: number }>(`/groups/${groupId}/members`, {
      researcher_ids: researcherIds,
    })
    return response.data
  },

  removeMember: async (groupId: string, researcherId: string): Promise<void> => {
    await api.delete(`/groups/${groupId}/members/${researcherId}`)
  },

  suggestMembers: async (keywords: string[], targetSize?: number): Promise<SuggestMembersResponse> => {
    const response = await api.post<SuggestMembersResponse>('/groups/suggest-members', {
      keywords,
      target_size: targetSize || 10,
    })
    return response.data
  },

  exportCsv: async (groupId: string): Promise<Blob> => {
    const response = await api.get(`/groups/${groupId}/export`, {
      responseType: 'blob',
    })
    return response.data
  },
}
