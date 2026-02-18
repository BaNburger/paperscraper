import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { groupsApi } from '@/lib/api'
import { queryKeys } from '@/config/queryKeys'
import { optimisticDeleteById, rollbackOptimisticSnapshots } from '@/lib/query'
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
    queryKey: queryKeys.groups.list(params),
    queryFn: () => groupsApi.list(params),
    placeholderData: keepPreviousData,
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime,
  })
}

export function useGroup(id: string) {
  return useQuery({
    queryKey: queryKeys.groups.detail(id),
    queryFn: () => groupsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateGroupRequest) => groupsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups', 'list'] })
    },
  })
}

export function useUpdateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateGroupRequest }) =>
      groupsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups.detail(id) })
      queryClient.invalidateQueries({ queryKey: ['groups', 'list'] })
    },
  })
}

export function useDeleteGroup() {
  const queryClient = useQueryClient()
  const groupsListKey = ['groups', 'list'] as const

  return useMutation({
    mutationFn: (id: string) => groupsApi.delete(id),
    onMutate: async (deletedId) => {
      const snapshots = await optimisticDeleteById<{ id: string }>(
        queryClient,
        groupsListKey,
        deletedId,
      )
      return { snapshots }
    },
    onError: (_err, _id, context) => {
      rollbackOptimisticSnapshots(queryClient, context?.snapshots)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: groupsListKey })
    },
  })
}

export function useAddMembers() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, researcherIds }: { groupId: string; researcherIds: string[] }) =>
      groupsApi.addMembers(groupId, researcherIds),
    onSuccess: (_, { groupId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups.detail(groupId) })
      queryClient.invalidateQueries({ queryKey: ['groups', 'list'] })
    },
  })
}

export function useRemoveMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, researcherId }: { groupId: string; researcherId: string }) =>
      groupsApi.removeMember(groupId, researcherId),
    onSuccess: (_, { groupId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups.detail(groupId) })
      queryClient.invalidateQueries({ queryKey: ['groups', 'list'] })
    },
  })
}

export function useSuggestMembers() {
  return useMutation({
    mutationFn: ({ keywords, targetSize }: { keywords: string[]; targetSize?: number }) =>
      groupsApi.suggestMembers(keywords, targetSize),
  })
}
