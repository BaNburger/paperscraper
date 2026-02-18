import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/components/ui/Button'

interface PaginationProps {
  page: number
  pages: number
  onPageChange: (page: number) => void
  summary?: ReactNode
  previousLabel?: string
  nextLabel?: string
  pageLabel?: string
}

export function Pagination({
  page,
  pages,
  onPageChange,
  summary,
  previousLabel = 'Previous',
  nextLabel = 'Next',
  pageLabel,
}: PaginationProps) {
  if (pages <= 1) return null

  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-muted-foreground">{summary}</div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          <ChevronLeft className="h-4 w-4" />
          {previousLabel}
        </Button>
        <span className="text-sm">{pageLabel ?? `Page ${page} of ${pages}`}</span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
        >
          {nextLabel}
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
