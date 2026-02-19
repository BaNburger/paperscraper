import { useTranslation } from 'react-i18next'
import { AccessibleModal } from '@/components/ui/AccessibleModal'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { getScoreColor, truncate } from '@/lib/utils'
import type { SearchResultItem } from '@/types'

type SearchScore = NonNullable<SearchResultItem['score']>

function ComparisonRadarChart({ papers }: { papers: { title: string; score: SearchScore }[] }) {
  const dimensions = [
    { key: 'overall_score', label: 'Overall' },
    { key: 'novelty', label: 'Novelty' },
    { key: 'ip_potential', label: 'IP' },
    { key: 'marketability', label: 'Market' },
    { key: 'feasibility', label: 'Feasibility' },
    { key: 'commercialization', label: 'Commercial' },
  ] as const

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']
  const size = 300
  const center = size / 2
  const radius = (size - 60) / 2

  const getPolygonPoints = (score: SearchScore): string =>
    dimensions
      .map((dim, i) => {
        const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2
        const value = (score[dim.key] as number) / 10
        const x = center + radius * value * Math.cos(angle)
        const y = center + radius * value * Math.sin(angle)
        return `${x},${y}`
      })
      .join(' ')

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        {[0.2, 0.4, 0.6, 0.8, 1].map((scale) => (
          <circle
            key={scale}
            cx={center}
            cy={center}
            r={radius * scale}
            fill="none"
            stroke="currentColor"
            strokeOpacity={0.1}
          />
        ))}

        {dimensions.map((_, i) => {
          const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2
          const x = center + radius * Math.cos(angle)
          const y = center + radius * Math.sin(angle)
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x}
              y2={y}
              stroke="currentColor"
              strokeOpacity={0.2}
            />
          )
        })}

        {dimensions.map((dim, i) => {
          const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2
          const x = center + (radius + 25) * Math.cos(angle)
          const y = center + (radius + 25) * Math.sin(angle)
          return (
            <text
              key={dim.key}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-xs fill-muted-foreground"
            >
              {dim.label}
            </text>
          )
        })}

        {papers.map((paper, idx) => (
          <polygon
            key={paper.title}
            points={getPolygonPoints(paper.score)}
            fill={colors[idx]}
            fillOpacity={0.2}
            stroke={colors[idx]}
            strokeWidth={2}
          />
        ))}
      </svg>

      <div className="flex flex-wrap gap-4 mt-4 justify-center">
        {papers.map((paper, idx) => (
          <div key={paper.title} className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[idx] }} />
            <span className="max-w-[150px] truncate">{paper.title}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

type ComparisonModalProps = {
  open: boolean
  papers: SearchResultItem[]
  onOpenChange: (open: boolean) => void
}

export function ComparisonModal({ open, papers, onOpenChange }: ComparisonModalProps) {
  const { t } = useTranslation()
  const papersWithScores = papers.filter((p) => p.score)

  return (
    <AccessibleModal
      open={open}
      onOpenChange={onOpenChange}
      title={t('search.paperComparison')}
      description={t('search.comparingPapers', { count: papers.length })}
      contentClassName="w-[min(95vw,72rem)]"
    >
      <div className="space-y-6">
        {papersWithScores.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>{t('search.scoreComparison')}</CardTitle>
              <CardDescription>{t('search.radarChartOverlay')}</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
              <ComparisonRadarChart
                papers={papersWithScores.map((p) => ({
                  title: p.title,
                  score: p.score!,
                }))}
              />
            </CardContent>
          </Card>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            {t('search.noScoresForComparison')}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>{t('search.metricComparison')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">{t('search.metric')}</th>
                    {papers.map((p) => (
                      <th key={p.id} className="text-center p-2 font-medium">
                        <div className="max-w-[150px]" title={p.title}>
                          {truncate(p.title, 30)}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.overallScore')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score ? (
                          <span className={getScoreColor(p.score.overall_score)}>
                            {p.score.overall_score.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.novelty')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.novelty?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.ipPotential')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.ip_potential?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.marketability')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.marketability?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.feasibility')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.feasibility?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.commercialization')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.score?.commercialization?.toFixed(1) ?? '-'}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('search.relevance')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {(p.relevance_score * 100).toFixed(0)}%
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-medium">{t('papers.source')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        <Badge variant="outline">{p.source}</Badge>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 font-medium">{t('search.published')}</td>
                    {papers.map((p) => (
                      <td key={p.id} className="text-center p-2">
                        {p.publication_date ? new Date(p.publication_date).toLocaleDateString() : '-'}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AccessibleModal>
  )
}
