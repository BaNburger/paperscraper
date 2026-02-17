import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api'
import type { CreateResearchGroup } from '@/types'

interface QueryControlOptions {
  enabled?: boolean
  staleTime?: number
}

export function useResearchGroups(options?: QueryControlOptions) {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
    placeholderData: keepPreviousData,
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime,
  })
}

// Backward-compatible alias
export const useProjects = useResearchGroups

export function useResearchGroup(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  })
}

// Backward-compatible alias
export const useProject = useResearchGroup

export function useResearchGroupClusters(id: string) {
  return useQuery({
    queryKey: ['projectClusters', id],
    queryFn: () => projectsApi.listClusters(id),
    enabled: !!id,
  })
}

export function useResearchGroupCluster(projectId: string, clusterId: string) {
  return useQuery({
    queryKey: ['projectCluster', projectId, clusterId],
    queryFn: () => projectsApi.getCluster(projectId, clusterId),
    enabled: !!projectId && !!clusterId,
  })
}

export function useInstitutionSearch(query: string) {
  return useQuery({
    queryKey: ['institutionSearch', query],
    queryFn: () => projectsApi.searchInstitutions(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  })
}

export function useAuthorSearch(query: string) {
  return useQuery({
    queryKey: ['authorSearch', query],
    queryFn: () => projectsApi.searchAuthors(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  })
}

export function useCreateResearchGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateResearchGroup) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

// Backward-compatible alias
export const useCreateProject = useCreateResearchGroup

export function useDeleteResearchGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['projects'] })
      const prev = queryClient.getQueryData<{ items: { id: string }[]; total: number }>([
        'projects',
      ])
      if (prev?.items) {
        queryClient.setQueryData(['projects'], {
          ...prev,
          items: prev.items.filter((p) => p.id !== deletedId),
          total: prev.total - 1,
        })
      }
      return { prev }
    },
    onError: (_err, _id, context) => {
      if (context?.prev) {
        queryClient.setQueryData(['projects'], context.prev)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

// Backward-compatible alias
export const useDeleteProject = useDeleteResearchGroup

export function useSyncResearchGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => projectsApi.sync(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      queryClient.invalidateQueries({ queryKey: ['projectClusters', id] })
    },
  })
}

export function useUpdateClusterLabel() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      clusterId,
      label,
    }: {
      projectId: string
      clusterId: string
      label: string
    }) => projectsApi.updateCluster(projectId, clusterId, { label }),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['projectClusters', projectId] })
    },
  })
}
