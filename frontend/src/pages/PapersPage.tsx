import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { usePapers, useIngestByDoi, useIngestFromOpenAlex } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import {
  FileText,
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Download,
} from 'lucide-react'
import { formatDate, truncate } from '@/lib/utils'

export function PapersPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get('page') ?? '1')
  const search = searchParams.get('search') ?? ''
  const pageSize = 10

  const [searchInput, setSearchInput] = useState(search)
  const [showImportModal, setShowImportModal] = useState(false)
  const [importMode, setImportMode] = useState<'doi' | 'openalex'>('doi')
  const [doiInput, setDoiInput] = useState('')
  const [openAlexQuery, setOpenAlexQuery] = useState('')
  const [openAlexMaxResults, setOpenAlexMaxResults] = useState(20)

  const { data, isLoading, error } = usePapers({ page, page_size: pageSize, search })
  const ingestByDoi = useIngestByDoi()
  const ingestFromOpenAlex = useIngestFromOpenAlex()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams({ search: searchInput, page: '1' })
  }

  const handlePageChange = (newPage: number) => {
    setSearchParams({ search, page: newPage.toString() })
  }

  const handleImportDoi = async () => {
    try {
      await ingestByDoi.mutateAsync(doiInput)
      setDoiInput('')
      setShowImportModal(false)
    } catch (err) {
      // Error handled by mutation
    }
  }

  const handleImportOpenAlex = async () => {
    try {
      await ingestFromOpenAlex.mutateAsync({
        query: openAlexQuery,
        max_results: openAlexMaxResults,
      })
      setOpenAlexQuery('')
      setShowImportModal(false)
    } catch (err) {
      // Error handled by mutation
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Papers</h1>
          <p className="text-muted-foreground mt-1">
            Manage your research paper library
          </p>
        </div>
        <Button onClick={() => setShowImportModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Import Papers
        </Button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search papers by title or abstract..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button type="submit">Search</Button>
      </form>

      {/* Papers List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            Failed to load papers. Please try again.
          </CardContent>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">No papers found</h3>
            <p className="text-muted-foreground text-sm mt-1">
              {search ? 'Try a different search term' : 'Import papers to get started'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {data?.items.map((paper) => (
              <Link key={paper.id} to={`/papers/${paper.id}`}>
                <Card className="hover:bg-muted/50 transition-colors">
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium line-clamp-2">{paper.title}</h3>
                        <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                          {truncate(paper.abstract ?? 'No abstract available', 200)}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 mt-3">
                          <Badge variant="outline">{paper.source}</Badge>
                          {paper.journal && (
                            <span className="text-xs text-muted-foreground">
                              {paper.journal}
                            </span>
                          )}
                          {paper.publication_date && (
                            <span className="text-xs text-muted-foreground">
                              {formatDate(paper.publication_date)}
                            </span>
                          )}
                          {paper.doi && (
                            <span className="text-xs text-muted-foreground">
                              DOI: {paper.doi}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        {paper.has_embedding && (
                          <Badge variant="secondary">Embedded</Badge>
                        )}
                        {paper.citations_count != null && paper.citations_count > 0 && (
                          <span className="text-xs text-muted-foreground">
                            {paper.citations_count} citations
                          </span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, data.total)} of {data.total} papers
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <span className="text-sm">
                  Page {page} of {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= data.pages}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg mx-4">
            <CardHeader>
              <CardTitle>Import Papers</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mode Tabs */}
              <div className="flex gap-2">
                <Button
                  variant={importMode === 'doi' ? 'default' : 'outline'}
                  onClick={() => setImportMode('doi')}
                  className="flex-1"
                >
                  By DOI
                </Button>
                <Button
                  variant={importMode === 'openalex' ? 'default' : 'outline'}
                  onClick={() => setImportMode('openalex')}
                  className="flex-1"
                >
                  From OpenAlex
                </Button>
              </div>

              {importMode === 'doi' ? (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="doi">DOI</Label>
                    <Input
                      id="doi"
                      placeholder="10.1234/example.123"
                      value={doiInput}
                      onChange={(e) => setDoiInput(e.target.value)}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowImportModal(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleImportDoi}
                      isLoading={ingestByDoi.isPending}
                      disabled={!doiInput}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Import
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="query">Search Query</Label>
                    <Input
                      id="query"
                      placeholder="e.g., machine learning healthcare"
                      value={openAlexQuery}
                      onChange={(e) => setOpenAlexQuery(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="maxResults">Max Results</Label>
                    <Input
                      id="maxResults"
                      type="number"
                      min={1}
                      max={100}
                      value={openAlexMaxResults}
                      onChange={(e) => setOpenAlexMaxResults(parseInt(e.target.value))}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowImportModal(false)}>
                      Cancel
                    </Button>
                    <Button
                      onClick={handleImportOpenAlex}
                      isLoading={ingestFromOpenAlex.isPending}
                      disabled={!openAlexQuery}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Import
                    </Button>
                  </div>
                  {ingestFromOpenAlex.isSuccess && (
                    <div className="rounded-md bg-green-100 p-3 text-sm text-green-800">
                      Imported {ingestFromOpenAlex.data.papers_created} papers
                      {ingestFromOpenAlex.data.papers_skipped > 0 && (
                        <> (skipped {ingestFromOpenAlex.data.papers_skipped} duplicates)</>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
