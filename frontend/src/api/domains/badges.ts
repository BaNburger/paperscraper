import type { BadgeListResponse, UserBadgeListResponse, UserStats } from '@/types/domains'

import { api } from '@/api/http/client'

export const badgesApi = {
  list: async (): Promise<BadgeListResponse> => {
    const response = await api.get<BadgeListResponse>('/badges/')
    return response.data
  },

  myBadges: async (): Promise<UserBadgeListResponse> => {
    const response = await api.get<UserBadgeListResponse>('/badges/me')
    return response.data
  },

  myStats: async (): Promise<UserStats> => {
    const response = await api.get<UserStats>('/badges/me/stats')
    return response.data
  },

  checkBadges: async (): Promise<UserBadgeListResponse> => {
    const response = await api.post<UserBadgeListResponse>('/badges/me/check')
    return response.data
  },
}
