import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import {
  usePapers,
  useIngestByDoi,
  useIngestFromOpenAlex,
  useIngestFromPubMed,
  useIngestFromArxiv,
  useUploadPdf,
} from '@/hooks'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { AccessibleModal } from '@/components/ui/AccessibleModal'
import {
  FileText,
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  Download,
  Upload,
  X,
  SearchX,
} from 'lucide-react'
import { formatDate, truncate } from '@/lib/utils'

type ImportMode = 'doi' | 'openalex' | 'pubmed' | 'arxiv' | 'pdf'

export function PapersPage() {
  const { t } = useTranslation()
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

  useEffect(() => {
    if (searchParams.get('import') !== 'true') return
    const openFrame = window.requestAnimationFrame(() => setShowImportModal(true))
    const nextParams = new URLSearchParams(searchParams)
    nextParams.delete('import')
    setSearchParams(nextParams, { replace: true })
    return () => window.cancelAnimationFrame(openFrame)
  }, [searchParams, setSearchParams])

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
      setImportResult({ type: 'success', message: t('papers.importSuccess') })
      setDoiInput('')
    } catch {
      setImportResult({ type: 'error', message: t('papers.importDoiFailed') })
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
        message: result.papers_skipped > 0
          ? t('papers.importedWithSkipped', { created: result.papers_created, skipped: result.papers_skipped })
          : t('papers.importedCount', { count: result.papers_created }),
      })
      setQueryInput('')
    } catch {
      setImportResult({ type: 'error', message: t('papers.importOpenAlexFailed') })
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
        message: result.papers_skipped > 0
          ? t('papers.importedWithSkipped', { created: result.papers_created, skipped: result.papers_skipped })
          : t('papers.importedCount', { count: result.papers_created }),
      })
      setQueryInput('')
    } catch {
      setImportResult({ type: 'error', message: t('papers.importPubMedFailed') })
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
        message: result.papers_skipped > 0
          ? t('papers.importedWithSkipped', { created: result.papers_created, skipped: result.papers_skipped })
          : t('papers.importedCount', { count: result.papers_created }),
      })
      setQueryInput('')
    } catch {
      setImportResult({ type: 'error', message: t('papers.importArxivFailed') })
    }
  }

  const handleUploadPdf = async () => {
    if (!selectedFile) return
    try {
      await uploadPdf.mutateAsync(selectedFile)
      setImportResult({ type: 'success', message: t('papers.pdfUploadSuccess') })
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch {
      setImportResult({ type: 'error', message: t('papers.pdfUploadFailed') })
    }
  }

  const MAX_PDF_SIZE_MB = 50
  const MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf') {
      setImportResult({ type: 'error', message: t('papers.invalidPdfFile') })
      return
    }

    if (file.size > MAX_PDF_SIZE_BYTES) {
      setImportResult({
        type: 'error',
        message: t('papers.fileTooLarge', { size: MAX_PDF_SIZE_MB }),
      })
      return
    }

    setSelectedFile(file)
    setImportResult(null)
  }

  const isImporting =
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
                {t('papers.doiDescription')}
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleImportDoi}
                isLoading={ingestByDoi.isPending}
                disabled={!doiInput || isImporting}
              >
                <Download className="h-4 w-4 mr-2" />
                {t('common.import')}
              </Button>
            </div>
          </div>
        )

      case 'openalex':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">{t('papers.searchQuery')}</Label>
              <Input
                id="query"
                placeholder="e.g., machine learning healthcare"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                {t('papers.openAlexDescription')}
              </p>
            </div>
            <div>
              <Label htmlFor="maxResults">{t('papers.maxResults')}</Label>
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
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleImportOpenAlex}
                isLoading={ingestFromOpenAlex.isPending}
                disabled={!queryInput || isImporting}
              >
                <Download className="h-4 w-4 mr-2" />
                {t('common.import')}
              </Button>
            </div>
          </div>
        )

      case 'pubmed':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">{t('papers.pubmedSearchQuery')}</Label>
              <Input
                id="query"
                placeholder="e.g., cancer immunotherapy[MeSH]"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                {t('papers.pubmedDescription')}
              </p>
            </div>
            <div>
              <Label htmlFor="maxResults">{t('papers.maxResults')}</Label>
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
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleImportPubMed}
                isLoading={ingestFromPubMed.isPending}
                disabled={!queryInput || isImporting}
              >
                <Download className="h-4 w-4 mr-2" />
                {t('common.import')}
              </Button>
            </div>
          </div>
        )

      case 'arxiv':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">{t('papers.arxivSearchQuery')}</Label>
              <Input
                id="query"
                placeholder="e.g., quantum computing"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                {t('papers.arxivDescription')}
              </p>
            </div>
            <div>
              <Label htmlFor="category">{t('papers.categoryOptional')}</Label>
              <Input
                id="category"
                placeholder="e.g., cs.AI, physics.med-ph"
                value={arxivCategory}
                onChange={(e) => setArxivCategory(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                {t('papers.categoryDescription')}
              </p>
            </div>
            <div>
              <Label htmlFor="maxResults">{t('papers.maxResults')}</Label>
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
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleImportArxiv}
                isLoading={ingestFromArxiv.isPending}
                disabled={!queryInput || isImporting}
              >
                <Download className="h-4 w-4 mr-2" />
                {t('common.import')}
              </Button>
            </div>
          </div>
        )

      case 'pdf':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="pdf">{t('papers.pdfFile')}</Label>
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
                        aria-label={t('papers.removeSelectedFile')}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">
                        {t('papers.pdfDropzone')}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {t('papers.maxFileSize', { size: 50 })}
                      </p>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleUploadPdf}
                isLoading={uploadPdf.isPending}
                disabled={!selectedFile || isImporting}
              >
                <Upload className="h-4 w-4 mr-2" />
                {t('papers.upload')}
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
          <h1 className="text-3xl font-bold">{t('papers.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('papers.subtitle')}
          </p>
        </div>
        <Button onClick={() => setShowImportModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('papers.importPapers')}
        </Button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t('papers.searchPlaceholder')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button type="submit">{t('common.search')}</Button>
      </form>

      {/* Papers List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            {t('papers.loadFailed')}
          </CardContent>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent>
            {search ? (
              <EmptyState
                icon={<SearchX className="h-16 w-16" />}
                title={t('papers.noSearchResults')}
                description={t('papers.noSearchResultsDescription')}
                action={{
                  label: t('papers.clearSearch'),
                  onClick: () => {
                    setSearchInput('')
                    setSearchParams({})
                  },
                }}
              />
            ) : (
              <EmptyState
                icon={<FileText className="h-16 w-16" />}
                title={t('papers.noPapers')}
                description={t('papers.noPapersStartDescription')}
                action={{
                  label: t('papers.importPapers'),
                  onClick: () => setShowImportModal(true),
                }}
              />
            )}
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
                          {truncate(paper.abstract ?? t('papers.noAbstract'), 200)}
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
                            {t('papers.citationsCount', { count: paper.citations_count })}
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
                {t('papers.showingResults', { from: (page - 1) * pageSize + 1, to: Math.min(page * pageSize, data.total), total: data.total })}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  {t('common.previous')}
                </Button>
                <span className="text-sm">
                  {t('common.pageOf', { page, pages: data.pages })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= data.pages}
                >
                  {t('common.next')}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      <AccessibleModal
        open={showImportModal}
        onOpenChange={(open) => {
          if (!open) {
            closeModal()
          }
        }}
        title={t('papers.importPapers')}
        description={t('papers.importDescription')}
        contentClassName="w-[min(95vw,48rem)]"
      >
        <div className="space-y-4">
          <div
            className="flex flex-wrap gap-2"
            role="tablist"
            aria-label={t('papers.importPapers')}
          >
            {[
              { id: 'doi' as const, label: 'DOI' },
              { id: 'openalex' as const, label: 'OpenAlex' },
              { id: 'pubmed' as const, label: 'PubMed' },
              { id: 'arxiv' as const, label: 'arXiv' },
              { id: 'pdf' as const, label: t('papers.pdfUpload') },
            ].map((tab) => (
              <Button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={importMode === tab.id}
                aria-controls={`import-panel-${tab.id}`}
                id={`import-tab-${tab.id}`}
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

          {importResult && (
            <div
              className={`rounded-md p-3 text-sm ${
                importResult.type === 'success'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
              }`}
              role={importResult.type === 'error' ? 'alert' : 'status'}
            >
              {importResult.message}
            </div>
          )}

          <div
            role="tabpanel"
            id={`import-panel-${importMode}`}
            aria-labelledby={`import-tab-${importMode}`}
          >
            {renderImportForm()}
          </div>
        </div>
      </AccessibleModal>
    </div>
  )
}
