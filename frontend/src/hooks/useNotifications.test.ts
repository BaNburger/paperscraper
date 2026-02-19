import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement, type ReactNode } from 'react'
import { useNotifications } from './useNotifications'
import type { NotificationItem, NotificationListResponse } from '@/types'

vi.mock('@/api', () => ({
  notificationsApi: {
    list: vi.fn(),
    getUnreadCount: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
  },
}))

import { notificationsApi } from '@/api'

const mockedApi = notificationsApi as {
  list: ReturnType<typeof vi.fn>
  getUnreadCount: ReturnType<typeof vi.fn>
  markAsRead: ReturnType<typeof vi.fn>
  markAllAsRead: ReturnType<typeof vi.fn>
}

// --- Factories ---

function createNotificationItem(overrides: Partial<NotificationItem> = {}): NotificationItem {
  return {
    id: 'notif-1',
    type: 'alert',
    title: 'Alert: ML Papers',
    message: 'Found 3 new papers (10 total)',
    is_read: false,
    resource_type: 'alert',
    resource_id: 'alert-1',
    created_at: '2026-01-15T12:00:00Z',
    ...overrides,
  }
}

function createListResponse(
  items: NotificationItem[],
  unread_count?: number,
): NotificationListResponse {
  return {
    items,
    total: items.length,
    page: 1,
    page_size: 20,
    pages: 1,
    unread_count: unread_count ?? items.filter((i) => !i.is_read).length,
  }
}

// --- Wrapper ---

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  })
  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

// --- Tests ---

describe('useNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.getUnreadCount.mockResolvedValue({ unread_count: 0 })
  })

  it('returns empty notifications when none exist', async () => {
    mockedApi.list.mockResolvedValue(createListResponse([]))

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.notifications).toEqual([])
    expect(result.current.unreadCount).toBe(0)
  })

  it('returns notifications from backend API', async () => {
    const item = createNotificationItem({
      id: 'notif-1',
      type: 'alert',
      title: 'Alert: ML Papers',
      message: 'Found 3 new papers',
      is_read: false,
      resource_type: 'alert',
      resource_id: 'alert-1',
    })

    mockedApi.list.mockResolvedValue(createListResponse([item], 1))
    mockedApi.getUnreadCount.mockResolvedValue({ unread_count: 1 })

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.notifications.length).toBe(1)
    })

    const notification = result.current.notifications[0]
    expect(notification.id).toBe('notif-1')
    expect(notification.type).toBe('alert')
    expect(notification.title).toBe('Alert: ML Papers')
    expect(notification.message).toBe('Found 3 new papers')
    expect(notification.isRead).toBe(false)
    expect(notification.resourceType).toBe('alert')
    expect(notification.resourceId).toBe('alert-1')
  })

  it('maps snake_case backend fields to camelCase', async () => {
    const item = createNotificationItem({
      is_read: true,
      resource_type: 'badge',
      resource_id: 'badge-123',
      created_at: '2026-01-20T08:00:00Z',
    })

    mockedApi.list.mockResolvedValue(createListResponse([item], 0))

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.notifications.length).toBe(1)
    })

    const notification = result.current.notifications[0]
    expect(notification.isRead).toBe(true)
    expect(notification.resourceType).toBe('badge')
    expect(notification.resourceId).toBe('badge-123')
    expect(notification.timestamp).toBe('2026-01-20T08:00:00Z')
  })

  it('counts unread notifications from backend', async () => {
    const items = [
      createNotificationItem({ id: 'n1', is_read: false }),
      createNotificationItem({ id: 'n2', is_read: true }),
      createNotificationItem({ id: 'n3', is_read: false }),
    ]

    mockedApi.list.mockResolvedValue(createListResponse(items, 2))
    mockedApi.getUnreadCount.mockResolvedValue({ unread_count: 2 })

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.notifications.length).toBe(3)
    })

    expect(result.current.unreadCount).toBe(2)
  })

  it('markAsRead calls backend API', async () => {
    const item = createNotificationItem({ id: 'notif-1', is_read: false })
    mockedApi.list.mockResolvedValue(createListResponse([item], 1))
    mockedApi.getUnreadCount.mockResolvedValue({ unread_count: 1 })
    mockedApi.markAsRead.mockResolvedValue({ updated: 1 })

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.notifications.length).toBe(1)
    })

    await act(async () => {
      result.current.markAsRead('notif-1')
    })

    expect(mockedApi.markAsRead).toHaveBeenCalledWith(['notif-1'])
  })

  it('markAllAsRead calls backend API', async () => {
    const items = [
      createNotificationItem({ id: 'n1', is_read: false }),
      createNotificationItem({ id: 'n2', is_read: false }),
    ]
    mockedApi.list.mockResolvedValue(createListResponse(items, 2))
    mockedApi.getUnreadCount.mockResolvedValue({ unread_count: 2 })
    mockedApi.markAllAsRead.mockResolvedValue({ updated: 2 })

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.notifications.length).toBe(2)
    })

    await act(async () => {
      result.current.markAllAsRead()
    })

    expect(mockedApi.markAllAsRead).toHaveBeenCalled()
  })

  it('handles badge notification type', async () => {
    const item = createNotificationItem({
      id: 'badge-notif-1',
      type: 'badge',
      title: 'Badge Earned: First Import',
      message: 'Congratulations! You earned the bronze First Import badge (+10 points)',
      resource_type: 'badge',
      resource_id: 'badge-42',
    })

    mockedApi.list.mockResolvedValue(createListResponse([item], 1))
    mockedApi.getUnreadCount.mockResolvedValue({ unread_count: 1 })

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.notifications.length).toBe(1)
    })

    const notification = result.current.notifications[0]
    expect(notification.type).toBe('badge')
    expect(notification.title).toBe('Badge Earned: First Import')
    expect(notification.resourceType).toBe('badge')
  })

  it('passes limit parameter to API as page_size', async () => {
    mockedApi.list.mockResolvedValue(createListResponse([], 0))

    renderHook(() => useNotifications(5), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(mockedApi.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 5,
      })
    })
  })

  it('handles API errors gracefully', async () => {
    mockedApi.list.mockRejectedValue(new Error('Network error'))
    mockedApi.getUnreadCount.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useNotifications(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.notifications).toEqual([])
    expect(result.current.unreadCount).toBe(0)
  })
})
