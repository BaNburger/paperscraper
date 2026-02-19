import type {
  Project,
  ProjectListResponse,
  ResearchCluster,
  ClusterPaper,
  ClusterDetail,
  InstitutionSearchResult,
  AuthorSearchResult,
  CreateProject,
  SyncResponse,
} from '@/types/core'

import { api } from '@/api/http/client'

export const projectsApi = {
  searchInstitutions: async (query: string): Promise<InstitutionSearchResult[]> => {
    const response = await api.get<InstitutionSearchResult[]>('/projects/search/institutions', {
      params: { query },
    })
    return response.data
  },

  searchAuthors: async (query: string): Promise<AuthorSearchResult[]> => {
    const response = await api.get<AuthorSearchResult[]>('/projects/search/authors', {
      params: { query },
    })
    return response.data
  },

  list: async (params?: { page?: number; page_size?: number; search?: string }): Promise<ProjectListResponse> => {
    const response = await api.get<ProjectListResponse>('/projects/', { params })
    return response.data
  },

  get: async (id: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${id}`)
    return response.data
  },

  create: async (data: CreateProject): Promise<Project> => {
    const response = await api.post<Project>('/projects/', data)
    return response.data
  },

  update: async (
    id: string,
    data: { name?: string; description?: string }
  ): Promise<Project> => {
    const response = await api.patch<Project>(`/projects/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`)
  },

  sync: async (id: string): Promise<SyncResponse> => {
    const response = await api.post<SyncResponse>(`/projects/${id}/sync`)
    return response.data
  },

  listClusters: async (id: string): Promise<ResearchCluster[]> => {
    const response = await api.get<ResearchCluster[]>(`/projects/${id}/clusters`)
    return response.data
  },

  getCluster: async (projectId: string, clusterId: string): Promise<ClusterDetail> => {
    const response = await api.get<ClusterDetail>(
      `/projects/${projectId}/clusters/${clusterId}`
    )
    return response.data
  },

  updateCluster: async (
    projectId: string,
    clusterId: string,
    data: { label: string }
  ): Promise<void> => {
    await api.patch(`/projects/${projectId}/clusters/${clusterId}`, data)
  },

  listPapers: async (id: string): Promise<ClusterPaper[]> => {
    const response = await api.get<ClusterPaper[]>(`/projects/${id}/papers`)
    return response.data
  },
}
