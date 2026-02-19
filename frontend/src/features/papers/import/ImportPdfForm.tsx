import { Upload, FileText, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useRef } from 'react'
import { Button } from '@/components/ui/Button'
import { Label } from '@/components/ui/Label'

type ImportPdfFormProps = {
  selectedFile: File | null
  onSelectFile: (file: File | null) => void
  onValidationError: (message: string) => void
  onImport: () => void
  onCancel: () => void
  isImporting: boolean
  isLoading: boolean
}

const MAX_PDF_SIZE_MB = 50
const MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

export function ImportPdfForm({
  selectedFile,
  onSelectFile,
  onValidationError,
  onImport,
  onCancel,
  isImporting,
  isLoading,
}: ImportPdfFormProps) {
  const { t } = useTranslation()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf') {
      onValidationError(t('papers.invalidPdfFile'))
      return
    }
    if (file.size > MAX_PDF_SIZE_BYTES) {
      onValidationError(t('papers.fileTooLarge', { size: MAX_PDF_SIZE_MB }))
      return
    }
    onSelectFile(file)
  }

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
                  onClick={(event) => {
                    event.stopPropagation()
                    onSelectFile(null)
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
                <p className="text-sm text-muted-foreground">{t('papers.pdfDropzone')}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {t('papers.maxFileSize', { size: MAX_PDF_SIZE_MB })}
                </p>
              </>
            )}
          </div>
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          {t('common.cancel')}
        </Button>
        <Button onClick={onImport} isLoading={isLoading} disabled={!selectedFile || isImporting}>
          <Upload className="h-4 w-4 mr-2" />
          {t('papers.upload')}
        </Button>
      </div>
    </div>
  )
}
