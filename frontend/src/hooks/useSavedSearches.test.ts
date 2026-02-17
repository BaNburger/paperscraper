import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import React from 'react'

vi.mock('@/lib/api', () => ({
  savedSearchesApi: {
    list: vi.fn(),
    get: vi.fn(),
    getByShareToken: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    generateShareLink: vi.fn(),
    revokeShareLink: vi.fn(),
    run: vi.fn(),
  },
}))

import { savedSearchesApi } from '@/lib/api'
import {
  useSavedSearches,
  useSavedSearch,
  useSharedSearch,
  useCreateSavedSearch,
  useUpdateSavedSearch,
  useDeleteSavedSearch,
  useGenerateShareLink,
  useRevokeShareLink,
  useRunSavedSearch,
} from './useSavedSearches'

import type { SavedSearchListResponse, SavedSearch, SearchResponse } from '@/types'

const mockSavedSearch: SavedSearch = {
  id: 'ss-1',
  name: 'My Search',
  description: 'Test saved search',
  query: 'machine learning',
  mode: 'hybrid',
  filters: {},
  is_public: false,
  share_token: null,
  share_url: null,
  alert_enabled: false,
  alert_frequency: null,
  last_alert_at: null,
  semantic_description: null,
  target_project_id: null,
  target_project_name: null,
  auto_import_enabled: false,
  import_sources: [],
  max_import_per_run: 20,
  discovery_frequency: null,
  last_discovery_at: null,
  run_count: 5,
  last_run_at: '2026-01-15T10:00:00Z',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
  created_by: { id: 'user-1', email: 'test@example.com', full_name: 'Test User' },
}

const mockListResponse: SavedSearchListResponse = {
  items: [mockSavedSearch],
  total: 1,
  page: 1,
  page_size: 20,
  pages: 1,
}

const mockSearchResponse: SearchResponse = {
  results: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 0,
  query: 'machine learning',
  mode: 'hybrid',
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useSavedSearches', () => {
  it('fetches the saved searches list', async () => {
    vi.mocked(savedSearchesApi.list).mockResolvedValue(mockListResponse)

    const { result } = renderHook(() => useSavedSearches(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.list).toHaveBeenCalledWith(undefined)
    expect(result.current.data).toEqual(mockListResponse)
  })

  it('passes params to the list API call', async () => {
    vi.mocked(savedSearchesApi.list).mockResolvedValue(mockListResponse)
    const params = { page: 2, page_size: 10, include_public: true }

    const { result } = renderHook(() => useSavedSearches(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.list).toHaveBeenCalledWith(params)
  })
})

describe('useSavedSearch', () => {
  it('fetches a single saved search by id', async () => {
    vi.mocked(savedSearchesApi.get).mockResolvedValue(mockSavedSearch)

    const { result } = renderHook(() => useSavedSearch('ss-1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.get).toHaveBeenCalledWith('ss-1')
    expect(result.current.data).toEqual(mockSavedSearch)
  })

  it('is disabled when id is undefined', () => {
    const { result } = renderHook(() => useSavedSearch(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.fetchStatus).toBe('idle')
    expect(savedSearchesApi.get).not.toHaveBeenCalled()
  })
})

describe('useSharedSearch', () => {
  it('fetches a saved search by share token', async () => {
    vi.mocked(savedSearchesApi.getByShareToken).mockResolvedValue(mockSavedSearch)

    const { result } = renderHook(() => useSharedSearch('abc123'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.getByShareToken).toHaveBeenCalledWith('abc123')
    expect(result.current.data).toEqual(mockSavedSearch)
  })

  it('is disabled when share token is undefined', () => {
    const { result } = renderHook(() => useSharedSearch(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.fetchStatus).toBe('idle')
    expect(savedSearchesApi.getByShareToken).not.toHaveBeenCalled()
  })
})

describe('useCreateSavedSearch', () => {
  it('calls savedSearchesApi.create and invalidates the list cache on success', async () => {
    vi.mocked(savedSearchesApi.create).mockResolvedValue(mockSavedSearch)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useCreateSavedSearch(), { wrapper })

    await act(async () => {
      result.current.mutate({
        name: 'My Search',
        query: 'machine learning',
        mode: 'hybrid',
      })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.create).toHaveBeenCalledWith({
      name: 'My Search',
      query: 'machine learning',
      mode: 'hybrid',
    })
    expect(result.current.data).toEqual(mockSavedSearch)
  })
})

describe('useUpdateSavedSearch', () => {
  it('calls savedSearchesApi.update with id and data, then invalidates caches', async () => {
    const updatedSearch = { ...mockSavedSearch, name: 'Updated Search' }
    vi.mocked(savedSearchesApi.update).mockResolvedValue(updatedSearch)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useUpdateSavedSearch(), { wrapper })

    await act(async () => {
      result.current.mutate({
        id: 'ss-1',
        data: { name: 'Updated Search' },
      })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.update).toHaveBeenCalledWith('ss-1', { name: 'Updated Search' })
    expect(result.current.data).toEqual(updatedSearch)
  })
})

describe('useDeleteSavedSearch', () => {
  it('calls savedSearchesApi.delete and invalidates the list cache', async () => {
    vi.mocked(savedSearchesApi.delete).mockResolvedValue(undefined)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useDeleteSavedSearch(), { wrapper })

    await act(async () => {
      result.current.mutate('ss-1')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.delete).toHaveBeenCalledWith('ss-1')
  })
})

describe('useGenerateShareLink', () => {
  it('calls savedSearchesApi.generateShareLink and invalidates both caches', async () => {
    const shareResult = { share_token: 'tok-abc', share_url: 'https://app.test/shared/tok-abc' }
    vi.mocked(savedSearchesApi.generateShareLink).mockResolvedValue(shareResult)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useGenerateShareLink(), { wrapper })

    await act(async () => {
      result.current.mutate('ss-1')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.generateShareLink).toHaveBeenCalledWith('ss-1')
    expect(result.current.data).toEqual(shareResult)
  })
})

describe('useRevokeShareLink', () => {
  it('calls savedSearchesApi.revokeShareLink and invalidates both caches', async () => {
    vi.mocked(savedSearchesApi.revokeShareLink).mockResolvedValue(undefined)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useRevokeShareLink(), { wrapper })

    await act(async () => {
      result.current.mutate('ss-1')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.revokeShareLink).toHaveBeenCalledWith('ss-1')
  })
})

describe('useRunSavedSearch', () => {
  it('calls savedSearchesApi.run with id and params', async () => {
    vi.mocked(savedSearchesApi.run).mockResolvedValue(mockSearchResponse)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useRunSavedSearch(), { wrapper })

    const runParams = { page: 1, page_size: 10 }

    await act(async () => {
      result.current.mutate({ id: 'ss-1', params: runParams })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.run).toHaveBeenCalledWith('ss-1', runParams)
    expect(result.current.data).toEqual(mockSearchResponse)
  })

  it('calls savedSearchesApi.run without params when none are provided', async () => {
    vi.mocked(savedSearchesApi.run).mockResolvedValue(mockSearchResponse)

    const wrapper = createWrapper()
    const { result } = renderHook(() => useRunSavedSearch(), { wrapper })

    await act(async () => {
      result.current.mutate({ id: 'ss-1' })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(savedSearchesApi.run).toHaveBeenCalledWith('ss-1', undefined)
  })
})
