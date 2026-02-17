import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { trendsApi } from '@/lib/api'

export function useTrendTopics(includeInactive = false) {
  return useQuery({
    queryKey: ['trends', includeInactive],
    queryFn: () => trendsApi.list({ include_inactive: includeInactive }),
  })
}

export function useTrendDashboard(id: string) {
  return useQuery({
    queryKey: ['trends', id, 'dashboard'],
    queryFn: () => trendsApi.getDashboard(id),
    enabled: !!id,
    staleTime: 60000,
  })
}

export function useTrendPapers(id: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['trends', id, 'papers', page, pageSize],
    queryFn: () => trendsApi.getPapers(id, { page, page_size: pageSize }),
    enabled: !!id,
  })
}

export function useCreateTrendTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description: string; color?: string }) =>
      trendsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trends'] })
    },
  })
}

export function useUpdateTrendTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string; color?: string; is_active?: boolean } }) =>
      trendsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['trends'] })
      queryClient.invalidateQueries({ queryKey: ['trends', variables.id] })
    },
  })
}

export function useDeleteTrendTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => trendsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trends'] })
    },
  })
}

export function useAnalyzeTrend() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, params }: { id: string; params?: { min_similarity?: number; max_papers?: number } }) =>
      trendsApi.analyze(id, params),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['trends'] })
      queryClient.invalidateQueries({ queryKey: ['trends', variables.id] })
    },
  })
}
