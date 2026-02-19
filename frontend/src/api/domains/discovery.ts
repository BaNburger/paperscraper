import { api } from '@/api/http/client'
import type {
  DiscoveryProfileListResponse,
  DiscoveryTriggerResponse,
  DiscoveryRunListResponse,
  DiscoveryRunResponse,
} from '@/types/domains'

export const discoveryApi = {
  listProfiles: async (): Promise<DiscoveryProfileListResponse> => {
    const response = await api.get<DiscoveryProfileListResponse>('/discovery/profiles/')
    return response.data
  },

  triggerRun: async (savedSearchId: string): Promise<DiscoveryTriggerResponse> => {
    const response = await api.post<DiscoveryTriggerResponse>(`/discovery/${savedSearchId}/run/`)
    return response.data
  },

  listRuns: async (
    savedSearchId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<DiscoveryRunListResponse> => {
    const response = await api.get<DiscoveryRunListResponse>(`/discovery/${savedSearchId}/runs/`, { params })
    return response.data
  },

  getRun: async (runId: string): Promise<DiscoveryRunResponse> => {
    const response = await api.get<DiscoveryRunResponse>(`/discovery/runs/${runId}`)
    return response.data
  },
}
