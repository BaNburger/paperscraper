import { BookOpen, Link as LinkIcon, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { cn } from '@/lib/utils'
import type { ReaderPayload } from '@/types'

type ReaderSectionProps = {
  show: boolean
  readerData: ReaderPayload | null | undefined
  readerLoading: boolean
  readerChunks: ReaderPayload['chunks']
  activeChunkId: string | null
  chunkRefs: React.MutableRefObject<Record<string, HTMLDivElement | null>>
  onHydrate: () => void
  isHydrating: boolean
}

export function ReaderSection({
  show,
  readerData,
  readerLoading,
  readerChunks,
  activeChunkId,
  chunkRefs,
  onHydrate,
  isHydrating,
}: ReaderSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              {t('papers.readerTitle')}
            </CardTitle>
            <CardDescription>{t('papers.readerDescription')}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {readerData?.status?.available ? (
              <Badge variant="secondary" className="capitalize">
                {readerData.status.source || 'full-text'}
              </Badge>
            ) : (
              <Badge variant="outline">{t('papers.readerUnavailableShort')}</Badge>
            )}
            <Button variant="outline" size="sm" onClick={onHydrate} isLoading={isHydrating}>
              <LinkIcon className="h-4 w-4 mr-2" />
              {readerData?.status?.available ? t('papers.readerRehydrate') : t('papers.readerHydrate')}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {readerLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        ) : !readerData?.status?.available || !readerChunks.length ? (
          <div className="rounded-lg border border-dashed p-6 text-center">
            <p className="text-sm text-muted-foreground mb-4">{t('papers.readerUnavailableDescription')}</p>
            <Button variant="outline" onClick={onHydrate} isLoading={isHydrating}>
              {t('papers.readerHydrate')}
            </Button>
          </div>
        ) : (
          <div className="max-h-[680px] overflow-y-auto rounded-lg border bg-background">
            <div className="space-y-4 p-4">
              {readerChunks.map((chunk) => (
                <div
                  key={chunk.id}
                  ref={(element) => {
                    chunkRefs.current[chunk.id] = element
                  }}
                  className={cn(
                    'rounded-md border p-3 text-sm leading-relaxed transition-colors',
                    activeChunkId === chunk.id ? 'border-primary bg-primary/5' : 'border-transparent'
                  )}
                >
                  <div className="mb-2 text-xs text-muted-foreground">
                    {t('papers.chunkLabel', { index: chunk.chunk_index + 1 })}
                  </div>
                  <p className="whitespace-pre-wrap">{chunk.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
