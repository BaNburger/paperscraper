import type { ZoteroConnectionStatus, ZoteroSyncRun } from '@/types/core'

import { api } from '@/api/http/client'

export const integrationsApi = {
  connectZotero: async (data: {
    user_id: string
    api_key: string
    base_url?: string
    library_type?: 'users' | 'groups'
  }): Promise<ZoteroConnectionStatus> => {
    const response = await api.post<ZoteroConnectionStatus>('/integrations/zotero/connect', data)
    return response.data
  },

  getZoteroStatus: async (): Promise<ZoteroConnectionStatus> => {
    const response = await api.get<ZoteroConnectionStatus>('/integrations/zotero/status')
    return response.data
  },

  syncZoteroOutbound: async (paperIds?: string[]): Promise<ZoteroSyncRun> => {
    const response = await api.post<ZoteroSyncRun>('/integrations/zotero/sync/outbound', {
      paper_ids: paperIds && paperIds.length ? paperIds : null,
    })
    return response.data
  },

  syncZoteroInbound: async (): Promise<ZoteroSyncRun> => {
    const response = await api.post<ZoteroSyncRun>('/integrations/zotero/sync/inbound')
    return response.data
  },

  getZoteroSyncRun: async (runId: string): Promise<ZoteroSyncRun> => {
    const response = await api.get<ZoteroSyncRun>(`/integrations/zotero/sync-runs/${runId}`)
    return response.data
  },
}
