import { Loader2, TrendingUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { InnovationRadar } from '@/components/InnovationRadar'
import { cn, getScoreColor } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'
import type { PaperScore } from '@/types'

type ScoreDimension = {
  key: string
  label: string
  icon: LucideIcon
  color: string
  textColor: string
}

type ScoringSectionProps = {
  show: boolean
  scoreLoading: boolean
  score: PaperScore | null | undefined
  scoreDimensions: ScoreDimension[]
  onScore: () => void
  isScoring: boolean
}

export function ScoringSection({
  show,
  scoreLoading,
  score,
  scoreDimensions,
  onScore,
  isScoring,
}: ScoringSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          {t('papers.scores')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {scoreLoading ? (
          <div className="flex justify-center py-4">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        ) : score ? (
          <div className="space-y-4">
            <div className="text-center pb-4 border-b">
              <p className="text-sm text-muted-foreground">{t('papers.overallScore')}</p>
              <p className={cn('text-4xl font-bold', getScoreColor(score.overall_score))}>
                {score.overall_score.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {t('papers.confidence', { value: (score.confidence * 100).toFixed(0) })}
              </p>
            </div>

            <InnovationRadar
              scores={{
                novelty: score.novelty,
                ip_potential: score.ip_potential,
                marketability: score.marketability,
                feasibility: score.feasibility,
                commercialization: score.commercialization,
                team_readiness: score.team_readiness,
              }}
              size={220}
            />

            <div className="space-y-3">
              {scoreDimensions.map((dim) => {
                const value = score[dim.key as keyof PaperScore] as number
                return (
                  <div key={dim.key as string}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <dim.icon className={cn('h-3 w-3', dim.textColor)} />
                        {dim.label}
                      </span>
                      <span className="font-medium">{value.toFixed(1)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div
                        className={cn('h-full rounded-full transition-all', dim.color)}
                        style={{ width: `${value * 10}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-muted-foreground text-sm mb-4">{t('papers.notScoredYet')}</p>
            <Button onClick={onScore} isLoading={isScoring} className="w-full">
              <TrendingUp className="h-4 w-4 mr-2" />
              {t('papers.scoreNow')}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
