import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeApi } from '@/lib/api'
import type { CreateKnowledgeSourceRequest, UpdateKnowledgeSourceRequest } from '@/types'

export function usePersonalKnowledge() {
  return useQuery({
    queryKey: ['knowledge', 'personal'],
    queryFn: () => knowledgeApi.listPersonal(),
  })
}

export function useOrganizationKnowledge() {
  return useQuery({
    queryKey: ['knowledge', 'organization'],
    queryFn: () => knowledgeApi.listOrganization(),
  })
}

export function useCreatePersonalKnowledge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateKnowledgeSourceRequest) => knowledgeApi.createPersonal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'personal'] })
    },
  })
}

export function useUpdatePersonalKnowledge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateKnowledgeSourceRequest }) =>
      knowledgeApi.updatePersonal(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'personal'] })
    },
  })
}

export function useDeletePersonalKnowledge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => knowledgeApi.deletePersonal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'personal'] })
    },
  })
}

export function useCreateOrganizationKnowledge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateKnowledgeSourceRequest) => knowledgeApi.createOrganization(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'organization'] })
    },
  })
}

export function useUpdateOrganizationKnowledge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateKnowledgeSourceRequest }) =>
      knowledgeApi.updateOrganization(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'organization'] })
    },
  })
}

export function useDeleteOrganizationKnowledge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteOrganization(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'organization'] })
    },
  })
}
