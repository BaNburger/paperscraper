import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import {
  useDashboardSummary,
  usePaperAnalytics,
  useTeamOverview,
  useFunnelAnalytics,
  useBenchmarks,
  useScheduledReports,
  useCreateScheduledReport,
  useDeleteScheduledReport,
  useRunScheduledReport,
  useUpdateScheduledReport,
} from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { EmptyState } from '@/components/ui/EmptyState'
import { ContentSkeleton } from '@/components/ui/PageSkeleton'
import {
  FileText,
  TrendingUp,
  Users,
  FolderKanban,
  Download,
  BarChart3,
  PieChart,
  Activity,
  ArrowUp,
  Filter,
  ArrowRight,
  Target,
  Award,
  CalendarClock,
  Plus,
  Play,
  Trash2,
  Mail,
  Clock,
} from 'lucide-react'
import { exportApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { ReportType, ReportSchedule, ScheduledReport } from '@/types'
import type { FunnelStage, BenchmarkMetric } from '@/types'

type AnalyticsTab = 'overview' | 'funnel' | 'benchmarks' | 'reports'

// Simple bar chart component
function SimpleBarChart({
  data,
  height = 200,
  label,
}: {
  data: { name: string; value: number }[]
  height?: number
  label?: string
}) {
  const maxValue = Math.max(...data.map((d) => d.value), 1)

  return (
    <div className="space-y-2">
      {label && <p className="text-sm text-muted-foreground mb-4">{label}</p>}
      <div className="flex items-end gap-2" style={{ height }}>
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-xs font-medium">{item.value}</span>
            <div
              className="w-full bg-primary/80 rounded-t transition-all hover:bg-primary"
              style={{
                height: `${(item.value / maxValue) * (height - 40)}px`,
                minHeight: item.value > 0 ? '4px' : '0px',
              }}
            />
            <span className="text-xs text-muted-foreground truncate w-full text-center">
              {item.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Comparison bar chart for benchmarks
function ComparisonBarChart({
  data,
}: {
  data: BenchmarkMetric[]
}) {
  const maxValue = Math.max(...data.flatMap((d) => [d.org_value, d.benchmark_value]), 1)

  return (
    <div className="space-y-4">
      {data.map((metric, index) => (
        <div key={index} className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{metric.label}</span>
            <span className="text-muted-foreground">
              {metric.org_value.toFixed(1)}{metric.unit} vs {metric.benchmark_value.toFixed(1)}{metric.unit}
            </span>
          </div>
          <div className="flex gap-2" style={{ height: 24 }}>
            <div className="flex-1 bg-muted rounded overflow-hidden">
              <div
                className={cn(
                  'h-full transition-all',
                  metric.higher_is_better
                    ? metric.org_value >= metric.benchmark_value
                      ? 'bg-green-500'
                      : 'bg-orange-500'
                    : metric.org_value <= metric.benchmark_value
                      ? 'bg-green-500'
                      : 'bg-orange-500'
                )}
                style={{ width: `${(metric.org_value / maxValue) * 100}%` }}
              />
            </div>
            <div className="flex-1 bg-muted rounded overflow-hidden">
              <div
                className="h-full bg-blue-500/50"
                style={{ width: `${(metric.benchmark_value / maxValue) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-primary" />
              Your org
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-blue-500/50" />
              Platform avg
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// Simple line chart component
function SimpleLineChart({
  data,
  height = 150,
}: {
  data: { date: string; count: number }[]
  height?: number
}) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground" style={{ height }}>
        No data available
      </div>
    )
  }

  const maxValue = Math.max(...data.map((d) => d.count), 1)
  const points = data.map((d, i) => ({
    x: (i / Math.max(data.length - 1, 1)) * 100,
    y: 100 - (d.count / maxValue) * 100,
    value: d.count,
    date: d.date,
  }))

  const pathD = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')

  return (
    <div className="relative" style={{ height }}>
      <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
        {/* Grid lines */}
        <line x1="0" y1="25" x2="100" y2="25" stroke="currentColor" strokeOpacity="0.1" />
        <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" strokeOpacity="0.1" />
        <line x1="0" y1="75" x2="100" y2="75" stroke="currentColor" strokeOpacity="0.1" />

        {/* Line */}
        <path d={pathD} fill="none" stroke="hsl(var(--primary))" strokeWidth="2" vectorEffect="non-scaling-stroke" />

        {/* Area fill */}
        <path
          d={`${pathD} L 100 100 L 0 100 Z`}
          fill="hsl(var(--primary))"
          fillOpacity="0.1"
        />

        {/* Points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="2"
            fill="hsl(var(--primary))"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className="flex justify-between text-xs text-muted-foreground mt-2">
        <span>{data[0]?.date}</span>
        <span>{data[data.length - 1]?.date}</span>
      </div>
    </div>
  )
}

// Simple pie/donut chart
function SimpleDonutChart({
  data,
  size = 120,
}: {
  data: { name: string; value: number; color: string }[]
  size?: number
}) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  if (total === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground" style={{ width: size, height: size }}>
        No data
      </div>
    )
  }

  let currentAngle = -90

  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} viewBox="0 0 100 100">
        {data.map((item, index) => {
          const angle = (item.value / total) * 360
          const startAngle = currentAngle
          currentAngle += angle

          const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180)
          const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180)
          const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180)
          const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180)

          const largeArcFlag = angle > 180 ? 1 : 0

          return (
            <path
              key={index}
              d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
              fill={item.color}
              stroke="white"
              strokeWidth="1"
            />
          )
        })}
        <circle cx="50" cy="50" r="25" fill="white" />
        <text x="50" y="50" textAnchor="middle" dominantBaseline="middle" className="text-lg font-bold" fill="currentColor">
          {total}
        </text>
      </svg>
      <div className="space-y-1">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
            <span className="text-muted-foreground">{item.name}</span>
            <span className="font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Funnel visualization component
function FunnelChart({ stages }: { stages: FunnelStage[] }) {
  const maxCount = Math.max(...stages.map((s) => s.count), 1)
  const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']

  return (
    <div className="space-y-3">
      {stages.map((stage, index) => (
        <div key={stage.stage} className="relative">
          <div className="flex items-center gap-4">
            <div className="w-32 text-sm font-medium text-right">{stage.label}</div>
            <div className="flex-1">
              <div
                className="h-10 rounded-r-lg flex items-center justify-end pr-3 transition-all"
                style={{
                  width: `${Math.max((stage.count / maxCount) * 100, 10)}%`,
                  backgroundColor: colors[index % colors.length],
                }}
              >
                <span className="text-white font-bold text-sm">{stage.count}</span>
              </div>
            </div>
            <div className="w-16 text-sm text-muted-foreground text-right">
              {stage.percentage.toFixed(1)}%
            </div>
          </div>
          {index < stages.length - 1 && (
            <div className="flex items-center gap-4 py-1 text-xs text-muted-foreground">
              <div className="w-32" />
              <ArrowRight className="h-3 w-3 ml-2" />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// Tab content components
function OverviewTab({
  summary,
  paperAnalytics,
  teamOverview,
}: {
  summary: ReturnType<typeof useDashboardSummary>['data']
  paperAnalytics: ReturnType<typeof usePaperAnalytics>['data']
  teamOverview: ReturnType<typeof useTeamOverview>['data']
}) {
  const { t } = useTranslation()
  const sourceColors: Record<string, string> = {
    openalex: '#3b82f6',
    pubmed: '#10b981',
    arxiv: '#f59e0b',
    doi: '#8b5cf6',
    pdf: '#ec4899',
    manual: '#6b7280',
    crossref: '#14b8a6',
    semantic_scholar: '#f97316',
  }

  const sourceData = paperAnalytics?.import_trends.by_source.map((s) => ({
    name: s.source,
    value: s.count,
    color: sourceColors[s.source] || '#6b7280',
  })) || []

  const scoreDistributionData = paperAnalytics?.scoring_stats.score_distribution.map((b) => ({
    name: `${b.range_start}-${b.range_end}`,
    value: b.count,
  })) || []

  const trendData = summary?.import_trend.map((t) => ({
    date: new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    count: t.count,
  })) || []

  return (
    <div className="space-y-8">
      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('analytics.totalPapers')}
            </CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_papers ?? 0}</div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              {(summary?.papers_this_week ?? 0) > 0 ? (
                <>
                  <ArrowUp className="h-3 w-3 text-green-500 mr-1" />
                  <span className="text-green-600">+{summary?.papers_this_week}</span>
                  <span className="ml-1">{t('analytics.thisWeek')}</span>
                </>
              ) : (
                <span>{t('analytics.noNewPapersThisWeek')}</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('analytics.scoredPapers')}
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.scored_papers ?? 0}</div>
            <div className="text-xs text-muted-foreground mt-1">
              Avg score: {summary?.average_score?.toFixed(1) ?? 'N/A'}/10
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('analytics.projects')}
            </CardTitle>
            <FolderKanban className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_projects ?? 0}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {summary?.active_projects ?? 0} active
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('analytics.teamMembers')}
            </CardTitle>
            <Users className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_users ?? 0}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {teamOverview?.active_users_last_7_days ?? 0} active this week
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {t('analytics.importTrend')}
            </CardTitle>
            <CardDescription>{t('analytics.importTrendDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <SimpleLineChart data={trendData} height={180} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              {t('analytics.papersBySource')}
            </CardTitle>
            <CardDescription>{t('analytics.papersBySourceDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <SimpleDonutChart data={sourceData} size={140} />
          </CardContent>
        </Card>
      </div>

      {/* More Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              {t('analytics.scoreDistribution')}
            </CardTitle>
            <CardDescription>{t('analytics.scoreDistributionDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            {scoreDistributionData.length > 0 ? (
              <SimpleBarChart data={scoreDistributionData} height={180} />
            ) : (
              <div className="flex items-center justify-center h-[180px] text-muted-foreground">
                {t('analytics.noScoredPapersYet')}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              {t('analytics.avgScoresByDimension')}
            </CardTitle>
            <CardDescription>{t('analytics.avgScoresByDimensionDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            {paperAnalytics?.scoring_stats.average_overall_score ? (
              <SimpleBarChart
                data={[
                  { name: 'Novelty', value: Math.round((paperAnalytics.scoring_stats.average_novelty ?? 0) * 10) / 10 },
                  { name: 'IP', value: Math.round((paperAnalytics.scoring_stats.average_ip_potential ?? 0) * 10) / 10 },
                  { name: 'Market', value: Math.round((paperAnalytics.scoring_stats.average_marketability ?? 0) * 10) / 10 },
                  { name: 'Feasible', value: Math.round((paperAnalytics.scoring_stats.average_feasibility ?? 0) * 10) / 10 },
                  { name: 'Comm.', value: Math.round((paperAnalytics.scoring_stats.average_commercialization ?? 0) * 10) / 10 },
                ]}
                height={180}
              />
            ) : (
              <div className="flex items-center justify-center h-[180px] text-muted-foreground">
                {t('analytics.noScoredPapersYet')}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Papers */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{t('analytics.topScoredPapers')}</CardTitle>
            <CardDescription>{t('analytics.topScoredPapersDescription')}</CardDescription>
          </div>
          <Link to="/papers">
            <Button variant="ghost" size="sm">
              {t('analytics.viewAll')}
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {paperAnalytics?.top_papers.length ? (
            <div className="space-y-3">
              {paperAnalytics.top_papers.slice(0, 5).map((paper, index) => (
                <Link
                  key={paper.id}
                  to={`/papers/${paper.id}`}
                  className="flex items-center gap-4 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted font-medium">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium truncate">{paper.title}</h4>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Badge variant="outline">{paper.source}</Badge>
                      {paper.doi && <span className="truncate">{paper.doi}</span>}
                    </div>
                  </div>
                  {paper.overall_score !== null && (
                    <Badge variant="default" className="shrink-0">
                      {paper.overall_score.toFixed(1)}/10
                    </Badge>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>{t('analytics.noPapersYet')}</p>
              <p className="text-sm">{t('analytics.importAndScorePapers')}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Embedding Coverage */}
      <Card>
        <CardHeader>
          <CardTitle>{t('analytics.embeddingCoverage')}</CardTitle>
          <CardDescription>{t('analytics.embeddingCoverageDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{
                    width: `${paperAnalytics?.embedding_coverage_percent ?? 0}%`,
                  }}
                />
              </div>
            </div>
            <div className="text-lg font-medium">
              {paperAnalytics?.embedding_coverage_percent?.toFixed(1) ?? 0}%
            </div>
          </div>
          <div className="flex justify-between text-sm text-muted-foreground mt-2">
            <span>{paperAnalytics?.papers_with_embeddings ?? 0} with embeddings</span>
            <span>{paperAnalytics?.papers_without_embeddings ?? 0} without embeddings</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function FunnelTab() {
  const { t } = useTranslation()
  const { data: funnel, isLoading } = useFunnelAnalytics()

  if (isLoading) {
    return <ContentSkeleton variant="dashboard" />
  }

  return (
    <div className="space-y-6">
      {/* Funnel Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            {t('analytics.innovationFunnel')}
          </CardTitle>
          <CardDescription>
            {t('analytics.innovationFunnelDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {funnel?.stages.length ? (
            <FunnelChart stages={funnel.stages} />
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Filter className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>{t('analytics.noFunnelData')}</p>
              <p className="text-sm">{t('analytics.noFunnelDataDescription')}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Conversion Rates */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            {t('analytics.conversionRates')}
          </CardTitle>
          <CardDescription>{t('analytics.conversionRatesDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {funnel?.conversion_rates ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
              <div className="text-center p-4 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-blue-600">
                  {funnel.conversion_rates.imported_to_scored?.toFixed(1) ?? 0}%
                </div>
                <div className="text-xs text-muted-foreground mt-1">Import → Scored</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-purple-600">
                  {funnel.conversion_rates.scored_to_pipeline?.toFixed(1) ?? 0}%
                </div>
                <div className="text-xs text-muted-foreground mt-1">Scored → Pipeline</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-pink-600">
                  {funnel.conversion_rates.pipeline_to_contacted?.toFixed(1) ?? 0}%
                </div>
                <div className="text-xs text-muted-foreground mt-1">Pipeline → Contacted</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted">
                <div className="text-2xl font-bold text-orange-600">
                  {funnel.conversion_rates.contacted_to_transferred?.toFixed(1) ?? 0}%
                </div>
                <div className="text-xs text-muted-foreground mt-1">Contacted → Transferred</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-green-100 dark:bg-green-900/20">
                <div className="text-2xl font-bold text-green-600">
                  {funnel.conversion_rates.overall?.toFixed(1) ?? 0}%
                </div>
                <div className="text-xs text-muted-foreground mt-1">Overall Conversion</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No conversion data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <Card>
        <CardHeader>
          <CardTitle>{t('analytics.funnelSummary')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center p-4 rounded-lg border">
              <div className="text-3xl font-bold">{funnel?.total_papers ?? 0}</div>
              <div className="text-sm text-muted-foreground mt-1">Total Papers</div>
            </div>
            <div className="text-center p-4 rounded-lg border">
              <div className="text-3xl font-bold">
                {funnel?.stages.find((s) => s.stage === 'transferred')?.count ?? 0}
              </div>
              <div className="text-sm text-muted-foreground mt-1">Successfully Transferred</div>
            </div>
            <div className="text-center p-4 rounded-lg border">
              <div className="text-3xl font-bold">
                {funnel?.stages.find((s) => s.stage === 'in_pipeline')?.count ?? 0}
              </div>
              <div className="text-sm text-muted-foreground mt-1">In Active Pipeline</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function BenchmarksTab() {
  const { t } = useTranslation()
  const { data: benchmarks, isLoading } = useBenchmarks()

  if (isLoading) {
    return <ContentSkeleton variant="dashboard" />
  }

  return (
    <div className="space-y-6">
      {/* Percentile Rank */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            {t('analytics.performanceRanking')}
          </CardTitle>
          <CardDescription>
            {t('analytics.performanceRankingDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-5xl font-bold text-primary">
                {benchmarks?.org_percentile?.toFixed(0) ?? 50}
                <span className="text-2xl">th</span>
              </div>
              <div className="text-sm text-muted-foreground mt-1">Percentile</div>
            </div>
            <div className="flex-1">
              <div className="h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-orange-500 via-yellow-500 to-green-500"
                  style={{ width: `${benchmarks?.org_percentile ?? 50}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>0th</span>
                <span>50th</span>
                <span>100th</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            Based on comparison with {benchmarks?.benchmark_data_points ?? 0} organizations
          </p>
        </CardContent>
      </Card>

      {/* Metrics Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            {t('analytics.metricComparison')}
          </CardTitle>
          <CardDescription>
            {t('analytics.metricComparisonDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {benchmarks?.metrics.length ? (
            <ComparisonBarChart data={benchmarks.metrics} />
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No benchmark data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {benchmarks?.metrics.map((metric) => {
          const isAboveBenchmark = metric.higher_is_better
            ? metric.org_value >= metric.benchmark_value
            : metric.org_value <= metric.benchmark_value
          const diff = metric.org_value - metric.benchmark_value
          const percentDiff = metric.benchmark_value > 0
            ? ((diff / metric.benchmark_value) * 100).toFixed(0)
            : '0'

          return (
            <Card key={metric.metric}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {metric.org_value.toFixed(1)}{metric.unit}
                </div>
                <div className={cn(
                  'text-sm mt-1 flex items-center gap-1',
                  isAboveBenchmark ? 'text-green-600' : 'text-orange-600'
                )}>
                  {isAboveBenchmark ? (
                    <ArrowUp className="h-3 w-3" />
                  ) : (
                    <ArrowUp className="h-3 w-3 rotate-180" />
                  )}
                  {Math.abs(Number(percentDiff))}% vs benchmark ({metric.benchmark_value.toFixed(1)}{metric.unit})
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

function ReportsTab() {
  const { t } = useTranslation()
  const { data: reports, isLoading } = useScheduledReports()
  const createReport = useCreateScheduledReport()
  const deleteReport = useDeleteScheduledReport()
  const runReport = useRunScheduledReport()
  const updateReport = useUpdateScheduledReport()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newReport, setNewReport] = useState({
    name: '',
    report_type: 'dashboard_summary' as ReportType,
    schedule: 'weekly' as ReportSchedule,
    recipients: '',
    format: 'pdf' as const,
  })

  const handleCreate = async () => {
    if (!newReport.name || !newReport.recipients) return
    try {
      await createReport.mutateAsync({
        name: newReport.name,
        report_type: newReport.report_type,
        schedule: newReport.schedule,
        recipients: newReport.recipients.split(',').map((e) => e.trim()),
        format: newReport.format,
      })
      setShowCreateForm(false)
      setNewReport({
        name: '',
        report_type: 'dashboard_summary',
        schedule: 'weekly',
        recipients: '',
        format: 'pdf',
      })
    } catch (error) {
      console.error('Failed to create report:', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this scheduled report?')) {
      try {
        await deleteReport.mutateAsync(id)
      } catch (error) {
        console.error('Failed to delete report:', error)
      }
    }
  }

  const handleRun = async (id: string) => {
    try {
      await runReport.mutateAsync(id)
    } catch (error) {
      console.error('Failed to run report:', error)
    }
  }

  const handleToggleActive = async (report: ScheduledReport) => {
    try {
      await updateReport.mutateAsync({
        reportId: report.id,
        data: { is_active: !report.is_active },
      })
    } catch (error) {
      console.error('Failed to toggle report:', error)
    }
  }

  if (isLoading) {
    return <ContentSkeleton variant="list" />
  }

  const reportTypeLabels: Record<ReportType, string> = {
    dashboard_summary: 'Dashboard Summary',
    paper_trends: 'Paper Trends',
    team_activity: 'Team Activity',
  }

  const scheduleLabels: Record<ReportSchedule, string> = {
    daily: 'Daily',
    weekly: 'Weekly',
    monthly: 'Monthly',
  }

  return (
    <div className="space-y-6">
      {/* Create Form */}
      {showCreateForm ? (
        <Card>
          <CardHeader>
            <CardTitle>{t('analytics.createScheduledReport')}</CardTitle>
            <CardDescription>{t('analytics.createScheduledReportDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="report-name">{t('analytics.reportName')}</Label>
                <Input
                  id="report-name"
                  placeholder="Weekly Dashboard Report"
                  value={newReport.name}
                  onChange={(e) => setNewReport({ ...newReport, name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="report-recipients">{t('analytics.recipients')}</Label>
                <Input
                  id="report-recipients"
                  placeholder="team@example.com, manager@example.com"
                  value={newReport.recipients}
                  onChange={(e) => setNewReport({ ...newReport, recipients: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="report-type">{t('analytics.reportType')}</Label>
                <select
                  id="report-type"
                  className="w-full rounded-md border px-3 py-2"
                  value={newReport.report_type}
                  onChange={(e) => setNewReport({ ...newReport, report_type: e.target.value as ReportType })}
                >
                  <option value="dashboard_summary">Dashboard Summary</option>
                  <option value="paper_trends">Paper Trends</option>
                  <option value="team_activity">Team Activity</option>
                </select>
              </div>
              <div>
                <Label htmlFor="report-schedule">{t('analytics.schedule')}</Label>
                <select
                  id="report-schedule"
                  className="w-full rounded-md border px-3 py-2"
                  value={newReport.schedule}
                  onChange={(e) => setNewReport({ ...newReport, schedule: e.target.value as ReportSchedule })}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleCreate} isLoading={createReport.isPending}>
                {t('analytics.createReport')}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="flex justify-end">
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {t('analytics.newScheduledReport')}
          </Button>
        </div>
      )}

      {/* Reports List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5" />
            {t('analytics.scheduledReports')}
          </CardTitle>
          <CardDescription>
            {t('analytics.scheduledReportsDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {reports?.items.length ? (
            <div className="space-y-4">
              {reports.items.map((report) => (
                <div
                  key={report.id}
                  className={cn(
                    'flex items-center justify-between p-4 rounded-lg border',
                    !report.is_active && 'opacity-60'
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{report.name}</h4>
                      <Badge variant={report.is_active ? 'default' : 'secondary'}>
                        {report.is_active ? 'Active' : 'Paused'}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <FileText className="h-3 w-3" />
                        {reportTypeLabels[report.report_type]}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {scheduleLabels[report.schedule]}
                      </span>
                      <span className="flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        {report.recipients.length} recipient{report.recipients.length !== 1 ? 's' : ''}
                      </span>
                      {report.last_sent_at && (
                        <span className="text-xs">
                          Last sent: {new Date(report.last_sent_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleActive(report)}
                    >
                      {report.is_active ? t('analytics.pause') : t('analytics.resume')}
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleRun(report.id)}
                      title="Run now"
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => handleDelete(report.id)}
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<CalendarClock className="h-12 w-12" />}
              title={t('analytics.noScheduledReports')}
              description={t('analytics.noScheduledReportsDescription')}
              action={{
                label: t('analytics.createReport'),
                onClick: () => setShowCreateForm(true),
              }}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function AnalyticsPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('overview')
  const [isExporting, setIsExporting] = useState(false)

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary()
  const { data: paperAnalytics, isLoading: analyticsLoading } = usePaperAnalytics(90)
  const { data: teamOverview, isLoading: teamLoading } = useTeamOverview()

  const handleExport = async (format: 'csv' | 'bibtex' | 'pdf') => {
    setIsExporting(true)
    try {
      const timestamp = new Date().toISOString().slice(0, 10)
      let blob: Blob
      let filename: string

      switch (format) {
        case 'csv':
          blob = await exportApi.exportCsv({ include_scores: true, include_authors: true })
          filename = `papers_export_${timestamp}.csv`
          break
        case 'bibtex':
          blob = await exportApi.exportBibtex({ include_abstract: true })
          filename = `papers_export_${timestamp}.bib`
          break
        case 'pdf':
          blob = await exportApi.exportPdf({ include_scores: true, include_abstract: true })
          filename = `papers_report_${timestamp}.txt`
          break
      }

      exportApi.downloadFile(blob, filename)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const isLoading = summaryLoading || analyticsLoading || teamLoading

  if (isLoading && activeTab === 'overview') {
    return <ContentSkeleton variant="dashboard" />
  }

  const tabs: { value: AnalyticsTab; label: string; icon: typeof BarChart3 }[] = [
    { value: 'overview', label: t('analytics.overview'), icon: BarChart3 },
    { value: 'funnel', label: t('analytics.innovationFunnel'), icon: Filter },
    { value: 'benchmarks', label: t('analytics.benchmarks'), icon: Award },
    { value: 'reports', label: t('analytics.scheduledReports'), icon: CalendarClock },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('analytics.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('analytics.subtitle')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleExport('csv')}
            disabled={isExporting}
          >
            <Download className="h-4 w-4 mr-2" />
            {t('analytics.exportCsv')}
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('bibtex')}
            disabled={isExporting}
          >
            <Download className="h-4 w-4 mr-2" />
            {t('analytics.exportBibtex')}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4 -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === tab.value
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/50'
              )}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <OverviewTab
          summary={summary}
          paperAnalytics={paperAnalytics}
          teamOverview={teamOverview}
        />
      )}
      {activeTab === 'funnel' && <FunnelTab />}
      {activeTab === 'benchmarks' && <BenchmarksTab />}
      {activeTab === 'reports' && <ReportsTab />}
    </div>
  )
}
