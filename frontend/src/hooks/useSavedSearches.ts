import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { savedSearchesApi } from '@/lib/api'
import type { CreateSavedSearchRequest, UpdateSavedSearchRequest } from '@/types'

export function useSavedSearches(params?: {
  page?: number
  page_size?: number
  include_public?: boolean
}) {
  return useQuery({
    queryKey: ['saved-searches', params],
    queryFn: () => savedSearchesApi.list(params),
  })
}

export function useSavedSearch(id: string | undefined) {
  return useQuery({
    queryKey: ['saved-search', id],
    queryFn: () => savedSearchesApi.get(id!),
    enabled: !!id,
  })
}

export function useSharedSearch(shareToken: string | undefined) {
  return useQuery({
    queryKey: ['shared-search', shareToken],
    queryFn: () => savedSearchesApi.getByShareToken(shareToken!),
    enabled: !!shareToken,
  })
}

export function useCreateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSavedSearchRequest) => savedSearchesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}

export function useUpdateSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSavedSearchRequest }) =>
      savedSearchesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
      queryClient.invalidateQueries({ queryKey: ['saved-search', variables.id] })
    },
  })
}

export function useDeleteSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedSearchesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}

export function useGenerateShareLink() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedSearchesApi.generateShareLink(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['saved-search', id] })
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}

export function useRevokeShareLink() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedSearchesApi.revokeShareLink(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['saved-search', id] })
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] })
    },
  })
}

export function useRunSavedSearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, params }: { id: string; params?: { page?: number; page_size?: number } }) =>
      savedSearchesApi.run(id, params),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['saved-search', variables.id] })
    },
  })
}
