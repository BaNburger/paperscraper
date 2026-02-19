import { BookOpen, ChevronRight, Sparkles, Users } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { AuthorBadge } from '@/components/AuthorBadge'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { cn, getScoreColor } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'
import type { PaperDetail, PaperScore } from '@/types'

type ScoreDimension = {
  key: string
  label: string
  icon: LucideIcon
  textColor: string
}

type PaperOverviewSectionProps = {
  show: boolean
  paper: PaperDetail
  showSimplified: boolean
  onShowSimplifiedChange: (value: boolean) => void
  hasBothAiSummaries: boolean
  onGenerateSimplified: () => void
  isGeneratingSimplified: boolean
  onGeneratePitch: () => void
  isGeneratingPitch: boolean
  onSelectAuthor: (authorId: string) => void
  score: PaperScore | null | undefined
  scoreDimensions: ScoreDimension[]
}

export function PaperOverviewSection({
  show,
  paper,
  showSimplified,
  onShowSimplifiedChange,
  hasBothAiSummaries,
  onGenerateSimplified,
  isGeneratingSimplified,
  onGeneratePitch,
  isGeneratingPitch,
  onSelectAuthor,
  score,
  scoreDimensions,
}: PaperOverviewSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              {t('papers.abstract')}
            </CardTitle>
            {paper.abstract && !hasBothAiSummaries && (
              <div className="flex items-center gap-2">
                {paper.simplified_abstract ? (
                  <div className="flex rounded-lg border p-0.5">
                    <Button
                      variant={!showSimplified ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => onShowSimplifiedChange(false)}
                      className="h-7 px-3"
                    >
                      {t('papers.original')}
                    </Button>
                    <Button
                      variant={showSimplified ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => onShowSimplifiedChange(true)}
                      className="h-7 px-3"
                    >
                      <Sparkles className="h-3 w-3 mr-1" />
                      {t('papers.simplified')}
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onGenerateSimplified}
                    isLoading={isGeneratingSimplified}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    {t('papers.simplify')}
                  </Button>
                )}
              </div>
            )}
          </div>
          {showSimplified && paper.simplified_abstract && !hasBothAiSummaries && (
            <CardDescription className="mt-1">{t('papers.simplifiedDescription')}</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {paper.one_line_pitch ? (
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-primary italic">&ldquo;{paper.one_line_pitch}&rdquo;</p>
                  {paper.simplified_abstract && (
                    <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                      {paper.simplified_abstract}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-muted/50 border border-dashed rounded-lg p-4 mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Sparkles className="h-4 w-4" />
                <span className="text-sm">{t('papers.noAiSummary')}</span>
              </div>
              <Button variant="outline" size="sm" onClick={onGeneratePitch} isLoading={isGeneratingPitch}>
                <Sparkles className="h-4 w-4 mr-2" />
                {t('papers.generateAiSummary')}
              </Button>
            </div>
          )}

          <p className="text-muted-foreground leading-relaxed">
            {showSimplified && paper.simplified_abstract && !hasBothAiSummaries
              ? paper.simplified_abstract
              : paper.abstract || t('papers.noAbstract')}
          </p>
        </CardContent>
      </Card>

      {paper.authors && paper.authors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              {t('papers.authorsCount', { count: paper.authors.length })}
            </CardTitle>
            <CardDescription>{t('papers.authorsDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {paper.authors.map((paperAuthor, index) => (
                <button
                  key={index}
                  onClick={() => onSelectAuthor(paperAuthor.author.id)}
                  className="w-full flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 transition-colors text-left"
                >
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium">{paperAuthor.author.name}</p>
                      <AuthorBadge
                        position={paperAuthor.position}
                        isCorresponding={paperAuthor.is_corresponding}
                        totalAuthors={paper.authors.length}
                      />
                    </div>
                    {paperAuthor.author.affiliations.length > 0 && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {paperAuthor.author.affiliations.join(', ')}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {paperAuthor.author.h_index && <Badge variant="outline">h-index: {paperAuthor.author.h_index}</Badge>}
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {score && (
        <Card>
          <CardHeader>
            <CardTitle>{t('papers.scoreAnalysis')}</CardTitle>
            <CardDescription>{t('papers.scoreAnalysisDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {scoreDimensions.map((dimension) => {
              const value = score[dimension.key as keyof PaperScore] as number
              const reasoning = score[`${dimension.key}_reasoning` as keyof PaperScore] as string
              return (
                <div key={dimension.key} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <dimension.icon className={cn('h-4 w-4', dimension.textColor)} />
                      <span className="font-medium">{dimension.label}</span>
                    </div>
                    <span className={cn('font-bold', getScoreColor(value))}>{value.toFixed(1)}/10</span>
                  </div>
                  <p className="text-sm text-muted-foreground pl-6">{reasoning || t('papers.noReasoning')}</p>
                </div>
              )
            })}
          </CardContent>
        </Card>
      )}
    </>
  )
}
