import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import {
  usePapers,
  useProjects,
  useIngestByDoi,
  useIngestFromOpenAlex,
  useIngestFromPubMed,
  useIngestFromArxiv,
  useUploadPdf,
} from '@/hooks'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'
import { useToast } from '@/components/ui/Toast'
import { Download, Plus, Search, UsersRound } from 'lucide-react'
import { WorkflowBanner } from '@/components/workflow/WorkflowBanner'
import { exportApi } from '@/api'
import { getApiErrorMessage } from '@/types'
import { ImportModal } from '@/features/papers/import/ImportModal'
import { type ImportMode } from '@/features/papers/import/importModeConfig'
import { PapersList } from '@/features/papers/list/PapersList'

export function PapersPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  const page = parseInt(searchParams.get('page') ?? '1', 10)
  const search = searchParams.get('search') ?? ''
  const pageSize = 10

  const [searchInput, setSearchInput] = useState(search)
  const [showImportModal, setShowImportModal] = useState(false)
  const [importMode, setImportMode] = useState<ImportMode>('doi')

  const [doiInput, setDoiInput] = useState('')
  const [queryInput, setQueryInput] = useState('')
  const [maxResults, setMaxResults] = useState(20)
  const [arxivCategory, setArxivCategory] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const [importResult, setImportResult] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)
  const [exportingFormat, setExportingFormat] = useState<'ris' | 'csljson' | null>(null)

  const { data, isLoading, error } = usePapers({ page, page_size: pageSize, search })
  const { data: projectsData } = useProjects()
  const ingestByDoi = useIngestByDoi()
  const ingestFromOpenAlex = useIngestFromOpenAlex()
  const ingestFromPubMed = useIngestFromPubMed()
  const ingestFromArxiv = useIngestFromArxiv()
  const uploadPdf = useUploadPdf()

  useEffect(() => {
    if (searchParams.get('import') !== 'true') return

    const openFrame = window.requestAnimationFrame(() => {
      setShowImportModal(true)
      const nextParams = new URLSearchParams(searchParams)
      nextParams.delete('import')
      setSearchParams(nextParams, { replace: true })
    })

    return () => window.cancelAnimationFrame(openFrame)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const resetImportState = () => {
    setDoiInput('')
    setQueryInput('')
    setMaxResults(20)
    setArxivCategory('')
    setSelectedFile(null)
    setImportResult(null)
  }

  const closeModal = () => {
    setShowImportModal(false)
    resetImportState()
  }

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault()
    setSearchParams({ search: searchInput, page: '1' })
  }

  const handlePageChange = (nextPage: number) => {
    setSearchParams({ search, page: nextPage.toString() })
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
        message:
          result.papers_skipped > 0
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
        message:
          result.papers_skipped > 0
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
        message:
          result.papers_skipped > 0
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
    } catch {
      setImportResult({ type: 'error', message: t('papers.pdfUploadFailed') })
    }
  }

  const handleQuickExport = async (format: 'ris' | 'csljson') => {
    try {
      setExportingFormat(format)
      const blob = format === 'ris' ? await exportApi.exportRis() : await exportApi.exportCslJson()
      const dateSuffix = new Date().toISOString().slice(0, 10)
      exportApi.downloadFile(blob, `papers_export_${dateSuffix}.${format === 'ris' ? 'ris' : 'json'}`)
      toast.success(t('papers.exportSuccessTitle'), t('papers.exportSuccessDescription'))
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.exportFailed'))
      toast.error(t('papers.exportFailedTitle'), message)
    } finally {
      setExportingFormat(null)
    }
  }

  const isImporting =
    ingestByDoi.isPending ||
    ingestFromOpenAlex.isPending ||
    ingestFromPubMed.isPending ||
    ingestFromArxiv.isPending ||
    uploadPdf.isPending

  return (
    <div className="space-y-6" data-testid="papers-page">
      <PageHeader
        title={t('papers.title')}
        description={t('papers.subtitle')}
        actions={
          <>
            <Button
              variant="outline"
              onClick={() => {
                void handleQuickExport('ris')
              }}
              isLoading={exportingFormat === 'ris'}
            >
              <Download className="h-4 w-4 mr-2" />
              RIS
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                void handleQuickExport('csljson')
              }}
              isLoading={exportingFormat === 'csljson'}
            >
              <Download className="h-4 w-4 mr-2" />
              CSL-JSON
            </Button>
            <Button onClick={() => setShowImportModal(true)} data-testid="papers-open-import">
              <Plus className="h-4 w-4 mr-2" />
              {t('papers.importPapers')}
            </Button>
          </>
        }
      />

      <WorkflowBanner
        bannerId="papers-to-projects"
        icon={UsersRound}
        message={t('workflow.banner.readyToEvaluate', 'You have papers in your library. Create a project to start evaluating them.')}
        ctaLabel={t('workflow.banner.readyToEvaluateCta', 'Create Project')}
        ctaPath="/projects"
        condition={(data?.total ?? 0) > 0 && (projectsData?.total ?? 0) === 0}
        variant="green"
      />

      <form onSubmit={handleSearch} className="flex gap-2" data-testid="papers-search-form">
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

      <PapersList
        data={data}
        isLoading={isLoading}
        error={error}
        search={search}
        page={page}
        pageSize={pageSize}
        onOpenImport={() => setShowImportModal(true)}
        onClearSearch={() => {
          setSearchInput('')
          setSearchParams({})
        }}
        onPageChange={handlePageChange}
      />

      <ImportModal
        open={showImportModal}
        onOpenChange={(open) => {
          if (!open) {
            closeModal()
            return
          }
          setShowImportModal(true)
        }}
        importMode={importMode}
        onImportModeChange={setImportMode}
        importResult={importResult}
        onClearImportResult={() => setImportResult(null)}
        doiInput={doiInput}
        onDoiInputChange={setDoiInput}
        queryInput={queryInput}
        onQueryInputChange={setQueryInput}
        maxResults={maxResults}
        onMaxResultsChange={setMaxResults}
        arxivCategory={arxivCategory}
        onArxivCategoryChange={setArxivCategory}
        selectedFile={selectedFile}
        onSelectFile={(file) => {
          setSelectedFile(file)
          if (file) {
            setImportResult(null)
          }
        }}
        onValidationError={(message) => {
          setImportResult({ type: 'error', message })
        }}
        onImportDoi={() => {
          void handleImportDoi()
        }}
        onImportOpenAlex={() => {
          void handleImportOpenAlex()
        }}
        onImportPubMed={() => {
          void handleImportPubMed()
        }}
        onImportArxiv={() => {
          void handleImportArxiv()
        }}
        onUploadPdf={() => {
          void handleUploadPdf()
        }}
        onCloseModal={closeModal}
        isImporting={isImporting}
        isDoiLoading={ingestByDoi.isPending}
        isOpenAlexLoading={ingestFromOpenAlex.isPending}
        isPubMedLoading={ingestFromPubMed.isPending}
        isArxivLoading={ingestFromArxiv.isPending}
        isPdfLoading={uploadPdf.isPending}
      />
    </div>
  )
}
