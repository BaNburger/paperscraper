import { useState, useCallback, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import DOMPurify from 'dompurify'
import { useSearchMutation, usePaper } from '@/hooks'

// Restrictive DOMPurify config for search highlights - only allow text formatting tags
const SANITIZE_CONFIG = {
  ALLOWED_TAGS: ['em', 'strong', 'mark', 'b', 'i'],
  ALLOWED_ATTR: [],
  KEEP_CONTENT: true,
}
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { AccessibleModal } from '@/components/ui/AccessibleModal'
import {
  Search,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  SearchX,
  ExternalLink,
  Calendar,
  BookOpen,
  Users,
  X,
  ChevronUp,
  ChevronDown,
  GitCompare,
  Check,
} from 'lucide-react'
import { formatDate, truncate, getScoreColor, cn } from '@/lib/utils'
import type { SearchMode, SearchResultItem } from '@/types'

const searchModeDefs: { value: SearchMode; labelKey: string; descriptionKey: string }[] = [
  { value: 'hybrid', labelKey: 'search.modeHybrid', descriptionKey: 'search.modeHybridDescription' },
  { value: 'fulltext', labelKey: 'search.modeFulltext', descriptionKey: 'search.modeFulltextDescription' },
  { value: 'semantic', labelKey: 'search.modeSemantic', descriptionKey: 'search.modeSemanticDescription' },
]

type SearchScore = NonNullable<SearchResultItem['score']>

function getHighlightSnippet(item: SearchResultItem, field: 'title' | 'abstract'): string | null {
  const highlight = item.highlights?.find((entry) => entry.field === field)
  return highlight?.snippet ?? null
}

function ScoreCard({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className={cn('text-center p-2 rounded-lg bg-muted/50', className)}>
      <div className={cn('text-lg font-bold', getScoreColor(value))}>{value.toFixed(1)}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

// Radar chart for comparing paper scores
function ComparisonRadarChart({ papers }: { papers: { title: string; score: SearchScore }[] }) {
  const dimensions = [
    { key: 'overall_score', label: 'Overall' },
    { key: 'novelty', label: 'Novelty' },
    { key: 'ip_potential', label: 'IP' },
    { key: 'marketability', label: 'Market' },
    { key: 'feasibility', label: 'Feasibility' },
    { key: 'commercialization', label: 'Commercial' },
  ] as const

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']
  const size = 300
  const center = size / 2
  const radius = (size - 60) / 2

  // Generate radar polygon points for a paper
  const getPolygonPoints = (score: SearchScore): string => {
    return dimensions
      .map((dim, i) => {
        const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2
        const value = (score[dim.key] as number) / 10
        const x = center + radius * value * Math.cos(angle)
        const y = center + radius * value * Math.sin(angle)
        return `${x},${y}`
      })
      .join(' ')
  }

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* Grid circles */}
        {[0.2, 0.4, 0.6, 0.8, 1].map((scale) => (
          <circle
            key={scale}
            cx={center}
            cy={center}
            r={radius * scale}
            fill="none"
            stroke="currentColor"
            strokeOpacity={0.1}
          />
        ))}

        {/* Axis lines */}
        {dimensions.map((_, i) => {
          const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2
          const x = center + radius * Math.cos(angle)
          const y = center + radius * Math.sin(angle)
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x}
              y2={y}
              stroke="currentColor"
              strokeOpacity={0.2}
            />
          )
        })}

        {/* Axis labels */}
        {dimensions.map((dim, i) => {
          const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2
          const x = center + (radius + 25) * Math.cos(angle)
          const y = center + (radius + 25) * Math.sin(angle)
          return (
            <text
              key={dim.key}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-xs fill-muted-foreground"
            >
              {dim.label}
            </text>
          )
        })}

        {/* Paper polygons */}
        {papers.map((paper, idx) => (
          <polygon
            key={idx}
            points={getPolygonPoints(paper.score)}
            fill={colors[idx]}
            fillOpacity={0.2}
            stroke={colors[idx]}
            strokeWidth={2}
          />
        ))}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-4 justify-center">
        {papers.map((paper, idx) => (
          <div key={idx} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: colors[idx] }}
            />
            <span className="max-w-[150px] truncate">{paper.title}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Comparison modal component
function ComparisonModal({
  open,
  papers,
  onOpenChange,
}: {
  open: boolean
  papers: SearchResultItem[]
  onOpenChange: (open: boolean) => void
}) {
  const { t } = useTranslation()
  const papersWithScores = papers.filter((p) => p.score)

  return (
    <AccessibleModal
      open={open}
      onOpenChange={onOpenChange}
      title={t('search.paperComparison')}
      description={t('search.comparingPapers', { count: papers.length })}
      contentClassName="w-[min(95vw,72rem)]"
    >
      <div className="space-y-6">
        {/* Radar Chart */}
        {papersWithScores.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>{t('search.scoreComparison')}</CardTitle>
              <CardDescription>{t('search.radarChartOverlay')}</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <ComparisonRadarChart
                papers={papersWithScores.map((p) => ({
                  title: p.title,
                  score: p.score!,
                }))}
              />
            </CardContent>
          </Card>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            {t('search.noScoresForComparison')}
          </div>
        )}

        {/* Comparison Table */}
        <Card>
          <CardHeader>
            <CardTitle>{t('search.metricComparison')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">{t('search.metric')}</th>
                    {papers.map((p) => (
                      <th key={p.id} className="text-center p-2 font-medium">
                        <div className="max-w-[150px] truncate" title={p.title}>
                          {p.title.slice(0, 30)}...
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.overallScore')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score ? (
                          <span className={getScoreColor(p.score.overall_score)}>
                            {p.score.overall_score.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.novelty')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.novelty?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.ipPotential')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.ip_potential?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.marketability')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.marketability?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.feasibility')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.feasibility?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.commercialization')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.commercialization?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('search.relevance')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {(p.relevance_score * 100).toFixed(0)}%
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.source')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        <Badge variant="outline">{p.source}</Badge>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 font-medium">{t('search.published')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.publication_date ? formatDate(p.publication_date) : '-'}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AccessibleModal>
  )
}

function PreviewPanel({
  selectedResult,
  onClose,
}: {
  selectedResult: SearchResultItem | null
  onClose: () => void
}) {
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
      {/* Header */}
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

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Metadata */}
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

        {/* Authors */}
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

        {/* Abstract */}
        <div>
          <h3 className="text-sm font-medium mb-2">{t('papers.abstract')}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {abstractHighlight ? (
              <span
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(abstractHighlight, SANITIZE_CONFIG),
                }}
              />
            ) : (
              paper.abstract || t('papers.noAbstract')
            )}
          </p>
        </div>

        {/* Scores */}
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

        {/* Keywords */}
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

      {/* Footer */}
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
  const resultsRef = useRef<HTMLDivElement>(null)
  const resultItemRefs = useRef<Array<HTMLDivElement | null>>([])

  const searchModes = searchModeDefs.map((m) => ({
    ...m,
    label: t(m.labelKey),
    description: t(m.descriptionKey),
  }))

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSearch(1)
  }

  const toggleCompareSelect = (paperId: string) => {
    const newSelected = new Set(selectedForCompare)
    if (newSelected.has(paperId)) {
      newSelected.delete(paperId)
    } else if (newSelected.size < 5) {
      newSelected.add(paperId)
    }
    setSelectedForCompare(newSelected)
  }

  const result = searchMutation.data
  const results = useMemo(() => result?.items ?? [], [result])
  const selectedResult = selectedIndex >= 0 ? results[selectedIndex] : null
  const papersForCompare = results.filter((r) => selectedForCompare.has(r.id))

  const focusResultItem = useCallback((index: number) => {
    const item = resultItemRefs.current[index]
    if (!item) return
    item.focus()
    item.scrollIntoView({ block: 'nearest' })
  }, [])

  const handleResultsKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLElement>) => {
      if (!results.length) return

      if (e.key === 'ArrowDown' || e.key === 'j') {
        e.preventDefault()
        const nextIndex =
          selectedIndex < 0 ? 0 : Math.min(selectedIndex + 1, results.length - 1)
        setSelectedIndex(nextIndex)
        focusResultItem(nextIndex)
        return
      }

      if (e.key === 'ArrowUp' || e.key === 'k') {
        e.preventDefault()
        const nextIndex =
          selectedIndex < 0 ? 0 : Math.max(selectedIndex - 1, 0)
        setSelectedIndex(nextIndex)
        focusResultItem(nextIndex)
        return
      }

      if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault()
        navigate(`/papers/${results[selectedIndex].id}`)
        return
      }

      if (e.key === 'Escape') {
        setSelectedIndex(-1)
      }
    },
    [focusResultItem, navigate, results, selectedIndex]
  )

  return (
    <div className="space-y-6">
      {/* Comparison Modal */}
      {showComparison && papersForCompare.length >= 2 && (
        <ComparisonModal
          open={showComparison}
          papers={papersForCompare}
          onOpenChange={setShowComparison}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('search.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('search.subtitle')}
          </p>
        </div>
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
            >
              {showPreview ? t('search.hidePreview') : t('search.showPreview')}
            </Button>
          )}
        </div>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={t('search.searchPlaceholder')}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" isLoading={searchMutation.isPending}>
                {t('common.search')}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => setShowFilters(!showFilters)}
              >
                <SlidersHorizontal className="h-4 w-4" />
              </Button>
            </div>

            {/* Search Mode */}
            <div className="flex flex-wrap gap-2">
              {searchModes.map((m) => (
                <Button
                  key={m.value}
                  type="button"
                  variant={mode === m.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMode(m.value)}
                >
                  {m.label}
                </Button>
              ))}
              <span className="text-sm text-muted-foreground self-center ml-2">
                {searchModes.find((m) => m.value === mode)?.description}
              </span>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="rounded-lg border p-4 space-y-4">
                {mode === 'hybrid' && (
                  <div>
                    <Label>
                      {t('search.semanticWeight', { value: semanticWeight.toFixed(1) })}
                    </Label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={semanticWeight}
                      onChange={(e) => setSemanticWeight(parseFloat(e.target.value))}
                      className="w-full mt-2"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>{t('search.moreTextBased')}</span>
                      <span>{t('search.moreSemantic')}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {searchMutation.isPending ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : result ? (
        <div className="flex gap-6">
          {/* Results List */}
          <div className={cn('flex-1 space-y-4', showPreview && 'lg:max-w-[55%]')}>
            {/* Results Header */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
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

            {/* Results List */}
            {results.length === 0 ? (
              <Card>
                <CardContent>
                  <EmptyState
                    icon={<SearchX className="h-16 w-16" />}
                    title={t('search.noResultsFound')}
                    description={t('search.noResultsDescription', { query: result.query })}
                    action={{
                      label: t('search.trySemanticSearch'),
                      onClick: () => setMode('semantic'),
                    }}
                  />
                </CardContent>
              </Card>
            ) : (
              <div
                ref={resultsRef}
                role="listbox"
                aria-label={t('search.resultsListLabel')}
                className="space-y-2"
                onKeyDown={handleResultsKeyDown}
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
                    onClick={() => setSelectedIndex(index)}
                    onFocus={() => setSelectedIndex(index)}
                    className={cn(
                      'transition-all rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                      selectedIndex === index && 'ring-2 ring-primary ring-offset-2 ring-offset-background rounded-lg'
                    )}
                  >
                    <Card className={cn('hover:bg-muted/50 transition-colors')}>
                      <CardContent className="py-4">
                        <div className="flex items-start justify-between gap-4">
                          {/* Compare Mode Checkbox */}
                          {compareMode && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleCompareSelect(item.id)
                              }}
                              className={cn(
                                'shrink-0 w-5 h-5 mt-0.5 rounded border-2 flex items-center justify-center transition-colors',
                                selectedForCompare.has(item.id)
                                  ? 'bg-primary border-primary text-primary-foreground'
                                  : 'border-muted-foreground/50 hover:border-primary'
                              )}
                            >
                              {selectedForCompare.has(item.id) && (
                                <Check className="h-3 w-3" />
                              )}
                            </button>
                          )}
                          <div className="min-w-0 flex-1">
                            <h3 className="font-medium line-clamp-2">
                              {getHighlightSnippet(item, 'title') ? (
                                <span
                                  dangerouslySetInnerHTML={{
                                    __html: DOMPurify.sanitize(
                                      getHighlightSnippet(item, 'title') || '',
                                      SANITIZE_CONFIG,
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
                                      SANITIZE_CONFIG,
                                    ),
                                  }}
                                />
                              ) : (
                                truncate(item.abstract ?? 'No abstract', 150)
                              )}
                            </p>
                            <div className="flex flex-wrap items-center gap-2 mt-3">
                              <Badge variant="outline">{item.source}</Badge>
                              {item.journal && (
                                <span className="text-xs text-muted-foreground">
                                  {item.journal}
                                </span>
                              )}
                              {item.publication_date && (
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(item.publication_date)}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-2 shrink-0">
                            <Badge variant="secondary">
                              {(item.relevance_score * 100).toFixed(0)}% match
                            </Badge>
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
                                navigate(`/papers/${item.id}`)
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

            {/* Pagination */}
            {result.pages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {t('common.pageOf', { page: result.page, pages: result.pages })}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(page - 1)}
                    disabled={page <= 1 || searchMutation.isPending}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    {t('common.previous')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(page + 1)}
                    disabled={page >= result.pages || searchMutation.isPending}
                  >
                    {t('common.next')}
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Preview Panel */}
          {showPreview && (
            <div className="hidden lg:block w-[45%] sticky top-6 self-start">
              <Card className="h-[calc(100vh-200px)]">
                <PreviewPanel
                  selectedResult={selectedResult}
                  onClose={() => setSelectedIndex(-1)}
                />
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
