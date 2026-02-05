import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { modelSettingsApi } from '@/lib/api'
import type { CreateModelConfigurationRequest, UpdateModelConfigurationRequest } from '@/types'

export function useModelConfigurations() {
  return useQuery({
    queryKey: ['model-configurations'],
    queryFn: () => modelSettingsApi.listModels(),
  })
}

export function useModelUsage(days?: number) {
  return useQuery({
    queryKey: ['model-usage', days],
    queryFn: () => modelSettingsApi.getUsage(days),
  })
}

export function useCreateModelConfiguration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateModelConfigurationRequest) => modelSettingsApi.createModel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-configurations'] })
    },
  })
}

export function useUpdateModelConfiguration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateModelConfigurationRequest }) =>
      modelSettingsApi.updateModel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-configurations'] })
    },
  })
}

export function useDeleteModelConfiguration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => modelSettingsApi.deleteModel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-configurations'] })
    },
  })
}
