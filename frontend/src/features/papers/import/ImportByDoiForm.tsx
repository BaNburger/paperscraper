import { useTranslation } from 'react-i18next'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'

type ImportByDoiFormProps = {
  doiInput: string
  onDoiInputChange: (value: string) => void
  onCancel: () => void
  onImport: () => void
  isImporting: boolean
  isLoading: boolean
}

export function ImportByDoiForm({
  doiInput,
  onDoiInputChange,
  onCancel,
  onImport,
  isImporting,
  isLoading,
}: ImportByDoiFormProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="doi">DOI</Label>
        <Input
          id="doi"
          placeholder="10.1234/example.123"
          value={doiInput}
          onChange={(e) => onDoiInputChange(e.target.value)}
        />
        <p className="text-xs text-muted-foreground mt-1">{t('papers.doiDescription')}</p>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          {t('common.cancel')}
        </Button>
        <Button onClick={onImport} isLoading={isLoading} disabled={!doiInput || isImporting}>
          <Download className="h-4 w-4 mr-2" />
          {t('common.import')}
        </Button>
      </div>
    </div>
  )
}
