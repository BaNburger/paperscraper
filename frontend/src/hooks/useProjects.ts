import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api'

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  })
}

export function useKanban(projectId: string) {
  return useQuery({
    queryKey: ['kanban', projectId],
    queryFn: () => projectsApi.getKanban(projectId),
    enabled: !!projectId,
  })
}

export function useProjectStatistics(projectId: string) {
  return useQuery({
    queryKey: ['projectStats', projectId],
    queryFn: () => projectsApi.getStatistics(projectId),
    enabled: !!projectId,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { name: string; description?: string }) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string
      data: { name?: string; description?: string; is_active?: boolean }
    }) => projectsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useMovePaper() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      paperId,
      stage,
    }: {
      projectId: string
      paperId: string
      stage: string
    }) => projectsApi.movePaper(projectId, paperId, stage),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projectStats', projectId] })
    },
  })
}

export function useAddPaperToProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, paperId }: { projectId: string; paperId: string }) =>
      projectsApi.addPaper(projectId, paperId),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projectStats', projectId] })
    },
  })
}

export function useRemovePaperFromProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, paperId }: { projectId: string; paperId: string }) =>
      projectsApi.removePaper(projectId, paperId),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['kanban', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projectStats', projectId] })
    },
  })
}
