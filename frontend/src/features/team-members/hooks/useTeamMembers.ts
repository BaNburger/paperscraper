import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'

async function invalidateTeamQueries(queryClient: ReturnType<typeof useQueryClient>) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.auth.pendingInvitations() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.auth.organizationUsers() }),
  ])
}

export function useTeamMembers() {
  const queryClient = useQueryClient()

  const usersQuery = useQuery({
    queryKey: queryKeys.auth.organizationUsers(),
    queryFn: authApi.listUsers,
  })

  const invitationsQuery = useQuery({
    queryKey: queryKeys.auth.pendingInvitations(),
    queryFn: authApi.listInvitations,
  })

  const inviteMutation = useMutation({
    mutationFn: ({ email, role }: { email: string; role: string }) => authApi.inviteUser(email, role),
    onSuccess: async () => {
      await invalidateTeamQueries(queryClient)
    },
  })

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => authApi.updateUserRole(userId, role),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.organizationUsers() })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => authApi.deactivateUser(userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.organizationUsers() })
    },
  })

  const reactivateMutation = useMutation({
    mutationFn: (userId: string) => authApi.reactivateUser(userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.organizationUsers() })
    },
  })

  const cancelInvitationMutation = useMutation({
    mutationFn: (invitationId: string) => authApi.cancelInvitation(invitationId),
    onSuccess: async () => {
      await invalidateTeamQueries(queryClient)
    },
  })

  return {
    usersQuery,
    invitationsQuery,
    inviteMutation,
    updateRoleMutation,
    deactivateMutation,
    reactivateMutation,
    cancelInvitationMutation,
  }
}
