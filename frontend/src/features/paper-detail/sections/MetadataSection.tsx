import { useTranslation } from 'react-i18next'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import type { PaperDetail } from '@/types'

type MetadataSectionProps = {
  show: boolean
  paper: PaperDetail
}

export function MetadataSection({ show, paper }: MetadataSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('papers.metadata')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {paper.doi && (
          <div>
            <p className="text-xs text-muted-foreground">DOI</p>
            <p className="text-sm font-mono">{paper.doi}</p>
          </div>
        )}
        {paper.volume && (
          <div>
            <p className="text-xs text-muted-foreground">{t('papers.volumeIssue')}</p>
            <p className="text-sm">
              {paper.volume}
              {paper.issue && ` (${paper.issue})`}
              {paper.pages && `, pp. ${paper.pages}`}
            </p>
          </div>
        )}
        {paper.citations_count !== null && (
          <div>
            <p className="text-xs text-muted-foreground">{t('papers.citations')}</p>
            <p className="text-sm">{paper.citations_count}</p>
          </div>
        )}
        {paper.references_count !== null && (
          <div>
            <p className="text-xs text-muted-foreground">{t('papers.references')}</p>
            <p className="text-sm">{paper.references_count}</p>
          </div>
        )}
        {paper.keywords.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">{t('papers.keywords')}</p>
            <div className="flex flex-wrap gap-1">
              {paper.keywords.map((keyword, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {keyword}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
