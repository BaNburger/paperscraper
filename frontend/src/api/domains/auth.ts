import type {
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  User,
  UpdateUserRequest,
  ChangePasswordRequest,
  UpdateOrganizationRequest,
  Organization,
  InvitationInfo,
  AcceptInviteRequest,
  TeamInvitation,
  OrganizationUsers,
  UserListItem,
  UpdateBrandingRequest,
} from '@/types'

import { api } from '@/api/http/client'

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/register', data)
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  verifyEmail: async (token: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/verify-email', { token })
    return response.data
  },

  resendVerification: async (email: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/resend-verification', { email })
    return response.data
  },

  forgotPassword: async (email: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/forgot-password', { email })
    return response.data
  },

  resetPassword: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/reset-password', {
      token,
      new_password: newPassword,
    })
    return response.data
  },

  getInvitationInfo: async (token: string): Promise<InvitationInfo> => {
    const response = await api.get<InvitationInfo>(`/auth/invitation/${token}`)
    return response.data
  },

  acceptInvitation: async (data: AcceptInviteRequest): Promise<AuthTokens> => {
    const response = await api.post<AuthTokens>('/auth/accept-invite', data)
    return response.data
  },

  inviteUser: async (email: string, role: string): Promise<TeamInvitation> => {
    const response = await api.post<TeamInvitation>('/auth/invite', { email, role })
    return response.data
  },

  listInvitations: async (): Promise<TeamInvitation[]> => {
    const response = await api.get<TeamInvitation[]>('/auth/invitations')
    return response.data
  },

  cancelInvitation: async (invitationId: string): Promise<void> => {
    await api.delete(`/auth/invitations/${invitationId}`)
  },

  listUsers: async (): Promise<OrganizationUsers> => {
    const response = await api.get<OrganizationUsers>('/auth/users')
    return response.data
  },

  updateUserRole: async (userId: string, role: string): Promise<UserListItem> => {
    const response = await api.patch<UserListItem>(`/auth/users/${userId}/role`, { role })
    return response.data
  },

  deactivateUser: async (userId: string): Promise<UserListItem> => {
    const response = await api.post<UserListItem>(`/auth/users/${userId}/deactivate`)
    return response.data
  },

  reactivateUser: async (userId: string): Promise<UserListItem> => {
    const response = await api.post<UserListItem>(`/auth/users/${userId}/reactivate`)
    return response.data
  },

  updateProfile: async (data: UpdateUserRequest): Promise<User> => {
    const response = await api.patch<User>('/auth/me', data)
    return response.data
  },

  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await api.post('/auth/change-password', data)
  },

  updateOrganization: async (data: UpdateOrganizationRequest): Promise<Organization> => {
    const response = await api.patch<Organization>('/auth/organization', data)
    return response.data
  },

  completeOnboarding: async (): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/onboarding/complete')
    return response.data
  },

  getMyPermissions: async (): Promise<{ role: string; permissions: string[] }> => {
    const response = await api.get<{ role: string; permissions: string[] }>('/auth/permissions')
    return response.data
  },

  getRoles: async (): Promise<{ roles: Record<string, string[]> }> => {
    const response = await api.get<{ roles: Record<string, string[]> }>('/auth/roles')
    return response.data
  },

  updateBranding: async (data: UpdateBrandingRequest): Promise<Organization> => {
    const response = await api.patch<Organization>('/auth/organization/branding', data)
    return response.data
  },

  uploadLogo: async (file: File): Promise<Organization> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<Organization>('/auth/organization/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
}
