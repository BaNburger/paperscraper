import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { GitCompare, Search } from 'lucide-react'
import { useSearchMutation } from '@/hooks'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { ComparisonModal } from '@/features/search/components/ComparisonModal'
import {
  SearchForm,
  type SearchModeDefinition,
} from '@/features/search/components/SearchForm'
import { ResultsList } from '@/features/search/components/ResultsList'
import { PreviewPanel } from '@/features/search/components/PreviewPanel'
import { useSearchKeyboardNavigation } from '@/features/search/hooks/useSearchKeyboardNavigation'
import { cn } from '@/lib/utils'
import type { SearchMode } from '@/types'

const searchModeDefs: { value: SearchMode; labelKey: string; descriptionKey: string }[] = [
  { value: 'hybrid', labelKey: 'search.modeHybrid', descriptionKey: 'search.modeHybridDescription' },
  { value: 'fulltext', labelKey: 'search.modeFulltext', descriptionKey: 'search.modeFulltextDescription' },
  { value: 'semantic', labelKey: 'search.modeSemantic', descriptionKey: 'search.modeSemanticDescription' },
]

export function SearchPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<SearchMode>('hybrid')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [semanticWeight, setSemanticWeight] = useState(0.5)
  const [selectedIndex, setSelectedIndex] = useState<number>(-1)
  const [showPreview, setShowPreview] = useState(true)
  const [compareMode, setCompareMode] = useState(false)
  const [selectedForCompare, setSelectedForCompare] = useState<Set<string>>(new Set())
  const [showComparison, setShowComparison] = useState(false)

  const searchModes = useMemo<SearchModeDefinition[]>(
    () =>
      searchModeDefs.map((searchMode) => ({
        value: searchMode.value,
        label: t(searchMode.labelKey),
        description: t(searchMode.descriptionKey),
      })),
    [t]
  )

  const searchMutation = useSearchMutation()

  const handleSearch = async (newPage = 1) => {
    if (!query.trim()) return
    setPage(newPage)
    setSelectedIndex(-1)
    setSelectedForCompare(new Set())
    setCompareMode(false)

    await searchMutation.mutateAsync({
      query: query.trim(),
      mode,
      page: newPage,
      page_size: 10,
      semantic_weight: mode === 'hybrid' ? semanticWeight : 0.5,
      include_highlights: true,
    })
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    void handleSearch(1)
  }

  const toggleCompareSelect = (paperId: string) => {
    const nextSelected = new Set(selectedForCompare)
    if (nextSelected.has(paperId)) {
      nextSelected.delete(paperId)
    } else if (nextSelected.size < 5) {
      nextSelected.add(paperId)
    }
    setSelectedForCompare(nextSelected)
  }

  const result = searchMutation.data
  const results = useMemo(() => result?.items ?? [], [result])
  const selectedResult = selectedIndex >= 0 ? results[selectedIndex] : null
  const papersForCompare = results.filter((paper) => selectedForCompare.has(paper.id))

  const { resultItemRefs, handleResultsKeyDown } = useSearchKeyboardNavigation({
    results,
    selectedIndex,
    setSelectedIndex,
    onOpenResult: (paperId) => navigate(`/papers/${paperId}`),
  })

  return (
    <div className="space-y-6" data-testid="search-page">
      {showComparison && papersForCompare.length >= 2 && (
        <ComparisonModal
          open={showComparison}
          papers={papersForCompare}
          onOpenChange={setShowComparison}
        />
      )}

      <PageHeader
        title={t('search.title')}
        description={t('search.subtitle')}
        actions={
          <div className="flex gap-2">
            {result && results.length > 0 && (
              <>
                {compareMode ? (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {t('search.selectedCount', { count: selectedForCompare.size, max: 5 })}
                    </span>
                    <Button
                      size="sm"
                      onClick={() => setShowComparison(true)}
                      disabled={selectedForCompare.size < 2}
                      data-testid="search-open-comparison"
                    >
                      <GitCompare className="h-4 w-4 mr-2" />
                      {t('search.compare')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setCompareMode(false)
                        setSelectedForCompare(new Set())
                      }}
                    >
                      {t('common.cancel')}
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCompareMode(true)}
                    data-testid="search-enable-compare"
                  >
                    <GitCompare className="h-4 w-4 mr-2" />
                    {t('search.comparePapers')}
                  </Button>
                )}
              </>
            )}
            {result && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPreview(!showPreview)}
                className="hidden lg:flex"
                data-testid="search-toggle-preview"
              >
                {showPreview ? t('search.hidePreview') : t('search.showPreview')}
              </Button>
            )}
          </div>
        }
      />

      <SearchForm
        query={query}
        onQueryChange={setQuery}
        mode={mode}
        onModeChange={setMode}
        showFilters={showFilters}
        onToggleFilters={() => setShowFilters((prev) => !prev)}
        semanticWeight={semanticWeight}
        onSemanticWeightChange={setSemanticWeight}
        searchModes={searchModes}
        isLoading={searchMutation.isPending}
        onSubmit={handleSubmit}
      />

      {searchMutation.isPending ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, index) => (
            <SkeletonCard key={index} />
          ))}
        </div>
      ) : result ? (
        <div className="flex gap-6">
          <div className={cn('flex-1', showPreview && 'lg:max-w-[55%]')}>
            <ResultsList
              result={result}
              results={results}
              selectedIndex={selectedIndex}
              onSelectIndex={setSelectedIndex}
              compareMode={compareMode}
              selectedForCompare={selectedForCompare}
              onToggleCompareSelect={toggleCompareSelect}
              onOpenResult={(paperId) => navigate(`/papers/${paperId}`)}
              onResultsKeyDown={handleResultsKeyDown}
              resultItemRefs={resultItemRefs}
              isLoading={searchMutation.isPending}
              page={page}
              onPageChange={(nextPage) => {
                void handleSearch(nextPage)
              }}
              onFallbackModeChange={setMode}
            />
          </div>

          {showPreview && (
            <div className="hidden lg:block w-[45%] sticky top-6 self-start" data-testid="search-preview-panel">
              <Card className="h-[calc(100vh-200px)]">
                <PreviewPanel selectedResult={selectedResult} onClose={() => setSelectedIndex(-1)} />
              </Card>
            </div>
          )}
        </div>
      ) : (
        <Card>
          <CardContent>
            <EmptyState
              icon={<Search className="h-16 w-16" />}
              title={t('search.startSearching')}
              description={t('search.startSearchingDescription')}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
