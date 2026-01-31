import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { alertsApi } from '@/lib/api'
import type { CreateAlertRequest, UpdateAlertRequest } from '@/types'

export function useAlerts(params?: {
  page?: number
  page_size?: number
  active_only?: boolean
}) {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => alertsApi.list(params),
  })
}

export function useAlert(id: string | undefined) {
  return useQuery({
    queryKey: ['alert', id],
    queryFn: () => alertsApi.get(id!),
    enabled: !!id,
  })
}

export function useCreateAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateAlertRequest) => alertsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useUpdateAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAlertRequest }) =>
      alertsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alert', variables.id] })
    },
  })
}

export function useDeleteAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => alertsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useAlertResults(alertId: string | undefined, params?: {
  page?: number
  page_size?: number
}) {
  return useQuery({
    queryKey: ['alert-results', alertId, params],
    queryFn: () => alertsApi.getResults(alertId!, params),
    enabled: !!alertId,
  })
}

export function useTestAlert() {
  return useMutation({
    mutationFn: (id: string) => alertsApi.test(id),
  })
}

export function useTriggerAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => alertsApi.trigger(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['alert', id] })
      queryClient.invalidateQueries({ queryKey: ['alert-results', id] })
    },
  })
}
