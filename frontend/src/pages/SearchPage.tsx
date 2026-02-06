import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
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
import type { SearchMode, SearchResult, PaperScore } from '@/types'

const searchModes: { value: SearchMode; label: string; description: string }[] = [
  { value: 'hybrid', label: 'Hybrid', description: 'Combines text and semantic search' },
  { value: 'fulltext', label: 'Full-text', description: 'Traditional keyword search' },
  { value: 'semantic', label: 'Semantic', description: 'AI-powered meaning search' },
]

function ScoreCard({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className={cn('text-center p-2 rounded-lg bg-muted/50', className)}>
      <div className={cn('text-lg font-bold', getScoreColor(value))}>{value.toFixed(1)}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

// Radar chart for comparing paper scores
function ComparisonRadarChart({ papers }: { papers: { title: string; score: PaperScore }[] }) {
  const dimensions = [
    { key: 'overall_score', label: 'Overall' },
    { key: 'novelty', label: 'Novelty' },
    { key: 'ip_potential', label: 'IP' },
    { key: 'marketability', label: 'Market' },
    { key: 'feasibility', label: 'Feasibility' },
    { key: 'team_readiness', label: 'Team' },
  ] as const

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']
  const size = 300
  const center = size / 2
  const radius = (size - 60) / 2

  // Generate radar polygon points for a paper
  const getPolygonPoints = (score: PaperScore): string => {
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
  papers,
  onClose,
}: {
  papers: SearchResult[]
  onClose: () => void
}) {
  const papersWithScores = papers.filter((p) => p.latest_score)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-background border-b p-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Paper Comparison</h2>
            <p className="text-sm text-muted-foreground">
              Comparing {papers.length} papers across scoring dimensions
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Radar Chart */}
          {papersWithScores.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Score Comparison</CardTitle>
                <CardDescription>Radar chart overlay of selected papers</CardDescription>
              </CardHeader>
              <CardContent className="flex justify-center">
                <ComparisonRadarChart
                  papers={papersWithScores.map((p) => ({
                    title: p.paper.title,
                    score: p.latest_score!,
                  }))}
                />
              </CardContent>
            </Card>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No papers with scores available for comparison
            </div>
          )}

          {/* Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle>Metric Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2 font-medium">Metric</th>
                      {papers.map((p) => (
                        <th key={p.paper.id} className="text-center p-2 font-medium">
                          <div className="max-w-[150px] truncate" title={p.paper.title}>
                            {p.paper.title.slice(0, 30)}...
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Overall Score</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.latest_score ? (
                            <span className={getScoreColor(p.latest_score.overall_score)}>
                              {p.latest_score.overall_score.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Novelty</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.latest_score?.novelty?.toFixed(1) ?? '-'}
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">IP Potential</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.latest_score?.ip_potential?.toFixed(1) ?? '-'}
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Marketability</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.latest_score?.marketability?.toFixed(1) ?? '-'}
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Feasibility</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.latest_score?.feasibility?.toFixed(1) ?? '-'}
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Team Readiness</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.latest_score?.team_readiness?.toFixed(1) ?? '-'}
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Relevance</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {(p.relevance_score * 100).toFixed(0)}%
                        </td>
                      ))}
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 font-medium">Source</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          <Badge variant="outline">{p.paper.source}</Badge>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-2 font-medium">Published</td>
                      {papers.map((p) => (
                        <td key={p.paper.id} className="text-center p-2">
                          {p.paper.publication_date
                            ? formatDate(p.paper.publication_date)
                            : '-'}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function PreviewPanel({
  selectedResult,
  onClose,
}: {
  selectedResult: SearchResult | null
  onClose: () => void
}) {
  const { data: paperDetail } = usePaper(selectedResult?.paper.id || '')

  if (!selectedResult) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">Select a paper to preview</p>
          <p className="text-xs mt-1">Use arrow keys to navigate</p>
        </div>
      </div>
    )
  }

  const paper = selectedResult.paper
  const score = selectedResult.latest_score

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
              <Users className="h-4 w-4" /> Authors
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
          <h3 className="text-sm font-medium mb-2">Abstract</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {selectedResult.highlights.abstract ? (
              <span
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(selectedResult.highlights.abstract, SANITIZE_CONFIG),
                }}
              />
            ) : (
              paper.abstract || 'No abstract available'
            )}
          </p>
        </div>

        {/* Scores */}
        {score && (
          <div>
            <h3 className="text-sm font-medium mb-3">Innovation Scores</h3>
            <div className="grid grid-cols-3 gap-2">
              <ScoreCard label="Overall" value={score.overall_score} />
              <ScoreCard label="Novelty" value={score.novelty} />
              <ScoreCard label="IP" value={score.ip_potential} />
              <ScoreCard label="Market" value={score.marketability} />
              <ScoreCard label="Feasibility" value={score.feasibility} />
              <ScoreCard label="Team" value={score.team_readiness} />
            </div>
          </div>
        )}

        {/* Keywords */}
        {paper.keywords && paper.keywords.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2">Keywords</h3>
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
            View Full Details
          </Button>
        </Link>
      </div>
    </div>
  )
}

export function SearchPage() {
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
      semantic_weight: mode === 'hybrid' ? semanticWeight : undefined,
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
  const results = result?.results ?? []
  const selectedResult = selectedIndex >= 0 ? results[selectedIndex] : null
  const papersForCompare = results.filter((r) => selectedForCompare.has(r.paper.id))

  // Keyboard navigation for results
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!results.length) return

      if (e.key === 'ArrowDown' || e.key === 'j') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
      } else if (e.key === 'ArrowUp' || e.key === 'k') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault()
        window.location.href = `/papers/${results[selectedIndex].paper.id}`
      } else if (e.key === 'Escape') {
        setSelectedIndex(-1)
      }
    },
    [results, selectedIndex]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && resultsRef.current) {
      const items = resultsRef.current.querySelectorAll('[data-result-item]')
      items[selectedIndex]?.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedIndex])

  return (
    <div className="space-y-6">
      {/* Comparison Modal */}
      {showComparison && papersForCompare.length >= 2 && (
        <ComparisonModal
          papers={papersForCompare}
          onClose={() => setShowComparison(false)}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Search</h1>
          <p className="text-muted-foreground mt-1">
            Find papers using full-text, semantic, or hybrid search
          </p>
        </div>
        <div className="flex gap-2">
          {result && results.length > 0 && (
            <>
              {compareMode ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {selectedForCompare.size}/5 selected
                  </span>
                  <Button
                    size="sm"
                    onClick={() => setShowComparison(true)}
                    disabled={selectedForCompare.size < 2}
                  >
                    <GitCompare className="h-4 w-4 mr-2" />
                    Compare
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setCompareMode(false)
                      setSelectedForCompare(new Set())
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCompareMode(true)}
                >
                  <GitCompare className="h-4 w-4 mr-2" />
                  Compare Papers
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
              {showPreview ? 'Hide' : 'Show'} Preview
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
                  placeholder="Search for papers..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" isLoading={searchMutation.isPending}>
                Search
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
                      Semantic Weight: {semanticWeight.toFixed(1)}
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
                      <span>More text-based</span>
                      <span>More semantic</span>
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
                Found {result.total} results for "{result.query}" using {result.mode} search
              </p>
              {results.length > 0 && (
                <div className="hidden sm:flex items-center gap-1 text-xs text-muted-foreground">
                  <ChevronUp className="h-3 w-3" />
                  <ChevronDown className="h-3 w-3" />
                  to navigate
                </div>
              )}
            </div>

            {/* Results List */}
            {results.length === 0 ? (
              <Card>
                <CardContent>
                  <EmptyState
                    icon={<SearchX className="h-16 w-16" />}
                    title="No results found"
                    description={`No papers match "${result.query}". Try different keywords or switch to semantic search for broader results.`}
                    action={{
                      label: 'Try Semantic Search',
                      onClick: () => setMode('semantic'),
                    }}
                  />
                </CardContent>
              </Card>
            ) : (
              <div ref={resultsRef} className="space-y-2">
                {results.map((item, index) => (
                  <div
                    key={item.paper.id}
                    data-result-item
                    onClick={() => setSelectedIndex(index)}
                    onDoubleClick={() => (window.location.href = `/papers/${item.paper.id}`)}
                    className={cn(
                      'cursor-pointer transition-all',
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
                                toggleCompareSelect(item.paper.id)
                              }}
                              className={cn(
                                'shrink-0 w-5 h-5 mt-0.5 rounded border-2 flex items-center justify-center transition-colors',
                                selectedForCompare.has(item.paper.id)
                                  ? 'bg-primary border-primary text-primary-foreground'
                                  : 'border-muted-foreground/50 hover:border-primary'
                              )}
                            >
                              {selectedForCompare.has(item.paper.id) && (
                                <Check className="h-3 w-3" />
                              )}
                            </button>
                          )}
                          <div className="min-w-0 flex-1">
                            <h3 className="font-medium line-clamp-2">
                              {item.highlights.title ? (
                                <span
                                  dangerouslySetInnerHTML={{
                                    __html: DOMPurify.sanitize(item.highlights.title, SANITIZE_CONFIG),
                                  }}
                                />
                              ) : (
                                item.paper.title
                              )}
                            </h3>
                            <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                              {item.highlights.abstract ? (
                                <span
                                  dangerouslySetInnerHTML={{
                                    __html: DOMPurify.sanitize(item.highlights.abstract, SANITIZE_CONFIG),
                                  }}
                                />
                              ) : (
                                truncate(item.paper.abstract ?? 'No abstract', 150)
                              )}
                            </p>
                            <div className="flex flex-wrap items-center gap-2 mt-3">
                              <Badge variant="outline">{item.paper.source}</Badge>
                              {item.paper.journal && (
                                <span className="text-xs text-muted-foreground">
                                  {item.paper.journal}
                                </span>
                              )}
                              {item.paper.publication_date && (
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(item.paper.publication_date)}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-2 shrink-0">
                            <Badge variant="secondary">
                              {(item.relevance_score * 100).toFixed(0)}% match
                            </Badge>
                            {item.latest_score && (
                              <div className="flex items-center gap-1 text-sm">
                                <TrendingUp className="h-3 w-3" />
                                <span className={getScoreColor(item.latest_score.overall_score)}>
                                  {item.latest_score.overall_score.toFixed(1)}
                                </span>
                              </div>
                            )}
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
                  Page {result.page} of {result.pages}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(page - 1)}
                    disabled={page <= 1 || searchMutation.isPending}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(page + 1)}
                    disabled={page >= result.pages || searchMutation.isPending}
                  >
                    Next
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
              title="Start searching"
              description="Enter keywords to find papers in your library. Use semantic search to discover papers by meaning, not just keywords."
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
