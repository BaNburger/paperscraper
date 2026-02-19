import { api } from '@/api/http/client'
import type {
  ModelConfiguration,
  ModelConfigurationListResponse,
  CreateModelConfigurationRequest,
  UpdateModelConfigurationRequest,
  UsageAggregation,
} from '@/types/domains'

export const modelSettingsApi = {
  listModels: async (): Promise<ModelConfigurationListResponse> => {
    const response = await api.get<ModelConfigurationListResponse>('/settings/models')
    return response.data
  },

  createModel: async (data: CreateModelConfigurationRequest): Promise<ModelConfiguration> => {
    const response = await api.post<ModelConfiguration>('/settings/models', data)
    return response.data
  },

  updateModel: async (id: string, data: UpdateModelConfigurationRequest): Promise<ModelConfiguration> => {
    const response = await api.patch<ModelConfiguration>(`/settings/models/${id}`, data)
    return response.data
  },

  deleteModel: async (id: string): Promise<void> => {
    await api.delete(`/settings/models/${id}`)
  },

  getUsage: async (days?: number): Promise<UsageAggregation> => {
    const response = await api.get<UsageAggregation>('/settings/models/usage', {
      params: days ? { days } : undefined,
    })
    return response.data
  },
}
