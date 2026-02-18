import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { discoveryApi } from '@/lib/api'
import { queryKeys } from '@/config/queryKeys'

export function useDiscoveryProfiles() {
  return useQuery({
    queryKey: queryKeys.discovery.profiles(),
    queryFn: () => discoveryApi.listProfiles(),
  })
}

export function useDiscoveryRuns(savedSearchId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.discovery.runs(savedSearchId ?? ''),
    queryFn: () => discoveryApi.listRuns(savedSearchId!),
    enabled: !!savedSearchId,
  })
}

export function useTriggerDiscovery() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (savedSearchId: string) => discoveryApi.triggerRun(savedSearchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery'] })
    },
  })
}
