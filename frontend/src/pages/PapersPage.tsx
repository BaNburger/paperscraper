import { useState, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  usePapers,
  useIngestByDoi,
  useIngestFromOpenAlex,
  useIngestFromPubMed,
  useIngestFromArxiv,
  useUploadPdf,
} from '@/hooks'
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
  Upload,
  X,
} from 'lucide-react'
import { formatDate, truncate } from '@/lib/utils'

type ImportMode = 'doi' | 'openalex' | 'pubmed' | 'arxiv' | 'pdf'

export function PapersPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get('page') ?? '1')
  const search = searchParams.get('search') ?? ''
  const pageSize = 10

  const [searchInput, setSearchInput] = useState(search)
  const [showImportModal, setShowImportModal] = useState(false)
  const [importMode, setImportMode] = useState<ImportMode>('doi')

  // DOI state
  const [doiInput, setDoiInput] = useState('')

  // Search-based import state (OpenAlex, PubMed, arXiv)
  const [queryInput, setQueryInput] = useState('')
  const [maxResults, setMaxResults] = useState(20)
  const [arxivCategory, setArxivCategory] = useState('')

  // PDF state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Import result message
  const [importResult, setImportResult] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)

  const { data, isLoading, error } = usePapers({ page, page_size: pageSize, search })
  const ingestByDoi = useIngestByDoi()
  const ingestFromOpenAlex = useIngestFromOpenAlex()
  const ingestFromPubMed = useIngestFromPubMed()
  const ingestFromArxiv = useIngestFromArxiv()
  const uploadPdf = useUploadPdf()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams({ search: searchInput, page: '1' })
  }

  const handlePageChange = (newPage: number) => {
    setSearchParams({ search, page: newPage.toString() })
  }

  const resetImportState = () => {
    setDoiInput('')
    setQueryInput('')
    setMaxResults(20)
    setArxivCategory('')
    setSelectedFile(null)
    setImportResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const closeModal = () => {
    setShowImportModal(false)
    resetImportState()
  }

  const handleImportDoi = async () => {
    try {
      await ingestByDoi.mutateAsync(doiInput)
      setImportResult({ type: 'success', message: 'Paper imported successfully!' })
      setDoiInput('')
    } catch {
      setImportResult({ type: 'error', message: 'Failed to import paper. Check the DOI and try again.' })
    }
  }

  const handleImportOpenAlex = async () => {
    try {
      const result = await ingestFromOpenAlex.mutateAsync({
        query: queryInput,
        max_results: maxResults,
      })
      setImportResult({
        type: 'success',
        message: `Imported ${result.papers_created} papers${
          result.papers_skipped > 0 ? ` (skipped ${result.papers_skipped} duplicates)` : ''
        }`,
      })
      setQueryInput('')
    } catch {
      setImportResult({ type: 'error', message: 'Failed to import from OpenAlex. Please try again.' })
    }
  }

  const handleImportPubMed = async () => {
    try {
      const result = await ingestFromPubMed.mutateAsync({
        query: queryInput,
        max_results: maxResults,
      })
      setImportResult({
        type: 'success',
        message: `Imported ${result.papers_created} papers${
          result.papers_skipped > 0 ? ` (skipped ${result.papers_skipped} duplicates)` : ''
        }`,
      })
      setQueryInput('')
    } catch {
      setImportResult({ type: 'error', message: 'Failed to import from PubMed. Please try again.' })
    }
  }

  const handleImportArxiv = async () => {
    try {
      const result = await ingestFromArxiv.mutateAsync({
        query: queryInput,
        max_results: maxResults,
        category: arxivCategory || undefined,
      })
      setImportResult({
        type: 'success',
        message: `Imported ${result.papers_created} papers${
          result.papers_skipped > 0 ? ` (skipped ${result.papers_skipped} duplicates)` : ''
        }`,
      })
      setQueryInput('')
    } catch {
      setImportResult({ type: 'error', message: 'Failed to import from arXiv. Please try again.' })
    }
  }

  const handleUploadPdf = async () => {
    if (!selectedFile) return
    try {
      await uploadPdf.mutateAsync(selectedFile)
      setImportResult({ type: 'success', message: 'PDF uploaded and processed successfully!' })
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch {
      setImportResult({ type: 'error', message: 'Failed to upload PDF. Please try again.' })
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
      setImportResult(null)
    } else {
      setImportResult({ type: 'error', message: 'Please select a valid PDF file.' })
    }
  }

  const isLoading_ =
    ingestByDoi.isPending ||
    ingestFromOpenAlex.isPending ||
    ingestFromPubMed.isPending ||
    ingestFromArxiv.isPending ||
    uploadPdf.isPending

  const renderImportForm = () => {
    switch (importMode) {
      case 'doi':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="doi">DOI</Label>
              <Input
                id="doi"
                placeholder="10.1234/example.123"
                value={doiInput}
                onChange={(e) => setDoiInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Enter a DOI to import a single paper
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button
                onClick={handleImportDoi}
                isLoading={ingestByDoi.isPending}
                disabled={!doiInput || isLoading_}
              >
                <Download className="h-4 w-4 mr-2" />
                Import
              </Button>
            </div>
          </div>
        )

      case 'openalex':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">Search Query</Label>
              <Input
                id="query"
                placeholder="e.g., machine learning healthcare"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Search OpenAlex for papers matching your query
              </p>
            </div>
            <div>
              <Label htmlFor="maxResults">Max Results</Label>
              <Input
                id="maxResults"
                type="number"
                min={1}
                max={100}
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 20)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button
                onClick={handleImportOpenAlex}
                isLoading={ingestFromOpenAlex.isPending}
                disabled={!queryInput || isLoading_}
              >
                <Download className="h-4 w-4 mr-2" />
                Import
              </Button>
            </div>
          </div>
        )

      case 'pubmed':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">PubMed Search Query</Label>
              <Input
                id="query"
                placeholder="e.g., cancer immunotherapy[MeSH]"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use PubMed search syntax for best results
              </p>
            </div>
            <div>
              <Label htmlFor="maxResults">Max Results</Label>
              <Input
                id="maxResults"
                type="number"
                min={1}
                max={100}
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 20)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button
                onClick={handleImportPubMed}
                isLoading={ingestFromPubMed.isPending}
                disabled={!queryInput || isLoading_}
              >
                <Download className="h-4 w-4 mr-2" />
                Import
              </Button>
            </div>
          </div>
        )

      case 'arxiv':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">arXiv Search Query</Label>
              <Input
                id="query"
                placeholder="e.g., quantum computing"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Search arXiv preprint repository
              </p>
            </div>
            <div>
              <Label htmlFor="category">Category (optional)</Label>
              <Input
                id="category"
                placeholder="e.g., cs.AI, physics.med-ph"
                value={arxivCategory}
                onChange={(e) => setArxivCategory(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Filter by arXiv category
              </p>
            </div>
            <div>
              <Label htmlFor="maxResults">Max Results</Label>
              <Input
                id="maxResults"
                type="number"
                min={1}
                max={100}
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 20)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button
                onClick={handleImportArxiv}
                isLoading={ingestFromArxiv.isPending}
                disabled={!queryInput || isLoading_}
              >
                <Download className="h-4 w-4 mr-2" />
                Import
              </Button>
            </div>
          </div>
        )

      case 'pdf':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="pdf">PDF File</Label>
              <div className="mt-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  id="pdf"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
                >
                  {selectedFile ? (
                    <div className="flex items-center justify-center gap-2">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <span className="text-sm">{selectedFile.name}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedFile(null)
                          if (fileInputRef.current) fileInputRef.current.value = ''
                        }}
                        className="ml-2 p-1 hover:bg-muted rounded"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">
                        Click to select a PDF file or drag and drop
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Max file size: 50MB
                      </p>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button
                onClick={handleUploadPdf}
                isLoading={uploadPdf.isPending}
                disabled={!selectedFile || isLoading_}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload
              </Button>
            </div>
          </div>
        )
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
                        {paper.one_line_pitch && (
                          <p className="text-sm font-medium text-primary mt-1 italic">
                            "{paper.one_line_pitch}"
                          </p>
                        )}
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
                        {paper.has_pdf && (
                          <Badge variant="secondary">PDF</Badge>
                        )}
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
          <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Import Papers</CardTitle>
              <button onClick={closeModal} className="p-1 hover:bg-muted rounded">
                <X className="h-5 w-5" />
              </button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mode Tabs */}
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'doi' as const, label: 'DOI' },
                  { id: 'openalex' as const, label: 'OpenAlex' },
                  { id: 'pubmed' as const, label: 'PubMed' },
                  { id: 'arxiv' as const, label: 'arXiv' },
                  { id: 'pdf' as const, label: 'PDF Upload' },
                ].map((tab) => (
                  <Button
                    key={tab.id}
                    variant={importMode === tab.id ? 'default' : 'outline'}
                    onClick={() => {
                      setImportMode(tab.id)
                      setImportResult(null)
                    }}
                    size="sm"
                  >
                    {tab.label}
                  </Button>
                ))}
              </div>

              {/* Import Result Message */}
              {importResult && (
                <div
                  className={`rounded-md p-3 text-sm ${
                    importResult.type === 'success'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                  }`}
                >
                  {importResult.message}
                </div>
              )}

              {/* Form for selected mode */}
              {renderImportForm()}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
