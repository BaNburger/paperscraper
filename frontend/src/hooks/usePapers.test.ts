import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement, type ReactNode } from 'react'
import { queryKeys } from '@/config/queryKeys'

import {
  usePapers,
  usePaper,
  usePaperScore,
  useDeletePaper,
  useIngestByDoi,
  useIngestFromOpenAlex,
  useScorePaper,
} from './usePapers'

// ---- Mocks ----

vi.mock('@/lib/api', () => ({
  papersApi: {
    list: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
    ingestByDoi: vi.fn(),
    ingestFromOpenAlex: vi.fn(),
    ingestFromPubMed: vi.fn(),
    ingestFromArxiv: vi.fn(),
    uploadPdf: vi.fn(),
    generatePitch: vi.fn(),
    generateSimplifiedAbstract: vi.fn(),
    ingestFromSemanticScholar: vi.fn(),
    getRelatedPatents: vi.fn(),
    getCitationGraph: vi.fn(),
    getIngestionRun: vi.fn(),
  },
  scoringApi: {
    scorePaper: vi.fn(),
    getLatestScore: vi.fn(),
  },
}))

import { papersApi, scoringApi } from '@/lib/api'

// ---- Helpers ----

const mockedPapersApi = papersApi as unknown as {
  list: ReturnType<typeof vi.fn>
  get: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
  ingestByDoi: ReturnType<typeof vi.fn>
  ingestFromOpenAlex: ReturnType<typeof vi.fn>
  getIngestionRun: ReturnType<typeof vi.fn>
}

const mockedScoringApi = scoringApi as unknown as {
  scorePaper: ReturnType<typeof vi.fn>
  getLatestScore: ReturnType<typeof vi.fn>
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

// ---- Test data ----

const mockPaperListResponse = {
  items: [
    { id: '1', title: 'Paper A', doi: '10.1234/a' },
    { id: '2', title: 'Paper B', doi: '10.1234/b' },
  ],
  total: 2,
  page: 1,
  pages: 1,
}

const mockPaperDetail = {
  id: 'paper-123',
  title: 'Quantum Computing Advances',
  doi: '10.1234/qc',
  abstract: 'A study on quantum computing.',
  source: 'openalex',
}

const mockPaperScore = {
  paper_id: 'paper-123',
  novelty: 8.5,
  ip_potential: 7.0,
  marketability: 6.5,
  feasibility: 9.0,
  commercialization: 5.5,
  team_readiness: 7.5,
  overall_score: 7.3,
  confidence: 0.85,
}

const mockScoreResponse = {
  paper_id: 'paper-123',
  scores: mockPaperScore,
  model_version: 'v1',
}

const mockCompletedIngestionRun = {
  id: 'run-123',
  status: 'completed',
  stats: {
    papers_created: 5,
    source_records_duplicates: 1,
    papers_matched: 1,
    errors: [] as string[],
  },
  error_message: null,
}

// ---- Tests ----

beforeEach(() => {
  vi.clearAllMocks()
})

describe('usePapers', () => {
  it('fetches papers list with the provided params', async () => {
    mockedPapersApi.list.mockResolvedValueOnce(mockPaperListResponse)

    const params = { page: 1, page_size: 20, search: 'quantum' }
    const { result } = renderHook(() => usePapers(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedPapersApi.list).toHaveBeenCalledWith(params)
    expect(result.current.data).toEqual(mockPaperListResponse)
  })

  it('passes empty params when no filters are provided', async () => {
    mockedPapersApi.list.mockResolvedValueOnce(mockPaperListResponse)

    const params = {}
    const { result } = renderHook(() => usePapers(params), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedPapersApi.list).toHaveBeenCalledWith({})
  })

  it('exposes error state when the API call fails', async () => {
    mockedPapersApi.list.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => usePapers({ page: 1 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('Network error')
  })
})

describe('usePaper', () => {
  it('fetches a single paper by ID', async () => {
    mockedPapersApi.get.mockResolvedValueOnce(mockPaperDetail)

    const { result } = renderHook(() => usePaper('paper-123'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedPapersApi.get).toHaveBeenCalledWith('paper-123')
    expect(result.current.data).toEqual(mockPaperDetail)
  })

  it('does not fetch when id is an empty string', async () => {
    const { result } = renderHook(() => usePaper(''), {
      wrapper: createWrapper(),
    })

    // The query should remain idle/pending since enabled is false
    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedPapersApi.get).not.toHaveBeenCalled()
  })

  it('starts fetching when id transitions from empty to a valid value', async () => {
    mockedPapersApi.get.mockResolvedValueOnce(mockPaperDetail)

    let paperId = ''
    const { result, rerender } = renderHook(() => usePaper(paperId), {
      wrapper: createWrapper(),
    })

    // Initially idle
    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedPapersApi.get).not.toHaveBeenCalled()

    // Update to valid ID
    paperId = 'paper-123'
    rerender()

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedPapersApi.get).toHaveBeenCalledWith('paper-123')
  })
})

describe('usePaperScore', () => {
  it('fetches the latest score for a paper', async () => {
    mockedScoringApi.getLatestScore.mockResolvedValueOnce(mockPaperScore)

    const { result } = renderHook(() => usePaperScore('paper-123'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedScoringApi.getLatestScore).toHaveBeenCalledWith('paper-123')
    expect(result.current.data).toEqual(mockPaperScore)
  })

  it('does not fetch when paperId is an empty string', async () => {
    const { result } = renderHook(() => usePaperScore(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.fetchStatus).toBe('idle')
    expect(mockedScoringApi.getLatestScore).not.toHaveBeenCalled()
  })
})

describe('useDeletePaper', () => {
  it('calls papersApi.delete with the provided ID', async () => {
    mockedPapersApi.delete.mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useDeletePaper(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate('paper-to-delete')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedPapersApi.delete).toHaveBeenCalledWith('paper-to-delete')
  })

  it('invalidates papers queries on successful deletion', async () => {
    mockedPapersApi.delete.mockResolvedValueOnce(undefined)

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
      },
    })
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children)

    const { result } = renderHook(() => useDeletePaper(), { wrapper })

    await act(async () => {
      result.current.mutate('paper-to-delete')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: queryKeys.papers.listRoot() })
  })
})

describe('useIngestByDoi', () => {
  it('calls papersApi.ingestByDoi with the DOI string', async () => {
    const mockPaper = { id: 'new-paper', title: 'New Discovery', doi: '10.5678/xyz' }
    mockedPapersApi.ingestByDoi.mockResolvedValueOnce(mockPaper)

    const { result } = renderHook(() => useIngestByDoi(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate('10.5678/xyz')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedPapersApi.ingestByDoi).toHaveBeenCalledWith('10.5678/xyz')
    expect(result.current.data).toEqual(mockPaper)
  })

  it('invalidates papers queries on successful ingestion', async () => {
    mockedPapersApi.ingestByDoi.mockResolvedValueOnce({ id: 'new-paper' })

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
      },
    })
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children)

    const { result } = renderHook(() => useIngestByDoi(), { wrapper })

    await act(async () => {
      result.current.mutate('10.5678/xyz')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: queryKeys.papers.listRoot() })
  })
})

describe('useIngestFromOpenAlex', () => {
  it('calls papersApi.ingestFromOpenAlex with query and max_results', async () => {
    mockedPapersApi.ingestFromOpenAlex.mockResolvedValueOnce({ ingest_run_id: 'run-123' })
    mockedPapersApi.getIngestionRun.mockResolvedValueOnce(mockCompletedIngestionRun)

    const params = { query: 'machine learning', max_results: 10 }
    const { result } = renderHook(() => useIngestFromOpenAlex(), {
      wrapper: createWrapper(),
    })

    let mutationResult: unknown
    await act(async () => {
      mutationResult = await result.current.mutateAsync(params)
    })

    expect(mockedPapersApi.ingestFromOpenAlex).toHaveBeenCalledWith(params)
    expect(mockedPapersApi.getIngestionRun).toHaveBeenCalledWith('run-123')
    expect(mutationResult).toEqual({
      ingest_run_id: 'run-123',
      status: 'completed',
      papers_created: 5,
      papers_skipped: 2,
      errors: [],
    })
  })

  it('calls papersApi.ingestFromOpenAlex with only query (no max_results)', async () => {
    mockedPapersApi.ingestFromOpenAlex.mockResolvedValueOnce({ ingest_run_id: 'run-456' })
    mockedPapersApi.getIngestionRun.mockResolvedValueOnce({
      ...mockCompletedIngestionRun,
      id: 'run-456',
    })

    const params = { query: 'CRISPR' }
    const { result } = renderHook(() => useIngestFromOpenAlex(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      await result.current.mutateAsync(params)
    })

    expect(mockedPapersApi.ingestFromOpenAlex).toHaveBeenCalledWith({ query: 'CRISPR' })
    expect(mockedPapersApi.getIngestionRun).toHaveBeenCalledWith('run-456')
  })
})

describe('useScorePaper', () => {
  it('calls scoringApi.scorePaper with the paper ID', async () => {
    mockedScoringApi.scorePaper.mockResolvedValueOnce(mockScoreResponse)

    const { result } = renderHook(() => useScorePaper(), {
      wrapper: createWrapper(),
    })

    await act(async () => {
      result.current.mutate('paper-123')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(mockedScoringApi.scorePaper).toHaveBeenCalledWith('paper-123')
    expect(result.current.data).toEqual(mockScoreResponse)
  })

  it('invalidates both score and detail paper queries on success', async () => {
    mockedScoringApi.scorePaper.mockResolvedValueOnce(mockScoreResponse)

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
      },
    })
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children)

    const { result } = renderHook(() => useScorePaper(), { wrapper })

    await act(async () => {
      result.current.mutate('paper-123')
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: queryKeys.papers.score('paper-123') })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: queryKeys.papers.detail('paper-123') })
  })
})
