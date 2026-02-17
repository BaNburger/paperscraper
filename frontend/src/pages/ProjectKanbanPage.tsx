import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  useResearchGroup,
  useResearchGroupClusters,
  useSyncResearchGroup,
  useUpdateClusterLabel,
} from '@/hooks'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useToast } from '@/components/ui/Toast'
import {
  ArrowLeft,
  RefreshCw,
  Building2,
  User,
  FileText,
  Layers,
  ChevronDown,
  ChevronRight,
  Pencil,
  Check,
  X,
  AlertCircle,
  Loader2,
  Calendar,
  Quote,
} from 'lucide-react'
import { formatDate, cn } from '@/lib/utils'
import type { ResearchCluster, ClusterPaper, ResearchGroup } from '@/types'

function SyncStatusBanner({ group }: { group: ResearchGroup }) {
  const { t } = useTranslation()

  if (group.sync_status === 'ready' || group.sync_status === 'idle') {
    return null
  }

  const config: Record<string, { message: string; className: string; icon: React.ReactNode }> = {
    importing: {
      message: t(
        'projects.status.importing',
        'Importing papers from OpenAlex. This may take a few minutes...'
      ),
      className: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
    },
    clustering: {
      message: t(
        'projects.status.clustering',
        'Clustering papers by topic. Almost done...'
      ),
      className: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
    },
    failed: {
      message: t(
        'projects.status.failed',
        'The last sync failed. Please try again.'
      ),
      className: 'bg-red-50 border-red-200 text-red-800',
      icon: <AlertCircle className="h-4 w-4" />,
    },
  }

  const statusConfig = config[group.sync_status]
  if (!statusConfig) return null

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border px-4 py-3',
        statusConfig.className
      )}
    >
      {statusConfig.icon}
      <span className="text-sm font-medium">{statusConfig.message}</span>
    </div>
  )
}

function EditableClusterLabel({
  clusterId,
  projectId,
  initialLabel,
}: {
  clusterId: string
  projectId: string
  initialLabel: string
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [label, setLabel] = useState(initialLabel)
  const updateLabel = useUpdateClusterLabel()
  const { success, error: showError } = useToast()
  const { t } = useTranslation()

  const handleSave = async () => {
    if (!label.trim() || label === initialLabel) {
      setLabel(initialLabel)
      setIsEditing(false)
      return
    }

    try {
      await updateLabel.mutateAsync({ projectId, clusterId, label: label.trim() })
      success(
        t('projects.labelUpdated', 'Label updated'),
        t('projects.labelUpdatedDescription', 'Cluster label has been updated.')
      )
      setIsEditing(false)
    } catch {
      showError(
        t('projects.labelUpdateFailed', 'Failed to update label'),
        t('projects.tryAgain', 'Please try again.')
      )
      setLabel(initialLabel)
      setIsEditing(false)
    }
  }

  const handleCancel = () => {
    setLabel(initialLabel)
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  if (isEditing) {
    return (
      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
        <Input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={handleKeyDown}
          className="h-7 text-sm font-semibold w-48"
          autoFocus
        />
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={handleSave}
          disabled={updateLabel.isPending}
        >
          <Check className="h-3.5 w-3.5 text-green-600" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={handleCancel}
        >
          <X className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-base font-semibold">{initialLabel}</span>
      <button
        className="opacity-0 group-hover/cluster:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
        onClick={(e) => {
          e.stopPropagation()
          setIsEditing(true)
        }}
        aria-label={t('projects.editLabel', 'Edit cluster label')}
      >
        <Pencil className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

function PaperRow({ paper }: { paper: ClusterPaper }) {
  return (
    <Link
      to={`/papers/${paper.id}`}
      className="block px-4 py-3 hover:bg-muted/50 transition-colors border-b last:border-b-0"
    >
      <h4 className="text-sm font-medium line-clamp-2 hover:text-primary transition-colors">
        {paper.title}
      </h4>
      <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
        {paper.authors_display && (
          <span className="truncate max-w-[200px]">{paper.authors_display}</span>
        )}
        {paper.publication_date && (
          <span className="flex items-center gap-1 shrink-0">
            <Calendar className="h-3 w-3" />
            {formatDate(paper.publication_date)}
          </span>
        )}
        {paper.citations_count !== undefined && paper.citations_count !== null && (
          <span className="flex items-center gap-1 shrink-0">
            <Quote className="h-3 w-3" />
            {paper.citations_count} citations
          </span>
        )}
      </div>
    </Link>
  )
}

function ClusterAccordionItem({
  cluster,
  projectId,
  isExpanded,
  onToggle,
}: {
  cluster: ResearchCluster
  projectId: string
  isExpanded: boolean
  onToggle: () => void
}) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const displayPapers = cluster.top_papers.slice(0, 3)
  const hasMore = cluster.paper_count > 3

  return (
    <div className="rounded-lg border bg-card group/cluster">
      {/* Cluster header */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/30 transition-colors"
        onClick={onToggle}
        aria-expanded={isExpanded}
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <EditableClusterLabel
              clusterId={cluster.id}
              projectId={projectId}
              initialLabel={cluster.label}
            />
            <Badge variant="secondary" className="text-xs shrink-0">
              {t('projects.paperCount', '{{count}} papers', { count: cluster.paper_count })}
            </Badge>
          </div>
          {cluster.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {cluster.keywords.map((keyword) => (
                <Badge key={keyword} variant="outline" className="text-xs font-normal">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t">
          {displayPapers.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-muted-foreground">
              {t('projects.noPapersInCluster', 'No papers in this cluster yet.')}
            </div>
          ) : (
            <>
              {displayPapers.map((paper) => (
                <PaperRow key={paper.id} paper={paper} />
              ))}
              {hasMore && (
                <div className="px-4 py-2 border-t">
                  <Button
                    variant="link"
                    size="sm"
                    className="text-xs p-0 h-auto"
                    onClick={() =>
                      navigate(`/projects/${projectId}?cluster=${cluster.id}`)
                    }
                  >
                    {t('projects.showAllPapers', 'Show all {{count}} papers', {
                      count: cluster.paper_count,
                    })}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export function ProjectKanbanPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { success, error: showError } = useToast()

  const { data: group, isLoading: isLoadingGroup, error: groupError } = useResearchGroup(id!)
  const { data: clusters, isLoading: isLoadingClusters } = useResearchGroupClusters(id!)
  const syncGroup = useSyncResearchGroup()

  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set())

  const toggleCluster = useCallback((clusterId: string) => {
    setExpandedClusters((prev) => {
      const next = new Set(prev)
      if (next.has(clusterId)) {
        next.delete(clusterId)
      } else {
        next.add(clusterId)
      }
      return next
    })
  }, [])

  const handleSync = async () => {
    if (!id) return
    try {
      await syncGroup.mutateAsync(id)
      success(
        t('projects.syncStarted', 'Sync started'),
        t('projects.syncStartedDescription', 'Papers are being imported and clustered.')
      )
    } catch {
      showError(
        t('projects.syncFailed', 'Failed to start sync'),
        t('projects.tryAgain', 'Please try again.')
      )
    }
  }

  const isSyncing =
    group?.sync_status === 'importing' || group?.sync_status === 'clustering'

  if (isLoadingGroup) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <SkeletonCard className="h-12 w-12" />
          <div className="space-y-2 flex-1">
            <SkeletonCard className="h-6 w-48" />
            <SkeletonCard className="h-4 w-32" />
          </div>
        </div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    )
  }

  if (groupError || !group) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-destructive">
            {t('projects.notFound', 'Research group not found.')}
          </p>
          <Link to="/projects">
            <Button variant="link" className="mt-4">
              {t('projects.backToGroups', 'Back to Research Groups')}
            </Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/projects')}
            aria-label={t('projects.backToGroups', 'Back to Research Groups')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{group.name}</h1>
            <div className="flex items-center gap-4 mt-1">
              {(group.institution_name || group.pi_name) && (
                <span className="text-sm text-muted-foreground flex items-center gap-1.5">
                  {group.institution_name ? (
                    <>
                      <Building2 className="h-3.5 w-3.5" />
                      {group.institution_name}
                    </>
                  ) : (
                    <>
                      <User className="h-3.5 w-3.5" />
                      {group.pi_name}
                    </>
                  )}
                </span>
              )}
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" />
                {t('projects.paperCount', '{{count}} papers', { count: group.paper_count })}
              </span>
              {group.last_synced_at && (
                <span className="text-sm text-muted-foreground">
                  {t('projects.lastSynced', 'Last synced: {{date}}', {
                    date: formatDate(group.last_synced_at),
                  })}
                </span>
              )}
            </div>
            {group.description && (
              <p className="text-sm text-muted-foreground mt-2">{group.description}</p>
            )}
          </div>
        </div>
        <Button
          onClick={handleSync}
          disabled={isSyncing || syncGroup.isPending}
          isLoading={syncGroup.isPending}
        >
          <RefreshCw className={cn('h-4 w-4 mr-2', isSyncing && 'animate-spin')} />
          {isSyncing
            ? t('projects.syncing', 'Syncing...')
            : t('projects.sync', 'Sync')}
        </Button>
      </div>

      {/* Status Banner */}
      <SyncStatusBanner group={group} />

      {/* Clusters */}
      {isLoadingClusters ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : !clusters?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<Layers className="h-16 w-16" />}
              title={t('projects.noClusters', 'No clusters yet')}
              description={
                group.sync_status === 'idle'
                  ? t(
                      'projects.noClustersIdle',
                      'Click "Sync" to import papers and automatically cluster them by topic.'
                    )
                  : isSyncing
                    ? t(
                        'projects.noClustersSyncing',
                        'Papers are being imported and clustered. This may take a few minutes.'
                      )
                    : t(
                        'projects.noClustersDefault',
                        'Sync this research group to discover topic clusters from their publications.'
                      )
              }
              action={
                group.sync_status === 'idle'
                  ? {
                      label: t('projects.sync', 'Sync'),
                      onClick: handleSync,
                    }
                  : undefined
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Layers className="h-5 w-5 text-muted-foreground" />
              {t('projects.topicClusters', 'Topic Clusters')}
              <Badge variant="secondary">{clusters.length}</Badge>
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (expandedClusters.size === clusters.length) {
                  setExpandedClusters(new Set())
                } else {
                  setExpandedClusters(new Set(clusters.map((c) => c.id)))
                }
              }}
            >
              {expandedClusters.size === clusters.length
                ? t('projects.collapseAll', 'Collapse all')
                : t('projects.expandAll', 'Expand all')}
            </Button>
          </div>
          {clusters.map((cluster) => (
            <ClusterAccordionItem
              key={cluster.id}
              cluster={cluster}
              projectId={id!}
              isExpanded={expandedClusters.has(cluster.id)}
              onToggle={() => toggleCluster(cluster.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
