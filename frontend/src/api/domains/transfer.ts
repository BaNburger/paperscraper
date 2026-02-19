import type {
  Conversation,
  ConversationDetail,
  ConversationListResponse,
  CreateConversationRequest,
  ConversationMessage,
  ConversationResource,
  MessageTemplate,
  NextStepsResponse,
} from '@/types/domains'

import { api } from '@/api/http/client'

export const transferApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    stage?: string
    search?: string
  }): Promise<ConversationListResponse> => {
    const response = await api.get<ConversationListResponse>('/transfer/', { params })
    return response.data
  },

  get: async (id: string): Promise<ConversationDetail> => {
    const response = await api.get<ConversationDetail>(`/transfer/${id}`)
    return response.data
  },

  create: async (data: CreateConversationRequest): Promise<Conversation> => {
    const response = await api.post<Conversation>('/transfer/', data)
    return response.data
  },

  updateStage: async (id: string, stage: string, notes?: string): Promise<Conversation> => {
    const response = await api.patch<Conversation>(`/transfer/${id}`, { stage, notes })
    return response.data
  },

  sendMessage: async (conversationId: string, content: string, mentions?: string[]): Promise<ConversationMessage> => {
    const response = await api.post<ConversationMessage>(`/transfer/${conversationId}/messages`, {
      content,
      mentions: mentions || [],
    })
    return response.data
  },

  sendMessageFromTemplate: async (
    conversationId: string,
    templateId: string,
    mentions?: string[]
  ): Promise<ConversationMessage> => {
    const response = await api.post<ConversationMessage>(
      `/transfer/${conversationId}/messages/from-template`,
      { template_id: templateId, mentions: mentions || [] }
    )
    return response.data
  },

  addResource: async (
    conversationId: string,
    data: { name: string; url?: string; file_path?: string; resource_type: string }
  ): Promise<ConversationResource> => {
    const response = await api.post<ConversationResource>(`/transfer/${conversationId}/resources`, data)
    return response.data
  },

  uploadResource: async (conversationId: string, file: File): Promise<ConversationResource> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<ConversationResource>(
      `/transfer/${conversationId}/resources/upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  getNextSteps: async (conversationId: string): Promise<NextStepsResponse> => {
    const response = await api.get<NextStepsResponse>(`/transfer/${conversationId}/next-steps`)
    return response.data
  },

  listTemplates: async (stage?: string): Promise<MessageTemplate[]> => {
    const response = await api.get<MessageTemplate[]>('/transfer/templates/', {
      params: stage ? { stage } : undefined,
    })
    return response.data
  },
}
