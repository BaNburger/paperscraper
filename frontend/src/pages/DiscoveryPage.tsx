import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useDiscoveryProfiles, useDiscoveryRuns, useTriggerDiscovery } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonCard } from '@/components/ui/Skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { useToast } from '@/components/ui/Toast'
import { Compass, History, Play, Plus, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { DiscoveryProfileSummary, DiscoveryRunStatus } from '@/types'

function getRunStatusVariant(status: DiscoveryRunStatus | null): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'completed':
      return 'default'
    case 'running':
      return 'secondary'
    case 'completed_with_errors':
      return 'outline'
    case 'failed':
      return 'destructive'
    default:
      return 'secondary'
  }
}

function getRunStatusLabel(status: DiscoveryRunStatus | null, t: (key: string, fallback: string) => string): string {
  switch (status) {
    case 'running':
      return t('discovery.statusRunning', 'Running')
    case 'completed':
      return t('discovery.statusCompleted', 'Completed')
    case 'completed_with_errors':
      return t('discovery.statusCompletedWithErrors', 'Completed with errors')
    case 'failed':
      return t('discovery.statusFailed', 'Failed')
    default:
      return t('discovery.neverRun', 'Never run')
  }
}

function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    openalex: 'OpenAlex',
    pubmed: 'PubMed',
    arxiv: 'arXiv',
    crossref: 'Crossref',
    semantic_scholar: 'Semantic Scholar',
  }
  return labels[source] ?? source
}

interface ProfileCardProps {
  profile: DiscoveryProfileSummary
  onRunNow: (id: string) => void
  onShowHistory: (profile: DiscoveryProfileSummary) => void
  isTriggering: boolean
  triggeringId: string | null
}

function ProfileCard({ profile, onRunNow, onShowHistory, isTriggering, triggeringId }: ProfileCardProps) {
  const { t } = useTranslation()
  const isThisTriggering = isTriggering && triggeringId === profile.id

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base line-clamp-1">{profile.name}</CardTitle>
          {profile.last_run_status && (
            <Badge variant={getRunStatusVariant(profile.last_run_status)} className="shrink-0">
              {getRunStatusLabel(profile.last_run_status, t)}
            </Badge>
          )}
        </div>
        {profile.query && (
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {profile.query}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between gap-4">
        <div className="space-y-3">
          {/* Source badges */}
          {profile.import_sources.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {profile.import_sources.map((source) => (
                <Badge key={source} variant="secondary" className="text-xs">
                  {getSourceLabel(source)}
                </Badge>
              ))}
            </div>
          )}

          {/* Metadata rows */}
          <div className="space-y-1.5 text-sm text-muted-foreground">
            {profile.target_project_name && (
              <p>
                <span className="font-medium text-foreground">
                  {t('discovery.targetProject', 'Target Project')}:
                </span>{' '}
                {profile.target_project_name}
              </p>
            )}
            {profile.discovery_frequency && (
              <p>
                <span className="font-medium text-foreground">
                  {t('discovery.frequency', 'Frequency')}:
                </span>{' '}
                <Badge variant="outline" className="ml-1 text-xs capitalize">
                  {profile.discovery_frequency}
                </Badge>
              </p>
            )}
            <p>
              <span className="font-medium text-foreground">
                {t('discovery.maxPerRun', 'Max per run')}:
              </span>{' '}
              {profile.max_import_per_run}
            </p>
            <p>
              <span className="font-medium text-foreground">
                {t('discovery.papersImported', 'Papers imported')}:
              </span>{' '}
              {profile.total_papers_imported}
            </p>
          </div>

          {/* Last discovery time */}
          <p className="text-xs text-muted-foreground">
            {profile.last_discovery_at
              ? t('discovery.lastRun', 'Last run') +
                ': ' +
                formatDistanceToNow(new Date(profile.last_discovery_at), {
                  addSuffix: true,
                })
              : t('discovery.neverRun', 'Never run')}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => onRunNow(profile.id)}
            disabled={isThisTriggering}
            className="flex-1"
          >
            {isThisTriggering ? (
              <>
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                {t('discovery.running', 'Running...')}
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-1.5" />
                {t('discovery.runNow', 'Run Now')}
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onShowHistory(profile)}
            aria-label={t('discovery.history', 'History')}
          >
            <History className="h-4 w-4 mr-1.5" />
            {t('discovery.history', 'History')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

interface HistoryDialogProps {
  profile: DiscoveryProfileSummary | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function HistoryDialog({ profile, open, onOpenChange }: HistoryDialogProps) {
  const { t } = useTranslation()
  const { data: runsData, isLoading } = useDiscoveryRuns(profile?.id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {t('discovery.history', 'History')} - {profile?.name}
          </DialogTitle>
          <DialogDescription>
            {t('discovery.historyDescription', 'Past discovery runs for this profile')}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto -mx-6 px-6">
          {isLoading ? (
            <div className="space-y-3 py-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="animate-pulse rounded-lg border p-4 space-y-2">
                  <div className="h-4 w-1/3 bg-muted rounded" />
                  <div className="h-3 w-2/3 bg-muted rounded" />
                </div>
              ))}
            </div>
          ) : !runsData?.items?.length ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {t('discovery.noRuns', 'No discovery runs yet')}
            </p>
          ) : (
            <div className="space-y-3 py-4">
              {runsData.items.map((run) => (
                <div key={run.id} className="rounded-lg border p-4 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {getSourceLabel(run.source)}
                      </Badge>
                      <Badge variant={getRunStatusVariant(run.status)} className="text-xs">
                        {getRunStatusLabel(run.status, t)}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">
                      {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                    <span>
                      {t('discovery.papersFound', 'Found')}: {run.papers_found}
                    </span>
                    <span>
                      {t('discovery.papersImported', 'Imported')}: {run.papers_imported}
                    </span>
                    <span>
                      {t('discovery.papersSkipped', 'Skipped')}: {run.papers_skipped}
                    </span>
                    {run.papers_added_to_project > 0 && (
                      <span>
                        {t('discovery.addedToProject', 'Added to project')}: {run.papers_added_to_project}
                      </span>
                    )}
                  </div>
                  {run.error_message && (
                    <p className="text-xs text-destructive">{run.error_message}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t('common.close', 'Close')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function DiscoveryPage() {
  const { t } = useTranslation()
  const [historyProfile, setHistoryProfile] = useState<DiscoveryProfileSummary | null>(null)
  const [triggeringId, setTriggeringId] = useState<string | null>(null)

  const navigate = useNavigate()
  const { data: profiles, isLoading, error } = useDiscoveryProfiles()
  const triggerDiscovery = useTriggerDiscovery()
  const { success, error: showError } = useToast()

  const handleRunNow = async (savedSearchId: string) => {
    setTriggeringId(savedSearchId)
    try {
      const result = await triggerDiscovery.mutateAsync(savedSearchId)
      success(
        t('discovery.triggerSuccess', 'Discovery run started'),
        result.message
      )
    } catch {
      showError(
        t('discovery.triggerFailed', 'Failed to start discovery'),
        t('discovery.tryAgain', 'Please try again later')
      )
    } finally {
      setTriggeringId(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {t('discovery.title', 'Discovery Profiles')}
          </h1>
          <p className="text-muted-foreground mt-1">
            {t('discovery.subtitle', 'Automated paper discovery from external sources')}
          </p>
        </div>
        <Button onClick={() => navigate('/saved-searches')}>
          <Plus className="h-4 w-4 mr-2" />
          {t('discovery.newProfile', 'New Profile')}
        </Button>
      </div>

      {/* Profiles Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            {t('discovery.loadFailed', 'Failed to load discovery profiles')}
          </CardContent>
        </Card>
      ) : !profiles?.items?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<Compass className="h-16 w-16" />}
              title={t('discovery.noProfiles', 'No discovery profiles')}
              description={t(
                'discovery.noProfilesDescription',
                'Create a saved search with auto-import enabled to start discovering papers automatically.'
              )}
              action={{
                label: t('discovery.newProfile', 'New Profile'),
                onClick: () => navigate('/saved-searches'),
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {profiles.items.map((profile) => (
            <ProfileCard
              key={profile.id}
              profile={profile}
              onRunNow={handleRunNow}
              onShowHistory={setHistoryProfile}
              isTriggering={triggerDiscovery.isPending}
              triggeringId={triggeringId}
            />
          ))}
        </div>
      )}

      {/* History Dialog */}
      <HistoryDialog
        profile={historyProfile}
        open={historyProfile !== null}
        onOpenChange={(open) => {
          if (!open) setHistoryProfile(null)
        }}
      />
    </div>
  )
}
