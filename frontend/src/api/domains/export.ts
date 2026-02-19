import type { ExportFormat } from '@/types/core'

import { api } from '@/api/http/client'
import { triggerBrowserDownload } from '@/lib/browser'

export const exportApi = {
  exportCsv: async (params?: {
    paper_ids?: string[]
    include_scores?: boolean
    include_authors?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/csv', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportBibtex: async (params?: {
    paper_ids?: string[]
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/bibtex', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportPdf: async (params?: {
    paper_ids?: string[]
    include_scores?: boolean
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/pdf', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportRis: async (params?: {
    paper_ids?: string[]
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/ris', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  exportCslJson: async (params?: {
    paper_ids?: string[]
    include_abstract?: boolean
  }): Promise<Blob> => {
    const response = await api.get('/export/csljson', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  batchExport: async (
    paperIds: string[],
    format: ExportFormat,
    options?: {
      include_scores?: boolean
      include_authors?: boolean
    }
  ): Promise<Blob> => {
    const response = await api.post(
      '/export/batch',
      { paper_ids: paperIds },
      {
        params: { format, ...options },
        responseType: 'blob',
      }
    )
    return response.data
  },

  downloadFile: (blob: Blob, filename: string): void => {
    triggerBrowserDownload(blob, filename)
  },
}
