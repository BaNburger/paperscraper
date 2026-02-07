import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { createElement } from 'react'
import {
  useAlerts,
  useAlert,
  useCreateAlert,
  useUpdateAlert,
  useDeleteAlert,
  useAlertResults,
  useTestAlert,
  useTriggerAlert,
} from './useAlerts'
import type {
  Alert,
  AlertListResponse,
  AlertResultListResponse,
  CreateAlertRequest,
  UpdateAlertRequest,
} from '@/types'

vi.mock('@/lib/api', () => ({
  alertsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getResults: vi.fn(),
    test: vi.fn(),
    trigger: vi.fn(),
  },
}))

import { alertsApi } from '@/lib/api'

const mockedAlertsApi = alertsApi as {
  list: ReturnType<typeof vi.fn>
  get: ReturnType<typeof vi.fn>
  create: ReturnType<typeof vi.fn>
  update: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
  getResults: ReturnType<typeof vi.fn>
  test: ReturnType<typeof vi.fn>
  trigger: ReturnType<typeof vi.fn>
}

const mockAlert: Alert = {
  id: 'alert-1',
  name: 'Test Alert',
  description: 'A test alert',
  channel: 'email',
  frequency: 'daily',
  min_results: 1,
  is_active: true,
  last_triggered_at: null,
  trigger_count: 0,
  saved_search: { id: 'ss-1', name: 'My Search', query: 'machine learning' },
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockAlertListResponse: AlertListResponse = {
  items: [mockAlert],
  total: 1,
  page: 1,
  page_size: 20,
  pages: 1,
}

const mockAlertResultListResponse: AlertResultListResponse = {
  items: [
    {
      id: 'result-1',
      alert_id: 'alert-1',
      status: 'sent',
      papers_found: 5,
      new_papers: 3,
      paper_ids: ['p-1', 'p-2', 'p-3'],
      delivered_at: '2026-01-02T00:00:00Z',
      error_message: null,
      created_at: '2026-01-02T00:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  pages: 1,
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useAlerts', () => {
  it('fetches the alerts list', async () => {
    mockedAlertsApi.list.mockResolvedValueOnce(mockAlertListResponse)

    const { result } = renderHook(() => useAlerts(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.list).toHaveBeenCalledWith(undefined)
    expect(result.current.data).toEqual(mockAlertListResponse)
  })

  it('passes params to the list API call', async () => {
    mockedAlertsApi.list.mockResolvedValueOnce(mockAlertListResponse)
    const params = { page: 2, page_size: 10, active_only: true }

    const { result } = renderHook(() => useAlerts(params), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.list).toHaveBeenCalledWith(params)
  })
})

describe('useAlert', () => {
  it('fetches a single alert by ID', async () => {
    mockedAlertsApi.get.mockResolvedValueOnce(mockAlert)

    const { result } = renderHook(() => useAlert('alert-1'), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.get).toHaveBeenCalledWith('alert-1')
    expect(result.current.data).toEqual(mockAlert)
  })

  it('is disabled when id is undefined', () => {
    const { result } = renderHook(() => useAlert(undefined), { wrapper: createWrapper() })

    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedAlertsApi.get).not.toHaveBeenCalled()
  })
})

describe('useCreateAlert', () => {
  it('calls create API and invalidates alerts cache on success', async () => {
    const newAlert: Alert = { ...mockAlert, id: 'alert-2', name: 'New Alert' }
    mockedAlertsApi.create.mockResolvedValueOnce(newAlert)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useCreateAlert(), { wrapper })

    const createData: CreateAlertRequest = {
      name: 'New Alert',
      saved_search_id: 'ss-1',
      channel: 'email',
      frequency: 'daily',
      min_results: 1,
    }

    await act(async () => {
      result.current.mutate(createData)
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.create).toHaveBeenCalledWith(createData)
    expect(result.current.data).toEqual(newAlert)
  })
})

describe('useUpdateAlert', () => {
  it('calls update API with id and data, and invalidates both caches', async () => {
    const updatedAlert: Alert = { ...mockAlert, name: 'Updated Alert' }
    mockedAlertsApi.update.mockResolvedValueOnce(updatedAlert)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useUpdateAlert(), { wrapper })

    const updateData: UpdateAlertRequest = { name: 'Updated Alert', is_active: false }

    await act(async () => {
      result.current.mutate({ id: 'alert-1', data: updateData })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.update).toHaveBeenCalledWith('alert-1', updateData)
    expect(result.current.data).toEqual(updatedAlert)
  })
})

describe('useDeleteAlert', () => {
  it('calls delete API and invalidates alerts cache on success', async () => {
    mockedAlertsApi.delete.mockResolvedValueOnce(undefined)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useDeleteAlert(), { wrapper })

    await act(async () => {
      result.current.mutate('alert-1')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.delete).toHaveBeenCalledWith('alert-1')
  })
})

describe('useAlertResults', () => {
  it('fetches alert results by alertId', async () => {
    mockedAlertsApi.getResults.mockResolvedValueOnce(mockAlertResultListResponse)

    const { result } = renderHook(() => useAlertResults('alert-1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.getResults).toHaveBeenCalledWith('alert-1', undefined)
    expect(result.current.data).toEqual(mockAlertResultListResponse)
  })

  it('passes pagination params to getResults', async () => {
    mockedAlertsApi.getResults.mockResolvedValueOnce(mockAlertResultListResponse)
    const params = { page: 2, page_size: 5 }

    const { result } = renderHook(() => useAlertResults('alert-1', params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.getResults).toHaveBeenCalledWith('alert-1', params)
  })

  it('is disabled when alertId is undefined', () => {
    const { result } = renderHook(() => useAlertResults(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedAlertsApi.getResults).not.toHaveBeenCalled()
  })
})

describe('useTestAlert', () => {
  it('calls test API and does not invalidate any cache', async () => {
    const testResult = {
      success: true,
      message: 'Test completed',
      papers_found: 3,
      sample_papers: [{ id: 'p-1', title: 'Sample Paper' }],
    }
    mockedAlertsApi.test.mockResolvedValueOnce(testResult)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useTestAlert(), { wrapper })

    await act(async () => {
      result.current.mutate('alert-1')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.test).toHaveBeenCalledWith('alert-1')
    expect(result.current.data).toEqual(testResult)
  })
})

describe('useTriggerAlert', () => {
  it('calls trigger API and invalidates alert and results caches', async () => {
    mockedAlertsApi.trigger.mockResolvedValueOnce(undefined)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useTriggerAlert(), { wrapper })

    await act(async () => {
      result.current.mutate('alert-1')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedAlertsApi.trigger).toHaveBeenCalledWith('alert-1')
  })
})
