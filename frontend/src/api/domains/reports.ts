import type {
  ScheduledReport,
  ScheduledReportListResponse,
  CreateScheduledReportRequest,
  UpdateScheduledReportRequest,
} from '@/types/core'

import { api } from '@/api/http/client'

export const reportsApi = {
  listScheduledReports: async (params?: {
    page?: number
    page_size?: number
    is_active?: boolean
  }): Promise<ScheduledReportListResponse> => {
    const response = await api.get<ScheduledReportListResponse>('/reports/scheduled', { params })
    return response.data
  },

  getScheduledReport: async (reportId: string): Promise<ScheduledReport> => {
    const response = await api.get<ScheduledReport>(`/reports/scheduled/${reportId}`)
    return response.data
  },

  createScheduledReport: async (data: CreateScheduledReportRequest): Promise<ScheduledReport> => {
    const response = await api.post<ScheduledReport>('/reports/scheduled', data)
    return response.data
  },

  updateScheduledReport: async (
    reportId: string,
    data: UpdateScheduledReportRequest
  ): Promise<ScheduledReport> => {
    const response = await api.patch<ScheduledReport>(`/reports/scheduled/${reportId}`, data)
    return response.data
  },

  deleteScheduledReport: async (reportId: string): Promise<void> => {
    await api.delete(`/reports/scheduled/${reportId}`)
  },

  runScheduledReport: async (reportId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<{ success: boolean; message: string }>(
      `/reports/scheduled/${reportId}/run`
    )
    return response.data
  },
}
