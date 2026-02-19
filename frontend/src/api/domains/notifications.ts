import { api } from '@/api/http/client'
import type { NotificationListResponse } from '@/types/domains'

export const notificationsApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    unread_only?: boolean
  }): Promise<NotificationListResponse> => {
    const response = await api.get<NotificationListResponse>('/notifications', { params })
    return response.data
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get<{ unread_count: number }>('/notifications/unread-count')
    return response.data
  },

  markAsRead: async (notificationIds: string[]): Promise<{ updated: number }> => {
    const response = await api.post<{ updated: number }>('/notifications/mark-read', {
      notification_ids: notificationIds,
    })
    return response.data
  },

  markAllAsRead: async (): Promise<{ updated: number }> => {
    const response = await api.post<{ updated: number }>('/notifications/mark-all-read')
    return response.data
  },
}
