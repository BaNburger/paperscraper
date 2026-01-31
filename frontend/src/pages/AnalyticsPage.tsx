import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDashboardSummary, usePaperAnalytics, useTeamOverview } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  FileText,
  TrendingUp,
  Users,
  FolderKanban,
  Download,
  BarChart3,
  PieChart,
  Activity,
  Loader2,
  ArrowUp,
} from 'lucide-react'
import { exportApi } from '@/lib/api'

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

export function AnalyticsPage() {
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Prepare chart data
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Insights into your research pipeline
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleExport('csv')}
            disabled={isExporting}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('bibtex')}
            disabled={isExporting}
          >
            <Download className="h-4 w-4 mr-2" />
            Export BibTeX
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Papers
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
                  <span className="ml-1">this week</span>
                </>
              ) : (
                <span>No new papers this week</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Scored Papers
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
              Projects
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
              Team Members
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
        {/* Import Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Import Trend (30 Days)
            </CardTitle>
            <CardDescription>Papers added over time</CardDescription>
          </CardHeader>
          <CardContent>
            <SimpleLineChart data={trendData} height={180} />
          </CardContent>
        </Card>

        {/* Source Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Papers by Source
            </CardTitle>
            <CardDescription>Where your papers come from</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <SimpleDonutChart data={sourceData} size={140} />
          </CardContent>
        </Card>
      </div>

      {/* More Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Score Distribution
            </CardTitle>
            <CardDescription>Distribution of overall scores</CardDescription>
          </CardHeader>
          <CardContent>
            {scoreDistributionData.length > 0 ? (
              <SimpleBarChart data={scoreDistributionData} height={180} />
            ) : (
              <div className="flex items-center justify-center h-[180px] text-muted-foreground">
                No scored papers yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Average Scores by Dimension */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Average Scores by Dimension
            </CardTitle>
            <CardDescription>How papers score across dimensions</CardDescription>
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
                No scored papers yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Papers */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Top Scored Papers</CardTitle>
            <CardDescription>Highest scoring papers in your library</CardDescription>
          </div>
          <Link to="/papers">
            <Button variant="ghost" size="sm">
              View all
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
              <p>No papers yet</p>
              <p className="text-sm">Import and score papers to see them here</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Embedding Coverage */}
      <Card>
        <CardHeader>
          <CardTitle>Embedding Coverage</CardTitle>
          <CardDescription>Papers with vector embeddings for semantic search</CardDescription>
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
