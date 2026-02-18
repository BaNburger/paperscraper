import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateScheduledReportRequest, UpdateScheduledReportRequest } from '@/types'

export function useScheduledReports(params?: {
  page?: number
  page_size?: number
  is_active?: boolean
}) {
  return useQuery({
    queryKey: queryKeys.reports.scheduled(params),
    queryFn: () => reportsApi.listScheduledReports(params),
  })
}

export function useScheduledReport(reportId: string) {
  return useQuery({
    queryKey: queryKeys.reports.scheduledDetail(reportId),
    queryFn: () => reportsApi.getScheduledReport(reportId),
    enabled: !!reportId,
  })
}

export function useCreateScheduledReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateScheduledReportRequest) =>
      reportsApi.createScheduledReport(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'scheduled'] })
    },
  })
}

export function useUpdateScheduledReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      reportId,
      data,
    }: {
      reportId: string
      data: UpdateScheduledReportRequest
    }) => reportsApi.updateScheduledReport(reportId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'scheduled'] })
    },
  })
}

export function useDeleteScheduledReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reportId: string) => reportsApi.deleteScheduledReport(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'scheduled'] })
    },
  })
}

export function useRunScheduledReport() {
  return useMutation({
    mutationFn: (reportId: string) => reportsApi.runScheduledReport(reportId),
  })
}
