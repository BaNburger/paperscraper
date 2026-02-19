import DOMPurify from 'dompurify'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { BookOpen, Calendar, ExternalLink, Search, Users, X } from 'lucide-react'
import { usePaper } from '@/hooks'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/lib/utils'
import type { SearchResultItem } from '@/types'
import { ScoreCard } from '@/features/search/components/ScoreCard'
import { getHighlightSnippet, SEARCH_SANITIZE_CONFIG } from '@/features/search/utils'

type PreviewPanelProps = {
  selectedResult: SearchResultItem | null
  onClose: () => void
}

export function PreviewPanel({ selectedResult, onClose }: PreviewPanelProps) {
  const { t } = useTranslation()
  const { data: paperDetail } = usePaper(selectedResult?.id || '')

  if (!selectedResult) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">{t('search.selectPaperToPreview')}</p>
          <p className="text-xs mt-1">{t('search.useArrowKeys')}</p>
        </div>
      </div>
    )
  }

  const paper = selectedResult
  const score = selectedResult.score
  const abstractHighlight = getHighlightSnippet(selectedResult, 'abstract')

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-start justify-between p-4 border-b">
        <div className="flex-1 min-w-0">
          <Badge variant="secondary" className="mb-2">
            {(selectedResult.relevance_score * 100).toFixed(0)}% match
          </Badge>
          <h2 className="text-lg font-semibold line-clamp-2">{paper.title}</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0 ml-2">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
          {paper.publication_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {formatDate(paper.publication_date)}
            </div>
          )}
          {paper.journal && (
            <div className="flex items-center gap-1">
              <BookOpen className="h-4 w-4" />
              {paper.journal}
            </div>
          )}
          <Badge variant="outline">{paper.source}</Badge>
        </div>

        {paperDetail?.authors && paperDetail.authors.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 flex items-center gap-1">
              <Users className="h-4 w-4" /> {t('papers.authors')}
            </h3>
            <div className="flex flex-wrap gap-2">
              {paperDetail.authors.slice(0, 5).map((author, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {author.author.name}
                  {author.is_corresponding && ' *'}
                </Badge>
              ))}
              {paperDetail.authors.length > 5 && (
                <Badge variant="outline" className="text-xs">
                  +{paperDetail.authors.length - 5} more
                </Badge>
              )}
            </div>
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium mb-2">{t('papers.abstract')}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {abstractHighlight ? (
              <span
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(abstractHighlight, SEARCH_SANITIZE_CONFIG),
                }}
              />
            ) : (
              paper.abstract || t('papers.noAbstract')
            )}
          </p>
        </div>

        {score && (
          <div>
            <h3 className="text-sm font-medium mb-3">{t('search.innovationScores')}</h3>
            <div className="grid grid-cols-3 gap-2">
              <ScoreCard label="Overall" value={score.overall_score} />
              <ScoreCard label="Novelty" value={score.novelty} />
              <ScoreCard label="IP" value={score.ip_potential} />
              <ScoreCard label="Market" value={score.marketability} />
              <ScoreCard label="Feasibility" value={score.feasibility} />
              <ScoreCard label="Commercial" value={score.commercialization} />
            </div>
          </div>
        )}

        {paper.keywords && paper.keywords.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2">{t('papers.keywords')}</h3>
            <div className="flex flex-wrap gap-1">
              {paper.keywords.map((keyword, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {keyword}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t">
        <Link to={`/papers/${paper.id}`}>
          <Button className="w-full">
            <ExternalLink className="h-4 w-4 mr-2" />
            {t('search.viewFullDetails')}
          </Button>
        </Link>
      </div>
    </div>
  )
}
