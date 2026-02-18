import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { formatDistanceToNow, format } from 'date-fns'
import {
  ArrowLeft,
  BarChart3,
  ExternalLink,
  FileText,
  Lightbulb,
  RefreshCw,
  Sparkles,
  Trash2,
  TrendingUp,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { ExternalLink as SafeExternalLink } from '@/components/ui/ExternalLink'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Skeleton, SkeletonStats } from '@/components/ui/Skeleton'
import { InnovationRadar } from '@/components/InnovationRadar'
import { useToast } from '@/components/ui/Toast'
import { useTrendDashboard, useAnalyzeTrend, useDeleteTrendTopic } from '@/hooks/useTrends'
import type { TrendTimelinePoint, TrendPaper, PatentResult, KeywordCount, TrendSnapshot } from '@/types'

// ---------------------------------------------------------------------------
// Inline SVG line chart
// ---------------------------------------------------------------------------

function SimpleLineChart({
  data,
  height = 180,
}: {
  data: TrendTimelinePoint[]
  height?: number
}) {
  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground"
        style={{ height }}
      >
        No timeline data available
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

  const pathD = points
    .map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
    .join(' ')

  return (
    <div className="relative" style={{ height }}>
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full"
        preserveAspectRatio="none"
        role="img"
        aria-label="Publication timeline chart"
      >
        {/* Grid lines */}
        <line x1="0" y1="25" x2="100" y2="25" stroke="currentColor" strokeOpacity="0.1" />
        <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" strokeOpacity="0.1" />
        <line x1="0" y1="75" x2="100" y2="75" stroke="currentColor" strokeOpacity="0.1" />

        {/* Area fill */}
        <path
          d={`${pathD} L 100 100 L 0 100 Z`}
          fill="hsl(var(--primary))"
          fillOpacity="0.1"
        />

        {/* Line */}
        <path
          d={pathD}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
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

// ---------------------------------------------------------------------------
// Metric stat card
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string | number
  icon: typeof FileText
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Paper list item
// ---------------------------------------------------------------------------

function PaperItem({ paper }: { paper: TrendPaper }) {
  const relevancePercent = Math.round(paper.relevance_score * 100)

  return (
    <Link
      to={`/papers/${paper.id}`}
      className="flex items-start gap-4 p-4 rounded-lg border hover:bg-muted/50 transition-colors"
    >
      <div className="flex-1 min-w-0">
        <h4 className="font-medium leading-snug">{paper.title}</h4>
        {paper.abstract && (
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{paper.abstract}</p>
        )}
        <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
          {paper.journal && <span>{paper.journal}</span>}
          {paper.journal && paper.publication_date && <span aria-hidden="true">&middot;</span>}
          {paper.publication_date && (
            <span>{format(new Date(paper.publication_date), 'MMM d, yyyy')}</span>
          )}
        </div>
      </div>
      <div className="flex flex-col items-end gap-2 shrink-0">
        <Badge variant="secondary">{relevancePercent}% match</Badge>
        {paper.overall_score !== null && (
          <Badge variant="default">{paper.overall_score.toFixed(1)}/10</Badge>
        )}
      </div>
    </Link>
  )
}

// ---------------------------------------------------------------------------
// Patent list item
// ---------------------------------------------------------------------------

function PatentItem({ patent }: { patent: PatentResult }) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-lg border">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h4 className="font-medium leading-snug">{patent.title}</h4>
          <Badge variant="outline" className="shrink-0">
            {patent.patent_number}
          </Badge>
        </div>
        {patent.abstract && (
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{patent.abstract}</p>
        )}
        <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
          {patent.applicant && <span>{patent.applicant}</span>}
          {patent.applicant && patent.publication_date && (
            <span aria-hidden="true">&middot;</span>
          )}
          {patent.publication_date && (
            <span>{format(new Date(patent.publication_date), 'MMM d, yyyy')}</span>
          )}
        </div>
      </div>
      <SafeExternalLink
        href={patent.espacenet_url}
        className="shrink-0"
        aria-label={`View patent ${patent.patent_number} on Espacenet`}
      >
        <Button variant="outline" size="sm">
          <ExternalLink className="h-4 w-4 mr-1" />
          Espacenet
        </Button>
      </SafeExternalLink>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Dashboard sections (rendered when snapshot exists)
// ---------------------------------------------------------------------------

function DashboardContent({
  snapshot,
  topPapers,
}: {
  snapshot: TrendSnapshot
  topPapers: TrendPaper[]
}) {
  const { t } = useTranslation()

  const radarScores = {
    novelty: snapshot.avg_novelty ?? 0,
    ip_potential: snapshot.avg_ip_potential ?? 0,
    marketability: snapshot.avg_marketability ?? 0,
    feasibility: snapshot.avg_feasibility ?? 0,
    commercialization: snapshot.avg_commercialization ?? 0,
    team_readiness: snapshot.avg_team_readiness ?? 0,
  }

  return (
    <div className="space-y-8">
      {/* Metrics row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label={t('trends.matchedPapers', 'Matched Papers')}
          value={snapshot.matched_papers_count}
          icon={FileText}
        />
        <StatCard
          label={t('trends.relatedPatents', 'Related Patents')}
          value={snapshot.patent_count}
          icon={BarChart3}
        />
        <StatCard
          label={t('trends.avgScore', 'Avg Score')}
          value={snapshot.avg_overall_score !== null ? snapshot.avg_overall_score.toFixed(1) : 'N/A'}
          icon={TrendingUp}
        />
        <StatCard
          label={t('trends.lastAnalyzed', 'Last Analyzed')}
          value={formatDistanceToNow(new Date(snapshot.created_at), { addSuffix: true })}
          icon={RefreshCw}
        />
      </div>

      {/* Radar + AI Summary */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              {t('trends.scoreRadar', 'Score Radar')}
            </CardTitle>
            <CardDescription>
              {t('trends.scoreRadarDescription', 'Average scores across all matched papers')}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <InnovationRadar scores={radarScores} size={260} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              {t('trends.aiSummary', 'AI Summary')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {snapshot.summary ? (
              <p className="text-sm leading-relaxed text-muted-foreground">{snapshot.summary}</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">
                {t('trends.noSummaryAvailable', 'No summary available')}
              </p>
            )}
            {snapshot.key_insights.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">
                  {t('trends.keyInsights', 'Key Insights')}
                </h4>
                <ul className="space-y-2">
                  {snapshot.key_insights.map((insight, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <Lightbulb className="h-4 w-4 mt-0.5 shrink-0 text-amber-500" />
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Timeline + Keywords */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              {t('trends.publicationTimeline', 'Publication Timeline')}
            </CardTitle>
            <CardDescription>
              {t('trends.publicationTimelineDescription', 'Papers per month matching this topic')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SimpleLineChart data={snapshot.timeline_data} height={180} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              {t('trends.topKeywords', 'Top Keywords')}
            </CardTitle>
            <CardDescription>
              {t('trends.topKeywordsDescription', 'Most frequent keywords in matched papers')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {snapshot.top_keywords.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {snapshot.top_keywords.map((kw: KeywordCount) => (
                  <Badge key={kw.keyword} variant="secondary">
                    {kw.keyword} ({kw.count})
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t('trends.noKeywords', 'No keywords extracted yet')}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Matched Papers */}
      {topPapers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {t('trends.topMatchedPapers', 'Top Matched Papers')}
            </CardTitle>
            <CardDescription>
              {t('trends.topMatchedPapersDescription', 'Highest relevance papers for this trend topic')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topPapers.map((paper) => (
                <PaperItem key={paper.id} paper={paper} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Related Patents */}
      {snapshot.patent_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              {t('trends.relatedPatents', 'Related Patents')}
            </CardTitle>
            <CardDescription>
              {t('trends.relatedPatentsDescription', 'Patents related to this trend topic')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {snapshot.patent_results.map((patent) => (
                <PatentItem key={patent.patent_number} patent={patent} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function TrendDetailSkeleton() {
  return (
    <div className="space-y-8">
      {/* Header skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>
      {/* Stats skeleton */}
      <SkeletonStats />
      {/* Content skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-[260px] w-full" />
        </div>
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export function TrendDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const toast = useToast()

  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data: dashboard, isLoading, error } = useTrendDashboard(id ?? '')
  const analyzeMutation = useAnalyzeTrend()
  const deleteMutation = useDeleteTrendTopic()

  function handleAnalyze() {
    if (!id) return
    analyzeMutation.mutate(
      { id },
      {
        onSuccess: () => {
          toast.success(
            t('trends.analysisComplete', 'Analysis complete'),
            t('trends.analysisCompleteDescription', 'The trend topic has been analyzed successfully.')
          )
        },
        onError: (err) => {
          toast.error(
            t('trends.analysisFailed', 'Analysis failed'),
            err instanceof Error ? err.message : t('trends.analysisFailedDescription', 'An error occurred during analysis.')
          )
        },
      }
    )
  }

  function handleDelete() {
    if (!id) return
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast.success(
          t('trends.topicDeleted', 'Topic deleted'),
          t('trends.topicDeletedDescription', 'The trend topic has been removed.')
        )
        navigate('/trends')
      },
      onError: (err) => {
        toast.error(
          t('trends.deleteFailed', 'Delete failed'),
          err instanceof Error ? err.message : t('trends.deleteFailedDescription', 'Could not delete the trend topic.')
        )
      },
    })
  }

  // ---- Loading state ----
  if (isLoading) {
    return <TrendDetailSkeleton />
  }

  // ---- Error state ----
  if (error || !dashboard) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/trends')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t('trends.backToTrends', 'Back to Trends')}
        </Button>
        <EmptyState
          icon={<FileText className="h-12 w-12" />}
          title={t('trends.notFound', 'Trend topic not found')}
          description={
            error instanceof Error
              ? error.message
              : t('trends.notFoundDescription', 'The trend topic you are looking for does not exist or has been removed.')
          }
          action={{
            label: t('trends.backToTrends', 'Back to Trends'),
            onClick: () => navigate('/trends'),
          }}
        />
      </div>
    )
  }

  const { topic, snapshot, top_papers } = dashboard
  const topicColor = topic.color ?? '#6b7280'

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/trends')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t('trends.backToTrends', 'Back to Trends')}
        </Button>

        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div
                className="h-4 w-4 rounded-full shrink-0"
                style={{ backgroundColor: topicColor }}
                aria-hidden="true"
              />
              <h1 className="text-3xl font-bold">{topic.name}</h1>
            </div>
            {topic.description && (
              <p className="text-muted-foreground max-w-2xl">{topic.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending}
              isLoading={analyzeMutation.isPending}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {t('trends.analyze', 'Analyze')}
            </Button>
            <Button
              variant="destructive"
              onClick={() => setShowDeleteDialog(true)}
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {t('trends.delete', 'Delete')}
            </Button>
          </div>
        </div>
      </div>

      {/* Dashboard content or empty state */}
      {snapshot ? (
        <DashboardContent snapshot={snapshot} topPapers={top_papers} />
      ) : (
        <Card>
          <CardContent className="py-12">
            <EmptyState
              icon={<Sparkles className="h-12 w-12" />}
              title={t('trends.noAnalysisYet', 'No analysis yet')}
              description={t(
                'trends.noAnalysisYetDescription',
                'Run an analysis to discover matching papers, patents, and insights for this trend topic.'
              )}
              action={{
                label: t('trends.runAnalysis', 'Run Analysis'),
                onClick: handleAnalyze,
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title={t('trends.deleteTitle', 'Delete trend topic')}
        description={t(
          'trends.deleteDescription',
          `Are you sure you want to delete "${topic.name}"? This action cannot be undone.`
        )}
        confirmLabel={t('trends.deleteConfirm', 'Delete')}
        cancelLabel={t('common.cancel', 'Cancel')}
        onConfirm={handleDelete}
        variant="destructive"
        isLoading={deleteMutation.isPending}
        icon={<Trash2 className="h-6 w-6 text-destructive" />}
      />
    </div>
  )
}
