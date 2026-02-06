import { useQuery } from '@tanstack/react-query'
import { analyticsApi, exportApi } from '@/lib/api'
import type { ExportFormat } from '@/types'

const ANALYTICS_STALE_TIME = 60000 // 1 minute

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: () => analyticsApi.getDashboardSummary(),
    staleTime: ANALYTICS_STALE_TIME,
  })
}

export function useTeamOverview() {
  return useQuery({
    queryKey: ['analytics', 'team'],
    queryFn: () => analyticsApi.getTeamOverview(),
    staleTime: ANALYTICS_STALE_TIME,
  })
}

export function usePaperAnalytics(days = 90) {
  return useQuery({
    queryKey: ['analytics', 'papers', days],
    queryFn: () => analyticsApi.getPaperAnalytics({ days }),
    staleTime: ANALYTICS_STALE_TIME,
  })
}

export function useFunnelAnalytics(params?: {
  project_id?: string
  start_date?: string
  end_date?: string
}) {
  return useQuery({
    queryKey: ['analytics', 'funnel', params],
    queryFn: () => analyticsApi.getFunnelAnalytics(params),
    staleTime: ANALYTICS_STALE_TIME,
  })
}

export function useBenchmarks() {
  return useQuery({
    queryKey: ['analytics', 'benchmarks'],
    queryFn: () => analyticsApi.getBenchmarks(),
    staleTime: ANALYTICS_STALE_TIME,
  })
}

function getExportTimestamp(): string {
  return new Date().toISOString().slice(0, 10)
}

const FILE_EXTENSIONS: Record<ExportFormat, string> = {
  csv: 'csv',
  bibtex: 'bib',
  pdf: 'txt',
}

export function useExportCsv() {
  return async (paperIds?: string[], includeScores = true, includeAuthors = true) => {
    const blob = await exportApi.exportCsv({
      paper_ids: paperIds,
      include_scores: includeScores,
      include_authors: includeAuthors,
    })
    exportApi.downloadFile(blob, `papers_export_${getExportTimestamp()}.csv`)
  }
}

export function useExportBibtex() {
  return async (paperIds?: string[], includeAbstract = true) => {
    const blob = await exportApi.exportBibtex({
      paper_ids: paperIds,
      include_abstract: includeAbstract,
    })
    exportApi.downloadFile(blob, `papers_export_${getExportTimestamp()}.bib`)
  }
}

export function useExportPdf() {
  return async (paperIds?: string[], includeScores = true, includeAbstract = true) => {
    const blob = await exportApi.exportPdf({
      paper_ids: paperIds,
      include_scores: includeScores,
      include_abstract: includeAbstract,
    })
    exportApi.downloadFile(blob, `papers_report_${getExportTimestamp()}.txt`)
  }
}

export function useBatchExport() {
  return async (
    paperIds: string[],
    format: ExportFormat,
    options?: { include_scores?: boolean; include_authors?: boolean }
  ) => {
    const blob = await exportApi.batchExport(paperIds, format, options)
    exportApi.downloadFile(blob, `papers_export_${getExportTimestamp()}.${FILE_EXTENSIONS[format]}`)
  }
}
