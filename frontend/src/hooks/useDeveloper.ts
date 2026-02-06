import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { developerApi } from '@/lib/api'
import type {
  CreateAPIKeyRequest,
  CreateWebhookRequest,
  UpdateWebhookRequest,
  CreateRepositorySourceRequest,
  UpdateRepositorySourceRequest,
} from '@/types'

// =============================================================================
// API Keys Hooks
// =============================================================================

export function useApiKeys() {
  return useQuery({
    queryKey: ['api-keys'],
    queryFn: () => developerApi.listApiKeys(),
  })
}

export function useCreateApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateAPIKeyRequest) => developerApi.createApiKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => developerApi.revokeApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })
}

// =============================================================================
// Webhooks Hooks
// =============================================================================

export function useWebhooks() {
  return useQuery({
    queryKey: ['webhooks'],
    queryFn: () => developerApi.listWebhooks(),
  })
}

export function useCreateWebhook() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateWebhookRequest) => developerApi.createWebhook(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateWebhookRequest }) =>
      developerApi.updateWebhook(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: (id: string) => developerApi.testWebhook(id),
  })
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => developerApi.deleteWebhook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
    },
  })
}

// =============================================================================
// Repository Sources Hooks
// =============================================================================

export function useRepositories() {
  return useQuery({
    queryKey: ['repositories'],
    queryFn: () => developerApi.listRepositories(),
  })
}

export function useRepository(id: string | undefined) {
  return useQuery({
    queryKey: ['repositories', id],
    queryFn: () => developerApi.getRepository(id!),
    enabled: !!id,
  })
}

export function useCreateRepository() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateRepositorySourceRequest) => developerApi.createRepository(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}

export function useUpdateRepository() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateRepositorySourceRequest }) =>
      developerApi.updateRepository(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}

export function useSyncRepository() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => developerApi.syncRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}

export function useDeleteRepository() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => developerApi.deleteRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}
