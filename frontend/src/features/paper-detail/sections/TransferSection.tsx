import { ArrowRightLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'

type TransferSectionProps = {
  show: boolean
  onStartTransfer: () => void
  onSyncToZotero: () => void
  isSyncingToZotero: boolean
  zoteroConnected: boolean
  onExport: (format: 'ris' | 'csljson') => void
}

export function TransferSection({
  show,
  onStartTransfer,
  onSyncToZotero,
  isSyncingToZotero,
  zoteroConnected,
  onExport,
}: TransferSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('papers.transferHubTitle')}</CardTitle>
        <CardDescription>{t('papers.transferHubDescription')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full" onClick={onStartTransfer}>
          <ArrowRightLeft className="h-4 w-4 mr-2" />
          {t('papers.startTransfer')}
        </Button>
        <Button
          variant="outline"
          className="w-full"
          onClick={onSyncToZotero}
          isLoading={isSyncingToZotero}
          disabled={!zoteroConnected}
        >
          {t('papers.syncToZotero')}
        </Button>
        <p className="text-xs text-muted-foreground">
          {zoteroConnected ? t('papers.zoteroConnected') : t('papers.zoteroNotConnected')}
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Button variant="outline" size="sm" onClick={() => onExport('ris')}>
            RIS
          </Button>
          <Button variant="outline" size="sm" onClick={() => onExport('csljson')}>
            CSL-JSON
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
