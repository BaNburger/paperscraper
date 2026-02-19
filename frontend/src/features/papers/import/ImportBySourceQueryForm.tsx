import { useTranslation } from 'react-i18next'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'

type Source = 'openalex' | 'pubmed' | 'arxiv'

type ImportBySourceQueryFormProps = {
  source: Source
  queryInput: string
  onQueryInputChange: (value: string) => void
  maxResults: number
  onMaxResultsChange: (value: number) => void
  arxivCategory: string
  onArxivCategoryChange: (value: string) => void
  onCancel: () => void
  onImport: () => void
  isImporting: boolean
  isLoading: boolean
}

const sourceCopy: Record<Source, { queryLabel: string; queryPlaceholder: string; description: string }> = {
  openalex: {
    queryLabel: 'papers.searchQuery',
    queryPlaceholder: 'e.g., machine learning healthcare',
    description: 'papers.openAlexDescription',
  },
  pubmed: {
    queryLabel: 'papers.pubmedSearchQuery',
    queryPlaceholder: 'e.g., cancer immunotherapy[MeSH]',
    description: 'papers.pubmedDescription',
  },
  arxiv: {
    queryLabel: 'papers.arxivSearchQuery',
    queryPlaceholder: 'e.g., quantum computing',
    description: 'papers.arxivDescription',
  },
}

export function ImportBySourceQueryForm({
  source,
  queryInput,
  onQueryInputChange,
  maxResults,
  onMaxResultsChange,
  arxivCategory,
  onArxivCategoryChange,
  onCancel,
  onImport,
  isImporting,
  isLoading,
}: ImportBySourceQueryFormProps) {
  const { t } = useTranslation()
  const copy = sourceCopy[source]

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="query">{t(copy.queryLabel)}</Label>
        <Input
          id="query"
          placeholder={copy.queryPlaceholder}
          value={queryInput}
          onChange={(e) => onQueryInputChange(e.target.value)}
        />
        <p className="text-xs text-muted-foreground mt-1">{t(copy.description)}</p>
      </div>

      {source === 'arxiv' && (
        <div>
          <Label htmlFor="category">{t('papers.categoryOptional')}</Label>
          <Input
            id="category"
            placeholder="e.g., cs.AI, physics.med-ph"
            value={arxivCategory}
            onChange={(e) => onArxivCategoryChange(e.target.value)}
          />
          <p className="text-xs text-muted-foreground mt-1">{t('papers.categoryDescription')}</p>
        </div>
      )}

      <div>
        <Label htmlFor="maxResults">{t('papers.maxResults')}</Label>
        <Input
          id="maxResults"
          type="number"
          min={1}
          max={100}
          value={maxResults}
          onChange={(e) => onMaxResultsChange(parseInt(e.target.value, 10) || 20)}
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          {t('common.cancel')}
        </Button>
        <Button onClick={onImport} isLoading={isLoading} disabled={!queryInput || isImporting}>
          <Download className="h-4 w-4 mr-2" />
          {t('common.import')}
        </Button>
      </div>
    </div>
  )
}
