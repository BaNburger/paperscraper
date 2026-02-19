import type {
  Paper,
  PaperDetail,
  PaperListResponse,
  IngestionJobResponse,
  IngestionRunResponse,
} from '@/types/core'
import type { RelatedPatentsResponse, CitationGraphResponse } from '@/types/domains'

import { api } from '@/api/http/client'

export const papersApi = {
  list: async (params: {
    page?: number
    page_size?: number
    search?: string
  }): Promise<PaperListResponse> => {
    const response = await api.get<PaperListResponse>('/papers/', { params })
    return response.data
  },

  get: async (id: string): Promise<PaperDetail> => {
    const response = await api.get<PaperDetail>(`/papers/${id}`)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/papers/${id}`)
  },

  ingestByDoi: async (doi: string): Promise<Paper> => {
    const response = await api.post<Paper>('/papers/ingest/doi', { doi })
    return response.data
  },

  ingestFromOpenAlex: async (params: {
    query: string
    max_results?: number
    filters?: Record<string, string>
  }): Promise<IngestionJobResponse> => {
    const response = await api.post<IngestionJobResponse>('/ingestion/sources/openalex/runs', params)
    return response.data
  },

  ingestFromPubMed: async (params: {
    query: string
    max_results?: number
  }): Promise<IngestionJobResponse> => {
    const response = await api.post<IngestionJobResponse>('/ingestion/sources/pubmed/runs', params)
    return response.data
  },

  ingestFromArxiv: async (params: {
    query: string
    max_results?: number
    category?: string
  }): Promise<IngestionJobResponse> => {
    const response = await api.post<IngestionJobResponse>('/ingestion/sources/arxiv/runs', params)
    return response.data
  },

  uploadPdf: async (file: File): Promise<Paper> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<Paper>('/papers/upload/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  generatePitch: async (paperId: string): Promise<Paper> => {
    const response = await api.post<Paper>(`/papers/${paperId}/generate-pitch`)
    return response.data
  },

  generateSimplifiedAbstract: async (paperId: string): Promise<Paper> => {
    const response = await api.post<Paper>(`/papers/${paperId}/generate-simplified-abstract`)
    return response.data
  },

  ingestFromSemanticScholar: async (params: {
    query: string
    max_results?: number
  }): Promise<IngestionJobResponse> => {
    const response = await api.post<IngestionJobResponse>('/ingestion/sources/semantic-scholar/runs', params)
    return response.data
  },

  getIngestionRun: async (runId: string): Promise<IngestionRunResponse> => {
    const response = await api.get<IngestionRunResponse>(`/ingestion/runs/${runId}`)
    return response.data
  },

  getRelatedPatents: async (paperId: string): Promise<RelatedPatentsResponse> => {
    const response = await api.get<RelatedPatentsResponse>(`/papers/${paperId}/patents`)
    return response.data
  },

  getCitationGraph: async (paperId: string): Promise<CitationGraphResponse> => {
    const response = await api.get<CitationGraphResponse>(`/papers/${paperId}/citations`)
    return response.data
  },
}
