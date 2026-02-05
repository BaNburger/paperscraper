import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { badgesApi } from '@/lib/api'

export function useBadges() {
  return useQuery({
    queryKey: ['badges'],
    queryFn: () => badgesApi.list(),
  })
}

export function useMyBadges() {
  return useQuery({
    queryKey: ['myBadges'],
    queryFn: () => badgesApi.myBadges(),
  })
}

export function useUserStats() {
  return useQuery({
    queryKey: ['userStats'],
    queryFn: () => badgesApi.myStats(),
  })
}

export function useCheckBadges() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => badgesApi.checkBadges(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myBadges'] })
      queryClient.invalidateQueries({ queryKey: ['userStats'] })
    },
  })
}
