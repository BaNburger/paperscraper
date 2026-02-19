import { useTranslation } from 'react-i18next'
import { AccessibleModal } from '@/components/ui/AccessibleModal'
import { ImportByDoiForm } from '@/features/papers/import/ImportByDoiForm'
import { ImportBySourceQueryForm } from '@/features/papers/import/ImportBySourceQueryForm'
import { ImportPdfForm } from '@/features/papers/import/ImportPdfForm'
import { ImportModeTabs } from '@/features/papers/import/ImportModeTabs'
import type { ImportMode } from '@/features/papers/import/importModeConfig'

type ImportResult = {
  type: 'success' | 'error'
  message: string
}

type ImportModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  importMode: ImportMode
  onImportModeChange: (mode: ImportMode) => void
  importResult: ImportResult | null
  onClearImportResult: () => void
  doiInput: string
  onDoiInputChange: (value: string) => void
  queryInput: string
  onQueryInputChange: (value: string) => void
  maxResults: number
  onMaxResultsChange: (value: number) => void
  arxivCategory: string
  onArxivCategoryChange: (value: string) => void
  selectedFile: File | null
  onSelectFile: (file: File | null) => void
  onValidationError: (message: string) => void
  onImportDoi: () => void
  onImportOpenAlex: () => void
  onImportPubMed: () => void
  onImportArxiv: () => void
  onUploadPdf: () => void
  onCloseModal: () => void
  isImporting: boolean
  isDoiLoading: boolean
  isOpenAlexLoading: boolean
  isPubMedLoading: boolean
  isArxivLoading: boolean
  isPdfLoading: boolean
}

export function ImportModal({
  open,
  onOpenChange,
  importMode,
  onImportModeChange,
  importResult,
  onClearImportResult,
  doiInput,
  onDoiInputChange,
  queryInput,
  onQueryInputChange,
  maxResults,
  onMaxResultsChange,
  arxivCategory,
  onArxivCategoryChange,
  selectedFile,
  onSelectFile,
  onValidationError,
  onImportDoi,
  onImportOpenAlex,
  onImportPubMed,
  onImportArxiv,
  onUploadPdf,
  onCloseModal,
  isImporting,
  isDoiLoading,
  isOpenAlexLoading,
  isPubMedLoading,
  isArxivLoading,
  isPdfLoading,
}: ImportModalProps) {
  const { t } = useTranslation()

  const renderImportForm = () => {
    if (importMode === 'doi') {
      return (
        <ImportByDoiForm
          doiInput={doiInput}
          onDoiInputChange={onDoiInputChange}
          onCancel={onCloseModal}
          onImport={onImportDoi}
          isImporting={isImporting}
          isLoading={isDoiLoading}
        />
      )
    }

    if (importMode === 'openalex') {
      return (
        <ImportBySourceQueryForm
          source="openalex"
          queryInput={queryInput}
          onQueryInputChange={onQueryInputChange}
          maxResults={maxResults}
          onMaxResultsChange={onMaxResultsChange}
          arxivCategory={arxivCategory}
          onArxivCategoryChange={onArxivCategoryChange}
          onCancel={onCloseModal}
          onImport={onImportOpenAlex}
          isImporting={isImporting}
          isLoading={isOpenAlexLoading}
        />
      )
    }

    if (importMode === 'pubmed') {
      return (
        <ImportBySourceQueryForm
          source="pubmed"
          queryInput={queryInput}
          onQueryInputChange={onQueryInputChange}
          maxResults={maxResults}
          onMaxResultsChange={onMaxResultsChange}
          arxivCategory={arxivCategory}
          onArxivCategoryChange={onArxivCategoryChange}
          onCancel={onCloseModal}
          onImport={onImportPubMed}
          isImporting={isImporting}
          isLoading={isPubMedLoading}
        />
      )
    }

    if (importMode === 'arxiv') {
      return (
        <ImportBySourceQueryForm
          source="arxiv"
          queryInput={queryInput}
          onQueryInputChange={onQueryInputChange}
          maxResults={maxResults}
          onMaxResultsChange={onMaxResultsChange}
          arxivCategory={arxivCategory}
          onArxivCategoryChange={onArxivCategoryChange}
          onCancel={onCloseModal}
          onImport={onImportArxiv}
          isImporting={isImporting}
          isLoading={isArxivLoading}
        />
      )
    }

    return (
      <ImportPdfForm
        selectedFile={selectedFile}
        onSelectFile={onSelectFile}
        onValidationError={onValidationError}
        onImport={onUploadPdf}
        onCancel={onCloseModal}
        isImporting={isImporting}
        isLoading={isPdfLoading}
      />
    )
  }

  return (
    <AccessibleModal
      open={open}
      onOpenChange={onOpenChange}
      title={t('papers.importPapers')}
      description={t('papers.importDescription')}
      contentClassName="w-[min(95vw,48rem)]"
    >
      <div className="space-y-4">
        <ImportModeTabs
          importMode={importMode}
          onModeChange={(mode) => {
            onImportModeChange(mode)
            onClearImportResult()
          }}
        />

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

        <div role="tabpanel" id={`import-panel-${importMode}`} aria-labelledby={`import-tab-${importMode}`}>
          {renderImportForm()}
        </div>
      </div>
    </AccessibleModal>
  )
}
