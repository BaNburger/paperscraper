import type { Paper } from '@/types/core'
import type {
  Submission,
  SubmissionDetail,
  SubmissionListResponse,
  CreateSubmissionRequest,
  UpdateSubmissionRequest,
  SubmissionReviewRequest,
  SubmissionAttachment,
  SubmissionScore,
} from '@/types/domains'

import { api } from '@/api/http/client'

export const submissionsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<SubmissionListResponse> => {
    const response = await api.get<SubmissionListResponse>('/submissions/', { params })
    return response.data
  },

  listMy: async (params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<SubmissionListResponse> => {
    const response = await api.get<SubmissionListResponse>('/submissions/my', { params })
    return response.data
  },

  get: async (id: string): Promise<SubmissionDetail> => {
    const response = await api.get<SubmissionDetail>(`/submissions/${id}`)
    return response.data
  },

  create: async (data: CreateSubmissionRequest): Promise<Submission> => {
    const response = await api.post<Submission>('/submissions/', data)
    return response.data
  },

  update: async (id: string, data: UpdateSubmissionRequest): Promise<Submission> => {
    const response = await api.patch<Submission>(`/submissions/${id}`, data)
    return response.data
  },

  submit: async (id: string): Promise<Submission> => {
    const response = await api.post<Submission>(`/submissions/${id}/submit`)
    return response.data
  },

  review: async (id: string, data: SubmissionReviewRequest): Promise<Submission> => {
    const response = await api.patch<Submission>(`/submissions/${id}/review`, data)
    return response.data
  },

  analyze: async (id: string): Promise<SubmissionScore> => {
    const response = await api.post<SubmissionScore>(`/submissions/${id}/analyze`)
    return response.data
  },

  convert: async (id: string): Promise<Paper> => {
    const response = await api.post<Paper>(`/submissions/${id}/convert`)
    return response.data
  },

  uploadAttachment: async (
    submissionId: string,
    file: File,
    attachmentType: string
  ): Promise<SubmissionAttachment> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('attachment_type', attachmentType)
    const response = await api.post<SubmissionAttachment>(
      `/submissions/${submissionId}/attachments`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },
}
