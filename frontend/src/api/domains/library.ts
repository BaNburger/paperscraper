import type {
  LibraryCollection,
  LibraryCollectionItem,
  ReaderPayload,
  PaperHighlight,
  PaperTag,
} from '@/types/core'

import { api } from '@/api/http/client'

export const libraryApi = {
  listCollections: async (): Promise<{ items: LibraryCollection[]; total: number }> => {
    const response = await api.get<{ items: LibraryCollection[]; total: number }>('/library/collections')
    return response.data
  },

  createCollection: async (data: {
    name: string
    description?: string
    parent_id?: string
  }): Promise<LibraryCollection> => {
    const response = await api.post<LibraryCollection>('/library/collections', data)
    return response.data
  },

  updateCollection: async (
    collectionId: string,
    data: {
      name?: string
      description?: string
      parent_id?: string | null
    }
  ): Promise<LibraryCollection> => {
    const response = await api.patch<LibraryCollection>(`/library/collections/${collectionId}`, data)
    return response.data
  },

  deleteCollection: async (collectionId: string): Promise<void> => {
    await api.delete(`/library/collections/${collectionId}`)
  },

  addPaperToCollection: async (
    collectionId: string,
    paperId: string
  ): Promise<LibraryCollectionItem> => {
    const response = await api.post<LibraryCollectionItem>(
      `/library/collections/${collectionId}/papers/${paperId}`
    )
    return response.data
  },

  removePaperFromCollection: async (
    collectionId: string,
    paperId: string
  ): Promise<LibraryCollectionItem> => {
    const response = await api.delete<LibraryCollectionItem>(
      `/library/collections/${collectionId}/papers/${paperId}`
    )
    return response.data
  },

  getReader: async (paperId: string): Promise<ReaderPayload> => {
    const response = await api.get<ReaderPayload>(`/library/papers/${paperId}/reader`)
    return response.data
  },

  hydrateFullText: async (
    paperId: string
  ): Promise<{
    paper_id: string
    hydrated: boolean
    source?: string | null
    chunks_created: number
    message: string
  }> => {
    const response = await api.post(`/library/papers/${paperId}/hydrate-fulltext`)
    return response.data
  },

  listHighlights: async (
    paperId: string,
    includeInactive = false
  ): Promise<{ items: PaperHighlight[]; total: number }> => {
    const response = await api.get<{ items: PaperHighlight[]; total: number }>(
      `/library/papers/${paperId}/highlights`,
      { params: { include_inactive: includeInactive } }
    )
    return response.data
  },

  createHighlight: async (
    paperId: string,
    data: {
      chunk_id?: string
      chunk_ref?: string
      quote: string
      insight_summary: string
      confidence?: number
    }
  ): Promise<PaperHighlight> => {
    const response = await api.post<PaperHighlight>(`/library/papers/${paperId}/highlights`, data)
    return response.data
  },

  generateHighlights: async (
    paperId: string,
    targetCount = 8
  ): Promise<{ items: PaperHighlight[]; total: number }> => {
    const response = await api.post<{ items: PaperHighlight[]; total: number }>(
      `/library/papers/${paperId}/highlights/generate`,
      { target_count: targetCount }
    )
    return response.data
  },

  updateHighlight: async (
    paperId: string,
    highlightId: string,
    data: {
      quote?: string
      insight_summary?: string
      confidence?: number
      is_active?: boolean
    }
  ): Promise<PaperHighlight> => {
    const response = await api.patch<PaperHighlight>(
      `/library/papers/${paperId}/highlights/${highlightId}`,
      data
    )
    return response.data
  },

  deleteHighlight: async (paperId: string, highlightId: string): Promise<void> => {
    await api.delete(`/library/papers/${paperId}/highlights/${highlightId}`)
  },

  listTags: async (): Promise<{ items: Array<{ tag: string; usage_count: number }>; total: number }> => {
    const response = await api.get<{ items: Array<{ tag: string; usage_count: number }>; total: number }>(
      '/library/tags'
    )
    return response.data
  },

  addPaperTag: async (paperId: string, tag: string): Promise<PaperTag> => {
    const response = await api.post<PaperTag>(`/library/papers/${paperId}/tags`, { tag })
    return response.data
  },

  removePaperTag: async (paperId: string, tag: string): Promise<{ removed: boolean }> => {
    const response = await api.delete<{ removed: boolean }>(`/library/papers/${paperId}/tags/${tag}`)
    return response.data
  },
}
