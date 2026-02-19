import type {
  DashboardSummary,
  TeamOverview,
  PaperAnalytics,
  FunnelAnalytics,
  BenchmarkAnalytics,
} from '@/types/core'

import { api } from '@/api/http/client'

export const analyticsApi = {
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>('/analytics/dashboard')
    return response.data
  },

  getTeamOverview: async (): Promise<TeamOverview> => {
    const response = await api.get<TeamOverview>('/analytics/team')
    return response.data
  },

  getPaperAnalytics: async (params?: { days?: number }): Promise<PaperAnalytics> => {
    const response = await api.get<PaperAnalytics>('/analytics/papers', { params })
    return response.data
  },

  getFunnelAnalytics: async (params?: {
    project_id?: string
    start_date?: string
    end_date?: string
  }): Promise<FunnelAnalytics> => {
    const response = await api.get<FunnelAnalytics>('/analytics/funnel', { params })
    return response.data
  },

  getBenchmarks: async (): Promise<BenchmarkAnalytics> => {
    const response = await api.get<BenchmarkAnalytics>('/analytics/benchmarks')
    return response.data
  },
}
