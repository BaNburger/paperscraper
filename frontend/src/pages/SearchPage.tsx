import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSearchMutation } from '@/hooks'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import {
  Search,
  Loader2,
  FileText,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
} from 'lucide-react'
import { formatDate, truncate, getScoreColor } from '@/lib/utils'
import type { SearchMode } from '@/types'

const searchModes: { value: SearchMode; label: string; description: string }[] = [
  { value: 'hybrid', label: 'Hybrid', description: 'Combines text and semantic search' },
  { value: 'fulltext', label: 'Full-text', description: 'Traditional keyword search' },
  { value: 'semantic', label: 'Semantic', description: 'AI-powered meaning search' },
]

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<SearchMode>('hybrid')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [semanticWeight, setSemanticWeight] = useState(0.5)

  const searchMutation = useSearchMutation()

  const handleSearch = async (newPage = 1) => {
    if (!query.trim()) return
    setPage(newPage)
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

  const result = searchMutation.data

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Search</h1>
        <p className="text-muted-foreground mt-1">
          Find papers using full-text, semantic, or hybrid search
        </p>
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
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : result ? (
        <div className="space-y-4">
          {/* Results Header */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Found {result.total} results for "{result.query}" using {result.mode} search
            </p>
          </div>

          {/* Results List */}
          {result.results.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="font-medium">No results found</h3>
                <p className="text-muted-foreground text-sm mt-1">
                  Try different keywords or search mode
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {result.results.map((item) => (
                <Link key={item.paper.id} to={`/papers/${item.paper.id}`}>
                  <Card className="hover:bg-muted/50 transition-colors">
                    <CardContent className="py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <h3 className="font-medium line-clamp-2">
                            {item.highlights.title ? (
                              <span
                                dangerouslySetInnerHTML={{
                                  __html: item.highlights.title,
                                }}
                              />
                            ) : (
                              item.paper.title
                            )}
                          </h3>
                          <p className="text-sm text-muted-foreground mt-2 line-clamp-3">
                            {item.highlights.abstract ? (
                              <span
                                dangerouslySetInnerHTML={{
                                  __html: item.highlights.abstract,
                                }}
                              />
                            ) : (
                              truncate(item.paper.abstract ?? 'No abstract', 200)
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
                </Link>
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
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">Start searching</h3>
            <p className="text-muted-foreground text-sm mt-1">
              Enter a query to search your paper library
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
