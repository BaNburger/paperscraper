import { FileText, SearchX } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Pagination } from '@/components/ui/Pagination'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { PaperListItem } from '@/features/papers/list/PaperListItem'
import type { PaperListResponse } from '@/types'

type PapersListProps = {
  data: PaperListResponse | undefined
  isLoading: boolean
  error: unknown
  search: string
  page: number
  pageSize: number
  onOpenImport: () => void
  onClearSearch: () => void
  onPageChange: (page: number) => void
}

export function PapersList({
  data,
  isLoading,
  error,
  search,
  page,
  pageSize,
  onOpenImport,
  onClearSearch,
  onPageChange,
}: PapersListProps) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <SkeletonCard key={index} />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-destructive">
          {t('papers.loadFailed')}
        </CardContent>
      </Card>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <Card>
        <CardContent>
          {search ? (
            <EmptyState
              icon={<SearchX className="h-16 w-16" />}
              title={t('papers.noSearchResults')}
              description={t('papers.noSearchResultsDescription')}
              action={{
                label: t('papers.clearSearch'),
                onClick: onClearSearch,
              }}
            />
          ) : (
            <EmptyState
              icon={<FileText className="h-16 w-16" />}
              title={t('papers.noPapers')}
              description={t('papers.noPapersStartDescription')}
              action={{
                label: t('papers.importPapers'),
                onClick: onOpenImport,
              }}
            />
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <div className="space-y-4" data-testid="papers-list">
        {data.items.map((paper) => (
          <PaperListItem key={paper.id} paper={paper} />
        ))}
      </div>

      {data.pages > 1 && (
        <Pagination
          page={page}
          pages={data.pages}
          onPageChange={onPageChange}
          summary={t('papers.showingResults', {
            from: (page - 1) * pageSize + 1,
            to: Math.min(page * pageSize, data.total),
            total: data.total,
          })}
          previousLabel={t('common.previous')}
          nextLabel={t('common.next')}
          pageLabel={t('common.pageOf', { page, pages: data.pages })}
        />
      )}
    </>
  )
}
