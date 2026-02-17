import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { discoveryApi } from '@/lib/api'

export function useDiscoveryProfiles() {
  return useQuery({
    queryKey: ['discoveryProfiles'],
    queryFn: () => discoveryApi.listProfiles(),
  })
}

export function useDiscoveryRuns(savedSearchId: string | undefined) {
  return useQuery({
    queryKey: ['discoveryRuns', savedSearchId],
    queryFn: () => discoveryApi.listRuns(savedSearchId!),
    enabled: !!savedSearchId,
  })
}

export function useTriggerDiscovery() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (savedSearchId: string) => discoveryApi.triggerRun(savedSearchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discoveryProfiles'] })
      queryClient.invalidateQueries({ queryKey: ['discoveryRuns'] })
    },
  })
}
