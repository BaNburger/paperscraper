import { memo } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import { formatDate, truncate } from '@/lib/utils'
import type { Paper } from '@/types'

type PaperListItemProps = {
  paper: Paper
}

export const PaperListItem = memo(function PaperListItem({ paper }: PaperListItemProps) {
  const { t } = useTranslation()

  return (
    <Link key={paper.id} to={`/papers/${paper.id}`} data-testid={`paper-list-item-${paper.id}`}>
      <Card variant="interactive" className="hover:bg-muted/50">
        <CardContent className="py-4">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h3 className="font-medium line-clamp-2">{paper.title}</h3>
              {paper.one_line_pitch && (
                <p className="text-sm font-medium text-primary mt-1 italic">
                  "{paper.one_line_pitch}"
                </p>
              )}
              <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                {truncate(paper.abstract ?? t('papers.noAbstract'), 200)}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <Badge variant="outline">{paper.source}</Badge>
                {paper.journal && <span className="text-xs text-muted-foreground">{paper.journal}</span>}
                {paper.publication_date && (
                  <span className="text-xs text-muted-foreground">{formatDate(paper.publication_date)}</span>
                )}
                {paper.doi && <span className="text-xs text-muted-foreground">DOI: {paper.doi}</span>}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 shrink-0">
              {paper.has_pdf && <Badge variant="secondary">PDF</Badge>}
              {paper.has_embedding && <Badge variant="secondary">Embedded</Badge>}
              {paper.citations_count != null && paper.citations_count > 0 && (
                <span className="text-xs text-muted-foreground">
                  {t('papers.citationsCount', { count: paper.citations_count })}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
})
