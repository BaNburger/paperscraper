import { useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { alertsApi } from '@/lib/api'
import type { AlertResult, Alert } from '@/types'

export interface Notification {
  id: string
  alertId: string
  alertName: string
  type: 'alert' | 'badge' | 'system'
  title: string
  description: string
  timestamp: string
  isRead: boolean
  papersFound?: number
  newPapers?: number
  paperIds?: string[]
}

// Store read notification IDs in localStorage
const READ_NOTIFICATIONS_KEY = 'paper_scraper_read_notifications'

function getReadNotificationIds(): Set<string> {
  try {
    const stored = localStorage.getItem(READ_NOTIFICATIONS_KEY)
    return new Set(stored ? JSON.parse(stored) : [])
  } catch {
    return new Set()
  }
}

function setReadNotificationIds(ids: Set<string>): void {
  try {
    localStorage.setItem(READ_NOTIFICATIONS_KEY, JSON.stringify([...ids]))
  } catch {
    // Ignore storage errors
  }
}

function alertResultToNotification(
  result: AlertResult,
  alert: Alert
): Notification {
  const readIds = getReadNotificationIds()
  return {
    id: result.id,
    alertId: result.alert_id,
    alertName: alert.name,
    type: 'alert',
    title: `Alert: ${alert.name}`,
    description:
      result.status === 'sent'
        ? `Found ${result.new_papers} new papers (${result.papers_found} total)`
        : result.status === 'failed'
          ? `Alert failed: ${result.error_message || 'Unknown error'}`
          : `Alert ${result.status}`,
    timestamp: result.created_at,
    isRead: readIds.has(result.id),
    papersFound: result.papers_found,
    newPapers: result.new_papers,
    paperIds: result.paper_ids,
  }
}

export function useNotifications(limit = 20) {
  const queryClient = useQueryClient()

  // Fetch all alerts to get their names
  const alertsQuery = useQuery({
    queryKey: ['alerts', 'list'],
    queryFn: () => alertsApi.list({ page_size: 100 }),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  // For each alert, we'll fetch its recent results
  // This is a simplified approach - in a production app, you'd have
  // a dedicated notifications endpoint
  const alerts = alertsQuery.data?.items ?? []

  // Memoize alert IDs to prevent query key instability (new array on each render)
  const alertIds = useMemo(() => alerts.map((a) => a.id), [alerts])

  // Fetch results for all alerts in parallel
  const resultsQueries = useQuery({
    queryKey: ['notifications', 'all', alertIds],
    queryFn: async () => {
      if (alerts.length === 0) return []

      // Fetch results for all alerts in parallel (limit to 10 alerts)
      const resultsPromises = alerts.slice(0, 10).map((alert) =>
        alertsApi
          .getResults(alert.id, { page: 1, page_size: 5 })
          .then((response) =>
            response.items.map((result) => alertResultToNotification(result, alert))
          )
          .catch(() => [] as Notification[])
      )

      const results = await Promise.all(resultsPromises)
      const allNotifications = results.flat()

      // Sort by timestamp, newest first
      return allNotifications
        .sort(
          (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        )
        .slice(0, limit)
    },
    enabled: alerts.length > 0,
    staleTime: 1000 * 60, // 1 minute
  })

  const notifications = resultsQueries.data ?? []
  const unreadCount = notifications.filter((n) => !n.isRead).length

  // Mutation to mark notifications as read
  const markAsReadMutation = useMutation({
    mutationFn: async (notificationIds: string[]) => {
      const readIds = getReadNotificationIds()
      notificationIds.forEach((id) => readIds.add(id))
      setReadNotificationIds(readIds)
      return notificationIds
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllAsRead = () => {
    const ids = notifications.map((n) => n.id)
    markAsReadMutation.mutate(ids)
  }

  const markAsRead = (notificationId: string) => {
    markAsReadMutation.mutate([notificationId])
  }

  return {
    notifications,
    unreadCount,
    isLoading: alertsQuery.isLoading || resultsQueries.isLoading,
    isError: alertsQuery.isError || resultsQueries.isError,
    markAsRead,
    markAllAsRead,
    refetch: () => {
      alertsQuery.refetch()
      resultsQueries.refetch()
    },
  }
}
