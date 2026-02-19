import { Loader2, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import type { PaperHighlight } from '@/types'

type HighlightsSectionProps = {
  show: boolean
  readerAvailable: boolean
  highlightsLoading: boolean
  highlightItems: PaperHighlight[]
  onGenerateHighlights: () => void
  isGenerating: boolean
  onFocusHighlight: (chunkId: string | null | undefined, chunkRef: string) => void
}

export function HighlightsSection({
  show,
  readerAvailable,
  highlightsLoading,
  highlightItems,
  onGenerateHighlights,
  isGenerating,
  onFocusHighlight,
}: HighlightsSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              {t('papers.insightsTitle')}
            </CardTitle>
            <CardDescription>{t('papers.insightsDescription')}</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onGenerateHighlights}
            isLoading={isGenerating}
            disabled={!readerAvailable}
          >
            {t('papers.generate')}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {highlightsLoading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        ) : !readerAvailable ? (
          <p className="text-sm text-muted-foreground">{t('papers.insightsNeedReader')}</p>
        ) : !highlightItems.length ? (
          <div className="rounded-lg border border-dashed p-4 text-center">
            <p className="text-sm text-muted-foreground mb-3">{t('papers.noHighlights')}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={onGenerateHighlights}
              isLoading={isGenerating}
            >
              {t('papers.generateHighlights')}
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {highlightItems.map((highlight) => (
              <button
                key={highlight.id}
                onClick={() => onFocusHighlight(highlight.chunk_id, highlight.chunk_ref)}
                className="w-full rounded-lg border p-3 text-left transition-colors hover:bg-muted/30"
              >
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
                  {highlight.source}
                </p>
                <p className="text-sm font-medium line-clamp-2">{highlight.quote}</p>
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                  {highlight.insight_summary}
                </p>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
