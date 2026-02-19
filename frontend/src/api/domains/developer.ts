import { api } from '@/api/http/client'
import type {
  APIKeyCreated,
  APIKeyListResponse,
  CreateAPIKeyRequest,
  Webhook,
  WebhookListResponse,
  CreateWebhookRequest,
  UpdateWebhookRequest,
  WebhookTestResult,
  RepositorySource,
  RepositorySourceListResponse,
  CreateRepositorySourceRequest,
  UpdateRepositorySourceRequest,
  RepositorySyncTriggerResponse,
} from '@/types/domains'

export const developerApi = {
  listApiKeys: async (): Promise<APIKeyListResponse> => {
    const response = await api.get<APIKeyListResponse>('/developer/api-keys/')
    return response.data
  },

  createApiKey: async (data: CreateAPIKeyRequest): Promise<APIKeyCreated> => {
    const response = await api.post<APIKeyCreated>('/developer/api-keys/', data)
    return response.data
  },

  revokeApiKey: async (id: string): Promise<void> => {
    await api.delete(`/developer/api-keys/${id}/`)
  },

  listWebhooks: async (): Promise<WebhookListResponse> => {
    const response = await api.get<WebhookListResponse>('/developer/webhooks/')
    return response.data
  },

  createWebhook: async (data: CreateWebhookRequest): Promise<Webhook> => {
    const response = await api.post<Webhook>('/developer/webhooks/', data)
    return response.data
  },

  updateWebhook: async (id: string, data: UpdateWebhookRequest): Promise<Webhook> => {
    const response = await api.patch<Webhook>(`/developer/webhooks/${id}/`, data)
    return response.data
  },

  testWebhook: async (id: string): Promise<WebhookTestResult> => {
    const response = await api.post<WebhookTestResult>(`/developer/webhooks/${id}/test/`)
    return response.data
  },

  deleteWebhook: async (id: string): Promise<void> => {
    await api.delete(`/developer/webhooks/${id}/`)
  },

  listRepositories: async (): Promise<RepositorySourceListResponse> => {
    const response = await api.get<RepositorySourceListResponse>('/developer/repositories/')
    return response.data
  },

  getRepository: async (id: string): Promise<RepositorySource> => {
    const response = await api.get<RepositorySource>(`/developer/repositories/${id}/`)
    return response.data
  },

  createRepository: async (data: CreateRepositorySourceRequest): Promise<RepositorySource> => {
    const response = await api.post<RepositorySource>('/developer/repositories/', data)
    return response.data
  },

  updateRepository: async (id: string, data: UpdateRepositorySourceRequest): Promise<RepositorySource> => {
    const response = await api.patch<RepositorySource>(`/developer/repositories/${id}/`, data)
    return response.data
  },

  syncRepository: async (id: string): Promise<RepositorySyncTriggerResponse> => {
    const response = await api.post<RepositorySyncTriggerResponse>(`/developer/repositories/${id}/sync/`)
    return response.data
  },

  deleteRepository: async (id: string): Promise<void> => {
    await api.delete(`/developer/repositories/${id}/`)
  },
}
