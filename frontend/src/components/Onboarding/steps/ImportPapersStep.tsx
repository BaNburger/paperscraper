import { useState } from 'react'
import { FileText, Search, Upload, Check, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { papersApi } from '@/lib/api'
import { useIngestionRunPoller } from '@/hooks/useIngestionRuns'

type ImportMethod = 'doi' | 'openalex' | 'pdf'

interface ImportPapersStepProps {
  importedIds: string[]
  onImport: (ids: string[]) => void
  onNext: () => void
  onSkip: () => void
}

export function ImportPapersStep({
  importedIds,
  onImport,
  onNext,
  onSkip,
}: ImportPapersStepProps) {
  const { waitForRun } = useIngestionRunPoller()
  const [method, setMethod] = useState<ImportMethod>('doi')
  const [doi, setDoi] = useState('')
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const handleDoiImport = async () => {
    if (!doi.trim()) return
    setIsLoading(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const paper = await papersApi.ingestByDoi(doi.trim())
      onImport([paper.id])
      setSuccessMessage(`Imported: "${paper.title}"`)
      setDoi('')
    } catch (_err) {
      setError('Failed to import paper. Please check the DOI and try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpenAlexImport = async () => {
    if (!query.trim()) return
    setIsLoading(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const queued = await papersApi.ingestFromOpenAlex({ query: query.trim(), max_results: 5 })
      const result = await waitForRun(queued.ingest_run_id)
      if (result.papers_created > 0) {
        setSuccessMessage(`Successfully imported ${result.papers_created} paper(s)`)
      } else {
        setError('No new papers found. They may already exist in your library.')
      }
      setQuery('')
    } catch (_err) {
      setError('Failed to search OpenAlex. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsLoading(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const paper = await papersApi.uploadPdf(file)
      onImport([paper.id])
      setSuccessMessage(`Uploaded: "${paper.title}"`)
    } catch (_err) {
      setError('Failed to upload PDF. Please try again.')
    } finally {
      setIsLoading(false)
      e.target.value = ''
    }
  }

  const methods = [
    { id: 'doi' as ImportMethod, label: 'By DOI', icon: FileText },
    { id: 'openalex' as ImportMethod, label: 'Search OpenAlex', icon: Search },
    { id: 'pdf' as ImportMethod, label: 'Upload PDF', icon: Upload },
  ]

  return (
    <div className="space-y-6">
      <p className="text-center text-muted-foreground">
        Add papers to your library using any of these methods
      </p>

      {/* Method Selector */}
      <div className="flex justify-center gap-2">
        {methods.map((m) => {
          const Icon = m.icon
          return (
            <Button
              key={m.id}
              variant={method === m.id ? 'default' : 'outline'}
              onClick={() => {
                setMethod(m.id)
                setError(null)
                setSuccessMessage(null)
              }}
              className="gap-2"
            >
              <Icon className="h-4 w-4" />
              {m.label}
            </Button>
          )
        })}
      </div>

      {/* Import Form */}
      <div className="max-w-md mx-auto space-y-4">
        {method === 'doi' && (
          <div className="space-y-2">
            <Label htmlFor="doi">Enter DOI</Label>
            <div className="flex gap-2">
              <Input
                id="doi"
                placeholder="e.g., 10.1038/nature12373"
                value={doi}
                onChange={(e) => setDoi(e.target.value)}
                disabled={isLoading}
              />
              <Button onClick={handleDoiImport} disabled={!doi.trim() || isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Import'}
              </Button>
            </div>
          </div>
        )}

        {method === 'openalex' && (
          <div className="space-y-2">
            <Label htmlFor="query">Search query</Label>
            <div className="flex gap-2">
              <Input
                id="query"
                placeholder="e.g., CRISPR gene editing"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
              />
              <Button onClick={handleOpenAlexImport} disabled={!query.trim() || isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Imports up to 5 papers matching your search
            </p>
          </div>
        )}

        {method === 'pdf' && (
          <div className="space-y-2">
            <Label>Upload PDF file</Label>
            <div className="border-2 border-dashed rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".pdf"
                onChange={handlePdfUpload}
                className="hidden"
                id="pdf-upload"
                disabled={isLoading}
              />
              <label
                htmlFor="pdf-upload"
                className={cn(
                  'cursor-pointer flex flex-col items-center gap-2',
                  isLoading && 'opacity-50 cursor-not-allowed'
                )}
              >
                {isLoading ? (
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                ) : (
                  <Upload className="h-8 w-8 text-muted-foreground" />
                )}
                <span className="text-sm text-muted-foreground">
                  Click to upload a PDF
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Status Messages */}
        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            {error}
          </div>
        )}
        {successMessage && (
          <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-3 rounded-lg">
            <Check className="h-4 w-4 flex-shrink-0" />
            {successMessage}
          </div>
        )}

        {/* Imported Count */}
        {importedIds.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            {importedIds.length} paper(s) imported in this session
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-center gap-4 pt-4">
        <Button variant="outline" onClick={onSkip}>
          Skip for now
        </Button>
        <Button onClick={onNext} disabled={importedIds.length === 0}>
          Continue
        </Button>
      </div>
    </div>
  )
}
