import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/contexts/AuthContext'
import { usePapers, useProjects, useEmbeddingStats, useConversations } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  FileText,
  UsersRound,
  Search,
  TrendingUp,
  Loader2,
  ArrowRight,
  Telescope,
  ClipboardCheck,
  ArrowRightLeft,
} from 'lucide-react'
import { formatDate, truncate } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface WorkflowLaneProps {
  icon: LucideIcon
  iconColor: string
  iconBg: string
  title: string
  description: string
  stats: { label: string; value: string | number }[]
  recentItems?: { id: string; label: string; href: string; badge?: string }[]
  ctaLabel: string
  ctaPath: string
  isLoading?: boolean
}

function WorkflowLane({
  icon: Icon,
  iconColor,
  iconBg,
  title,
  description,
  stats,
  recentItems,
  ctaLabel,
  ctaPath,
  isLoading,
}: WorkflowLaneProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className={`rounded-lg p-2 ${iconBg}`}>
            <Icon className={`h-5 w-5 ${iconColor}`} />
          </div>
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <CardDescription className="text-xs mt-0.5">{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4">
        {/* Stats grid */}
        <div className={`grid gap-2 ${stats.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-md bg-muted/50 px-3 py-2">
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-lg font-semibold">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : stat.value}
              </p>
            </div>
          ))}
        </div>

        {/* Recent items */}
        {recentItems && recentItems.length > 0 && (
          <div className="space-y-1.5">
            {recentItems.map((item) => (
              <Link
                key={item.id}
                to={item.href}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm hover:bg-muted/50 transition-colors"
              >
                <span className="truncate">{item.label}</span>
                {item.badge && (
                  <Badge variant="outline" className="ml-2 shrink-0 text-xs">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            ))}
          </div>
        )}

        {/* CTA */}
        <div className="mt-auto pt-2">
          <Link to={ctaPath} className="block">
            <Button variant="outline" className="w-full">
              {ctaLabel}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const { data: papersData, isLoading: papersLoading } = usePapers({ page: 1, page_size: 3 })
  const { data: projects, isLoading: projectsLoading } = useProjects()
  const { data: embeddingStats } = useEmbeddingStats()
  const { data: conversationsData } = useConversations({ page: 1, page_size: 1 })

  const topStats = [
    {
      title: t('dashboard.totalPapers'),
      value: papersData?.total ?? 0,
      icon: FileText,
      color: 'text-blue-600',
    },
    {
      title: t('dashboard.activeProjects'),
      value: projects?.total ?? 0,
      icon: UsersRound,
      color: 'text-green-600',
    },
    {
      title: t('dashboard.embeddings'),
      value: embeddingStats ? `${embeddingStats.embedding_coverage.toFixed(0)}%` : '\u2014',
      icon: Search,
      color: 'text-purple-600',
    },
  ]

  const recentPapers =
    papersData?.items?.slice(0, 3).map((p) => ({
      id: p.id,
      label: truncate(p.title, 50),
      href: `/papers/${p.id}`,
      badge: p.source,
    })) ?? []

  const recentProjects =
    projects?.items?.slice(0, 3).map((p) => ({
      id: p.id,
      label: p.name,
      href: `/projects/${p.id}`,
      badge: p.is_active ? t('dashboard.active') : t('dashboard.inactive'),
    })) ?? []

  const scoredCount = papersData?.items?.filter((p) => p.has_embedding).length ?? 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">
          {t('dashboard.welcomeBack', {
            name: user?.full_name?.split(' ')[0] ?? t('dashboard.defaultName'),
          })}
        </h1>
        <p className="text-muted-foreground mt-1">{t('dashboard.subtitle')}</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        {topStats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Workflow Lanes */}
      <div className="grid gap-6 md:grid-cols-3">
        <WorkflowLane
          icon={Telescope}
          iconColor="text-blue-600"
          iconBg="bg-blue-100 dark:bg-blue-950"
          title={t('dashboard.workflow.discoverTitle', 'Discover')}
          description={t('dashboard.workflow.discoverDescription', 'Find and import papers')}
          stats={[
            {
              label: t('dashboard.workflow.papersInLibrary', 'Papers in Library'),
              value: papersData?.total ?? 0,
            },
            {
              label: t('dashboard.workflow.embeddingCoverage', 'Embedding Coverage'),
              value: embeddingStats
                ? `${embeddingStats.embedding_coverage.toFixed(0)}%`
                : '\u2014',
            },
          ]}
          recentItems={recentPapers}
          ctaLabel={t('dashboard.workflow.discoverCta', 'Search Papers')}
          ctaPath="/search"
          isLoading={papersLoading}
        />

        <WorkflowLane
          icon={ClipboardCheck}
          iconColor="text-green-600"
          iconBg="bg-green-100 dark:bg-green-950"
          title={t('dashboard.workflow.evaluateTitle', 'Evaluate')}
          description={t('dashboard.workflow.evaluateDescription', 'Score and organize papers')}
          stats={[
            {
              label: t('dashboard.workflow.activeProjects', 'Active Projects'),
              value: projects?.total ?? 0,
            },
            {
              label: t('dashboard.workflow.scoredPapers', 'Scored Papers'),
              value: scoredCount,
            },
          ]}
          recentItems={recentProjects}
          ctaLabel={t('dashboard.workflow.evaluateCta', 'View Papers')}
          ctaPath="/papers"
          isLoading={projectsLoading}
        />

        <WorkflowLane
          icon={ArrowRightLeft}
          iconColor="text-purple-600"
          iconBg="bg-purple-100 dark:bg-purple-950"
          title={t('dashboard.workflow.transferTitle', 'Transfer')}
          description={t(
            'dashboard.workflow.transferDescription',
            'Start transfer conversations'
          )}
          stats={[
            {
              label: t('dashboard.workflow.conversations', 'Conversations'),
              value: conversationsData?.total ?? 0,
            },
          ]}
          ctaLabel={t('dashboard.workflow.transferCta', 'Start Transfer')}
          ctaPath="/transfer"
        />
      </div>

      {/* Recent Papers - full width detail view */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{t('dashboard.recentPapers')}</CardTitle>
            <CardDescription>{t('dashboard.recentPapersDescription')}</CardDescription>
          </div>
          <Link to="/papers">
            <Button variant="ghost" size="sm">
              {t('dashboard.viewAll')}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {papersLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !papersData?.items?.length ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>{t('dashboard.noPapers')}</p>
              <p className="text-sm">{t('dashboard.noPapersDescription')}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {papersData?.items.map((paper) => (
                <Link
                  key={paper.id}
                  to={`/papers/${paper.id}`}
                  className="block rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium line-clamp-1">{paper.title}</h3>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {truncate(paper.abstract ?? t('dashboard.noAbstract'), 150)}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline">{paper.source}</Badge>
                        {paper.publication_date && (
                          <span className="text-xs text-muted-foreground">
                            {formatDate(paper.publication_date)}
                          </span>
                        )}
                      </div>
                    </div>
                    {paper.has_embedding && (
                      <Badge variant="secondary" className="shrink-0">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        {t('dashboard.scored')}
                      </Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
