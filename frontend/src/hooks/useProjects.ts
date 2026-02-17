import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { projectsApi } from '@/lib/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateProject } from '@/types'

interface QueryControlOptions {
  enabled?: boolean
  staleTime?: number
}

export function useProjects(options?: QueryControlOptions) {
  return useQuery({
    queryKey: queryKeys.projects.list(),
    queryFn: () => projectsApi.list(),
    placeholderData: keepPreviousData,
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  })
}

export function useProjectClusters(id: string) {
  return useQuery({
    queryKey: queryKeys.projects.clusters(id),
    queryFn: () => projectsApi.listClusters(id),
    enabled: !!id,
  })
}

export function useProjectCluster(projectId: string, clusterId: string) {
  return useQuery({
    queryKey: queryKeys.projects.cluster(projectId, clusterId),
    queryFn: () => projectsApi.getCluster(projectId, clusterId),
    enabled: !!projectId && !!clusterId,
  })
}

export function useInstitutionSearch(query: string) {
  return useQuery({
    queryKey: queryKeys.projects.institutions(query),
    queryFn: () => projectsApi.searchInstitutions(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  })
}

export function useAuthorSearch(query: string) {
  return useQuery({
    queryKey: queryKeys.projects.authors(query),
    queryFn: () => projectsApi.searchAuthors(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProject) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.list() })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects.list() })
      const prev = queryClient.getQueryData<{ items: { id: string }[]; total: number }>(
        queryKeys.projects.list()
      )

      if (prev?.items) {
        queryClient.setQueryData(queryKeys.projects.list(), {
          ...prev,
          items: prev.items.filter((project) => project.id !== deletedId),
          total: prev.total - 1,
        })
      }

      return { prev }
    },
    onError: (_err, _id, context) => {
      if (context?.prev) {
        queryClient.setQueryData(queryKeys.projects.list(), context.prev)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.list() })
    },
  })
}

export function useSyncProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => projectsApi.sync(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.clusters(id) })
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
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.clusters(projectId) })
    },
  })
}
