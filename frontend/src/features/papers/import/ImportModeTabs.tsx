import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import { importModeConfig, type ImportMode } from '@/features/papers/import/importModeConfig'

type ImportModeTabsProps = {
  importMode: ImportMode
  onModeChange: (mode: ImportMode) => void
}

export function ImportModeTabs({ importMode, onModeChange }: ImportModeTabsProps) {
  const { t } = useTranslation()

  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label={t('papers.importPapers')}>
      {importModeConfig.map((tab) => (
        <Button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={importMode === tab.id}
          aria-controls={`import-panel-${tab.id}`}
          id={`import-tab-${tab.id}`}
          variant={importMode === tab.id ? 'default' : 'outline'}
          onClick={() => onModeChange(tab.id)}
          size="sm"
        >
          {tab.label.includes('.') ? t(tab.label) : tab.label}
        </Button>
      ))}
    </div>
  )
}
