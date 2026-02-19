import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authorsApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateContactRequest } from '@/types'

export function useAuthors(params?: { page?: number; page_size?: number; search?: string }) {
  return useQuery({
    queryKey: queryKeys.authors.list(params),
    queryFn: () => authorsApi.list(params),
  })
}

export function useAuthorProfile(authorId: string) {
  return useQuery({
    queryKey: queryKeys.authors.profile(authorId),
    queryFn: () => authorsApi.getProfile(authorId),
    enabled: !!authorId,
  })
}

export function useAuthorDetail(authorId: string) {
  return useQuery({
    queryKey: queryKeys.authors.detail(authorId),
    queryFn: () => authorsApi.getDetail(authorId),
    enabled: !!authorId,
  })
}

export function useAuthorContactStats(authorId: string) {
  return useQuery({
    queryKey: queryKeys.authors.contactStats(authorId),
    queryFn: () => authorsApi.getContactStats(authorId),
    enabled: !!authorId,
  })
}

export function useCreateContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ authorId, data }: { authorId: string; data: CreateContactRequest }) =>
      authorsApi.createContact(authorId, data),
    onSuccess: (_, { authorId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.detail(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.contactStats(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.listRoot() })
    },
  })
}

export function useUpdateContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      authorId,
      contactId,
      data,
    }: {
      authorId: string
      contactId: string
      data: Partial<CreateContactRequest>
    }) => authorsApi.updateContact(authorId, contactId, data),
    onSuccess: (_, { authorId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.detail(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.contactStats(authorId) })
    },
  })
}

export function useDeleteContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ authorId, contactId }: { authorId: string; contactId: string }) =>
      authorsApi.deleteContact(authorId, contactId),
    onSuccess: (_, { authorId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.detail(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.contactStats(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.listRoot() })
    },
  })
}

export function useEnrichAuthor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      authorId,
      source,
      forceUpdate,
    }: {
      authorId: string
      source?: string
      forceUpdate?: boolean
    }) => authorsApi.enrichAuthor(authorId, { source, force_update: forceUpdate }),
    onSuccess: (_, { authorId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.profile(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.detail(authorId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.authors.listRoot() })
    },
  })
}
