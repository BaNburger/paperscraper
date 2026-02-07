import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/lib/api'
import type { NotificationItem } from '@/types'

export interface Notification {
  id: string
  type: 'alert' | 'badge' | 'system'
  title: string
  message: string | null
  isRead: boolean
  resourceType: string | null
  resourceId: string | null
  timestamp: string
}

function toNotification(item: NotificationItem): Notification {
  return {
    id: item.id,
    type: item.type,
    title: item.title,
    message: item.message,
    isRead: item.is_read,
    resourceType: item.resource_type,
    resourceId: item.resource_id,
    timestamp: item.created_at,
  }
}

export function useNotifications(limit = 20) {
  const queryClient = useQueryClient()

  // Fetch notifications from backend with polling
  const notificationsQuery = useQuery({
    queryKey: ['notifications', 'list', limit],
    queryFn: () => notificationsApi.list({ page: 1, page_size: limit }),
    staleTime: 1000 * 30, // 30 seconds
    refetchInterval: 1000 * 60, // Poll every 60 seconds
  })

  // Lightweight unread count query for badge display (polls more frequently)
  const unreadCountQuery = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationsApi.getUnreadCount(),
    staleTime: 1000 * 15, // 15 seconds
    refetchInterval: 1000 * 30, // Poll every 30 seconds
  })

  const notifications = (notificationsQuery.data?.items ?? []).map(toNotification)
  const unreadCount =
    unreadCountQuery.data?.unread_count ??
    notificationsQuery.data?.unread_count ??
    0

  // Mutation to mark specific notifications as read
  const markAsReadMutation = useMutation({
    mutationFn: (notificationIds: string[]) =>
      notificationsApi.markAsRead(notificationIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  // Mutation to mark all notifications as read
  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAsRead = (notificationId: string) => {
    markAsReadMutation.mutate([notificationId])
  }

  const markAllAsRead = () => {
    markAllAsReadMutation.mutate()
  }

  return {
    notifications,
    unreadCount,
    isLoading: notificationsQuery.isLoading,
    isError: notificationsQuery.isError,
    markAsRead,
    markAllAsRead,
    refetch: () => {
      notificationsQuery.refetch()
      unreadCountQuery.refetch()
    },
  }
}
