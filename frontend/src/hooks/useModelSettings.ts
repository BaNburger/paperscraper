import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { modelSettingsApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateModelConfigurationRequest, UpdateModelConfigurationRequest } from '@/types'

export function useModelConfigurations() {
  return useQuery({
    queryKey: queryKeys.models.configurations(),
    queryFn: () => modelSettingsApi.listModels(),
  })
}

export function useModelUsage(days?: number) {
  return useQuery({
    queryKey: queryKeys.models.usage(days ?? 90),
    queryFn: () => modelSettingsApi.getUsage(days),
  })
}

export function useCreateModelConfiguration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateModelConfigurationRequest) => modelSettingsApi.createModel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.models.configurations() })
    },
  })
}

export function useUpdateModelConfiguration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateModelConfigurationRequest }) =>
      modelSettingsApi.updateModel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.models.configurations() })
    },
  })
}

export function useDeleteModelConfiguration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => modelSettingsApi.deleteModel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.models.configurations() })
    },
  })
}
