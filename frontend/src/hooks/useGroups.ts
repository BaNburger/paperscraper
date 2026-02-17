import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { groupsApi } from '@/lib/api'
import type { CreateGroupRequest, UpdateGroupRequest } from '@/types'

interface QueryControlOptions {
  enabled?: boolean
  staleTime?: number
}

export function useGroups(
  params?: { page?: number; page_size?: number; type?: string },
  options?: QueryControlOptions
) {
  return useQuery({
    queryKey: ['groups', params],
    queryFn: () => groupsApi.list(params),
    placeholderData: keepPreviousData,
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime,
  })
}

export function useGroup(id: string) {
  return useQuery({
    queryKey: ['group', id],
    queryFn: () => groupsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateGroupRequest) => groupsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useUpdateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateGroupRequest }) =>
      groupsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['group', id] })
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useDeleteGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => groupsApi.delete(id),
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['groups'] })
      const queries = queryClient.getQueriesData<{ items: { id: string }[]; total: number }>({
        queryKey: ['groups'],
      })
      for (const [key, data] of queries) {
        if (data?.items) {
          queryClient.setQueryData(key, {
            ...data,
            items: data.items.filter((g) => g.id !== deletedId),
            total: data.total - 1,
          })
        }
      }
      return { queries }
    },
    onError: (_err, _id, context) => {
      if (context?.queries) {
        for (const [key, data] of context.queries) {
          queryClient.setQueryData(key, data)
        }
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useAddMembers() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, researcherIds }: { groupId: string; researcherIds: string[] }) =>
      groupsApi.addMembers(groupId, researcherIds),
    onSuccess: (_, { groupId }) => {
      queryClient.invalidateQueries({ queryKey: ['group', groupId] })
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useRemoveMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, researcherId }: { groupId: string; researcherId: string }) =>
      groupsApi.removeMember(groupId, researcherId),
    onSuccess: (_, { groupId }) => {
      queryClient.invalidateQueries({ queryKey: ['group', groupId] })
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useSuggestMembers() {
  return useMutation({
    mutationFn: ({ keywords, targetSize }: { keywords: string[]; targetSize?: number }) =>
      groupsApi.suggestMembers(keywords, targetSize),
  })
}
