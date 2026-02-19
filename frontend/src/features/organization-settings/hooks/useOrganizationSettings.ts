import { useMutation, useQuery } from '@tanstack/react-query'
import { authApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import type { UpdateOrganizationRequest } from '@/types'

type MutationCallbacks = {
  onSuccess?: () => void
  onError?: () => void
}

export function useOrganizationRoles() {
  return useQuery({
    queryKey: queryKeys.auth.roles(),
    queryFn: () => authApi.getRoles(),
    staleTime: 5 * 60 * 1000,
  })
}

export function useMyPermissions() {
  return useQuery({
    queryKey: queryKeys.auth.permissions(),
    queryFn: () => authApi.getMyPermissions(),
    staleTime: 5 * 60 * 1000,
  })
}

export function useUpdateOrganization(callbacks?: MutationCallbacks) {
  return useMutation({
    mutationFn: (data: UpdateOrganizationRequest) => authApi.updateOrganization(data),
    onSuccess: () => callbacks?.onSuccess?.(),
    onError: () => callbacks?.onError?.(),
  })
}
