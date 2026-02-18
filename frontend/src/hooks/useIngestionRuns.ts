import { useCallback } from 'react'
import { papersApi } from '@/lib/api'

export interface IngestionSummaryResult {
  ingest_run_id: string
  status: 'completed' | 'completed_with_errors' | 'failed'
  papers_created: number
  papers_skipped: number
  errors: string[]
}

const TERMINAL_STATUSES = new Set(['completed', 'completed_with_errors', 'failed'])
const POLL_INTERVAL_MS = 1200
const POLL_TIMEOUT_MS = 3 * 60 * 1000

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

export function useIngestionRunPoller() {
  const waitForRun = useCallback(
    async (runId: string, timeoutMs = POLL_TIMEOUT_MS): Promise<IngestionSummaryResult> => {
      const startedAt = Date.now()

      while (Date.now() - startedAt < timeoutMs) {
        const run = await papersApi.getIngestionRun(runId)
        if (TERMINAL_STATUSES.has(run.status)) {
          const status = run.status as IngestionSummaryResult['status']
          const stats = run.stats ?? {
            papers_created: 0,
            papers_matched: 0,
            papers_failed: 0,
            source_records_inserted: 0,
            source_records_duplicates: 0,
            errors: [] as string[],
          }
          const statsErrors = stats.errors ?? []
          const skipped = stats.source_records_duplicates + stats.papers_matched
          const errors =
            statsErrors.length > 0
              ? statsErrors
              : status === 'failed' && run.error_message
                ? [run.error_message]
                : []
          return {
            ingest_run_id: runId,
            status,
            papers_created: stats.papers_created,
            papers_skipped: skipped,
            errors,
          }
        }
        await sleep(POLL_INTERVAL_MS)
      }

      return {
        ingest_run_id: runId,
        status: 'failed',
        papers_created: 0,
        papers_skipped: 0,
        errors: ['Timed out waiting for ingestion run completion'],
      }
    },
    []
  )

  return { waitForRun }
}
