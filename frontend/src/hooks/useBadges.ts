import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { badgesApi } from '@/lib/api'
import { queryKeys } from '@/config/queryKeys'

export function useBadges() {
  return useQuery({
    queryKey: queryKeys.badges.all(),
    queryFn: () => badgesApi.list(),
  })
}

export function useMyBadges() {
  return useQuery({
    queryKey: queryKeys.badges.mine(),
    queryFn: () => badgesApi.myBadges(),
  })
}

export function useUserStats() {
  return useQuery({
    queryKey: queryKeys.badges.stats(),
    queryFn: () => badgesApi.myStats(),
  })
}

export function useCheckBadges() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => badgesApi.checkBadges(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.badges.mine() })
      queryClient.invalidateQueries({ queryKey: queryKeys.badges.stats() })
    },
  })
}
