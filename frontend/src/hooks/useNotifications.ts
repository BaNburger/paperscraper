import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
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

interface NotificationQueryOptions {
  enabled?: boolean
  poll?: boolean
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

export function useNotifications(limit = 20, options?: NotificationQueryOptions) {
  const queryClient = useQueryClient()
  const shouldPoll = options?.poll ?? true
  const isVisible = () =>
    typeof document === 'undefined' || document.visibilityState === 'visible'

  // Fetch full notifications payload only when needed (e.g., panel open)
  const notificationsQuery = useQuery({
    queryKey: queryKeys.notifications.list(limit),
    queryFn: () => notificationsApi.list({ page: 1, page_size: limit }),
    enabled: options?.enabled ?? true,
    staleTime: 1000 * 30, // 30 seconds
    refetchInterval: () =>
      shouldPoll && isVisible() ? 1000 * 60 : false,
  })

  // Lightweight unread count query for badge display (polls more frequently)
  const unreadCountQuery = useQuery({
    queryKey: queryKeys.notifications.unreadCount(),
    queryFn: () => notificationsApi.getUnreadCount(),
    staleTime: 1000 * 15, // 15 seconds
    refetchInterval: () =>
      shouldPoll && isVisible() ? 1000 * 30 : false,
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
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all() })
    },
  })

  // Mutation to mark all notifications as read
  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all() })
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
