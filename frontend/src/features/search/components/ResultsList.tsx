import DOMPurify from 'dompurify'
import { useTranslation } from 'react-i18next'
import {
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ExternalLink,
  SearchX,
  TrendingUp,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { getScoreColor, cn, formatDate, truncate } from '@/lib/utils'
import type { SearchResponse, SearchResultItem, SearchMode } from '@/types'
import { getHighlightSnippet, SEARCH_SANITIZE_CONFIG } from '@/features/search/utils'

type ResultsListProps = {
  result: SearchResponse
  results: SearchResultItem[]
  selectedIndex: number
  onSelectIndex: (index: number) => void
  compareMode: boolean
  selectedForCompare: Set<string>
  onToggleCompareSelect: (paperId: string) => void
  onOpenResult: (paperId: string) => void
  onResultsKeyDown: (event: React.KeyboardEvent<HTMLElement>) => void
  resultItemRefs: React.MutableRefObject<Array<HTMLDivElement | null>>
  isLoading: boolean
  page: number
  onPageChange: (page: number) => void
  onFallbackModeChange: (mode: SearchMode) => void
}

export function ResultsList({
  result,
  results,
  selectedIndex,
  onSelectIndex,
  compareMode,
  selectedForCompare,
  onToggleCompareSelect,
  onOpenResult,
  onResultsKeyDown,
  resultItemRefs,
  isLoading,
  page,
  onPageChange,
  onFallbackModeChange,
}: ResultsListProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-4" data-testid="search-results-pane">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground" data-testid="search-results-summary">
          {t('search.foundResults', { total: result.total, query: result.query, mode: result.mode })}
        </p>
        {results.length > 0 && (
          <div className="hidden sm:flex items-center gap-1 text-xs text-muted-foreground">
            <ChevronUp className="h-3 w-3" />
            <ChevronDown className="h-3 w-3" />
            {t('search.toNavigate')}
          </div>
        )}
      </div>

      {results.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<SearchX className="h-16 w-16" />}
              title={t('search.noResultsFound')}
              description={t('search.noResultsDescription', { query: result.query })}
              action={{
                label: t('search.trySemanticSearch'),
                onClick: () => onFallbackModeChange('semantic'),
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div
          role="listbox"
          aria-label={t('search.resultsListLabel')}
          className="space-y-2"
          onKeyDown={onResultsKeyDown}
          data-testid="search-results-list"
        >
          {results.map((item, index) => (
            <div
              key={item.id}
              ref={(element) => {
                resultItemRefs.current[index] = element
              }}
              role="option"
              aria-selected={selectedIndex === index}
              tabIndex={0}
              onClick={() => onSelectIndex(index)}
              onFocus={() => onSelectIndex(index)}
              data-testid={`search-result-${item.id}`}
              className={cn(
                'transition-all rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                selectedIndex === index && 'ring-2 ring-primary ring-offset-2 ring-offset-background rounded-lg'
              )}
            >
              <Card className={cn('hover:bg-muted/50 transition-colors')}>
                <CardContent className="py-4">
                  <div className="flex items-start justify-between gap-4">
                    {compareMode && (
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation()
                          onToggleCompareSelect(item.id)
                        }}
                        data-testid={`search-compare-toggle-${item.id}`}
                        className={cn(
                          'shrink-0 w-5 h-5 mt-0.5 rounded border-2 flex items-center justify-center transition-colors',
                          selectedForCompare.has(item.id)
                            ? 'bg-primary border-primary text-primary-foreground'
                            : 'border-muted-foreground/50 hover:border-primary'
                        )}
                      >
                        {selectedForCompare.has(item.id) && <Check className="h-3 w-3" />}
                      </button>
                    )}
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium line-clamp-2">
                        {getHighlightSnippet(item, 'title') ? (
                          <span
                            dangerouslySetInnerHTML={{
                              __html: DOMPurify.sanitize(
                                getHighlightSnippet(item, 'title') || '',
                                SEARCH_SANITIZE_CONFIG
                              ),
                            }}
                          />
                        ) : (
                          item.title
                        )}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                        {getHighlightSnippet(item, 'abstract') ? (
                          <span
                            dangerouslySetInnerHTML={{
                              __html: DOMPurify.sanitize(
                                getHighlightSnippet(item, 'abstract') || '',
                                SEARCH_SANITIZE_CONFIG
                              ),
                            }}
                          />
                        ) : (
                          truncate(item.abstract ?? 'No abstract', 150)
                        )}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 mt-3">
                        <Badge variant="outline">{item.source}</Badge>
                        {item.journal && <span className="text-xs text-muted-foreground">{item.journal}</span>}
                        {item.publication_date && (
                          <span className="text-xs text-muted-foreground">{formatDate(item.publication_date)}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 shrink-0">
                      <Badge variant="secondary">{(item.relevance_score * 100).toFixed(0)}% match</Badge>
                      {item.score && (
                        <div className="flex items-center gap-1 text-sm">
                          <TrendingUp className="h-3 w-3" />
                          <span className={getScoreColor(item.score.overall_score)}>
                            {item.score.overall_score.toFixed(1)}
                          </span>
                        </div>
                      )}
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={(event) => {
                          event.stopPropagation()
                          onOpenResult(item.id)
                        }}
                      >
                        <ExternalLink className="h-3.5 w-3.5 mr-1" />
                        {t('search.openResult')}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}

      {result.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {t('common.pageOf', { page: result.page, pages: result.pages })}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1 || isLoading}
            >
              <ChevronLeft className="h-4 w-4" />
              {t('common.previous')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= result.pages || isLoading}
            >
              {t('common.next')}
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
