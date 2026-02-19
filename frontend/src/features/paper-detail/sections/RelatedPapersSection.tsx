import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import type { SimilarPapersResponse } from '@/types'

type RelatedPapersSectionProps = {
  show: boolean
  expanded: boolean
  onToggle: () => void
  loading: boolean
  data: SimilarPapersResponse | undefined
  hasEmbedding: boolean
}

export function RelatedPapersSection({
  show,
  expanded,
  onToggle,
  loading,
  data,
  hasEmbedding,
}: RelatedPapersSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <button className="flex w-full items-center justify-between text-left" onClick={onToggle}>
          <div>
            <CardTitle>{t('papers.similarPapers')}</CardTitle>
            <CardDescription>{t('papers.similarPapersDescription')}</CardDescription>
          </div>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </CardHeader>
      {expanded && (
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : !data?.similar_papers?.length ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              {hasEmbedding ? t('papers.noSimilarPapers') : t('papers.generateEmbedding')}
            </p>
          ) : (
            <div className="space-y-3">
              {data.similar_papers.map((result) => (
                <Link
                  key={result.id}
                  to={`/papers/${result.id}`}
                  className="block rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                >
                  <p className="text-sm font-medium line-clamp-2">{result.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t('papers.similarity', { value: (result.similarity_score * 100).toFixed(0) })}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
