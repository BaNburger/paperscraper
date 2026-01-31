import { useQuery } from '@tanstack/react-query'
import { analyticsApi, exportApi } from '@/lib/api'
import type { ExportFormat } from '@/types'

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: () => analyticsApi.getDashboardSummary(),
    staleTime: 60000, // 1 minute
  })
}

export function useTeamOverview() {
  return useQuery({
    queryKey: ['analytics', 'team'],
    queryFn: () => analyticsApi.getTeamOverview(),
    staleTime: 60000,
  })
}

export function usePaperAnalytics(days: number = 90) {
  return useQuery({
    queryKey: ['analytics', 'papers', days],
    queryFn: () => analyticsApi.getPaperAnalytics({ days }),
    staleTime: 60000,
  })
}

// Export helpers
export function useExportCsv() {
  return async (paperIds?: string[], includeScores = true, includeAuthors = true) => {
    const blob = await exportApi.exportCsv({
      paper_ids: paperIds,
      include_scores: includeScores,
      include_authors: includeAuthors,
    })
    const timestamp = new Date().toISOString().slice(0, 10)
    exportApi.downloadFile(blob, `papers_export_${timestamp}.csv`)
  }
}

export function useExportBibtex() {
  return async (paperIds?: string[], includeAbstract = true) => {
    const blob = await exportApi.exportBibtex({
      paper_ids: paperIds,
      include_abstract: includeAbstract,
    })
    const timestamp = new Date().toISOString().slice(0, 10)
    exportApi.downloadFile(blob, `papers_export_${timestamp}.bib`)
  }
}

export function useExportPdf() {
  return async (paperIds?: string[], includeScores = true, includeAbstract = true) => {
    const blob = await exportApi.exportPdf({
      paper_ids: paperIds,
      include_scores: includeScores,
      include_abstract: includeAbstract,
    })
    const timestamp = new Date().toISOString().slice(0, 10)
    exportApi.downloadFile(blob, `papers_report_${timestamp}.txt`)
  }
}

export function useBatchExport() {
  return async (
    paperIds: string[],
    format: ExportFormat,
    options?: { include_scores?: boolean; include_authors?: boolean }
  ) => {
    const blob = await exportApi.batchExport(paperIds, format, options)
    const timestamp = new Date().toISOString().slice(0, 10)
    const extensions: Record<ExportFormat, string> = {
      csv: 'csv',
      bibtex: 'bib',
      pdf: 'txt',
    }
    exportApi.downloadFile(blob, `papers_export_${timestamp}.${extensions[format]}`)
  }
}
