import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import {
  useAlerts,
  useDeleteAlert,
  useUpdateAlert,
  useTestAlert,
  useTriggerAlert,
  useAlertResults,
} from '@/hooks/useAlerts'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  Bell,
  BellOff,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Trash2,
  Play,
  Check,
  X,
  Plus,
  FlaskConical,
  History,
  Mail,
  Monitor,
  Search,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

export function AlertsPage() {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get('page') ?? '1')
  const pageSize = 10

  const [activeOnly, setActiveOnly] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [viewResultsAlertId, setViewResultsAlertId] = useState<string | undefined>(undefined)
  const [resultsPage, setResultsPage] = useState(1)

  const { data, isLoading, error } = useAlerts({
    page,
    page_size: pageSize,
    active_only: activeOnly,
  })
  const deleteAlert = useDeleteAlert()
  const updateAlert = useUpdateAlert()
  const testAlert = useTestAlert()
  const triggerAlert = useTriggerAlert()
  const { data: resultsData, isLoading: resultsLoading } = useAlertResults(
    viewResultsAlertId,
    { page: resultsPage, page_size: 10 }
  )

  const handlePageChange = (newPage: number) => {
    setSearchParams({ page: newPage.toString() })
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteAlert.mutateAsync(id)
      setDeleteConfirm(null)
      if (viewResultsAlertId === id) {
        setViewResultsAlertId(undefined)
      }
    } catch {
      // Error handled by mutation
    }
  }

  const handleToggleActive = async (id: string, currentActive: boolean) => {
    try {
      await updateAlert.mutateAsync({ id, data: { is_active: !currentActive } })
    } catch {
      // Error handled by mutation
    }
  }

  const handleTest = async (id: string) => {
    try {
      await testAlert.mutateAsync(id)
    } catch {
      // Error handled by mutation
    }
  }

  const handleTrigger = async (id: string) => {
    try {
      await triggerAlert.mutateAsync(id)
    } catch {
      // Error handled by mutation
    }
  }

  const handleViewResults = (alertId: string) => {
    if (viewResultsAlertId === alertId) {
      setViewResultsAlertId(undefined)
    } else {
      setViewResultsAlertId(alertId)
      setResultsPage(1)
    }
  }

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email':
        return <Mail className="h-3 w-3" />
      case 'in_app':
        return <Monitor className="h-3 w-3" />
      default:
        return null
    }
  }

  const getChannelLabel = (channel: string) => {
    switch (channel) {
      case 'email':
        return t('alerts.channelEmail')
      case 'in_app':
        return t('alerts.channelInApp')
      default:
        return channel
    }
  }

  const getFrequencyLabel = (frequency: string) => {
    switch (frequency) {
      case 'immediately':
        return t('alerts.frequencyImmediately')
      case 'daily':
        return t('alerts.frequencyDaily')
      case 'weekly':
        return t('alerts.frequencyWeekly')
      default:
        return frequency
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent':
        return (
          <Badge variant="default" className="gap-1 bg-green-600">
            <CheckCircle2 className="h-3 w-3" />
            {t('alerts.statusSent')}
          </Badge>
        )
      case 'failed':
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            {t('alerts.statusFailed')}
          </Badge>
        )
      case 'skipped':
        return (
          <Badge variant="secondary" className="gap-1">
            <X className="h-3 w-3" />
            {t('alerts.statusSkipped')}
          </Badge>
        )
      case 'pending':
        return (
          <Badge variant="outline" className="gap-1 border-yellow-500 text-yellow-600">
            <Clock className="h-3 w-3" />
            {t('alerts.statusPending')}
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('alerts.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('alerts.subtitle')}
          </p>
        </div>
        <Link to="/saved-searches">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            {t('alerts.createAlert')}
          </Button>
        </Link>
      </div>

      {/* Filter Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant={activeOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setActiveOnly(!activeOnly)
              setSearchParams({ page: '1' })
            }}
          >
            {activeOnly ? (
              <Bell className="h-4 w-4 mr-2" />
            ) : (
              <BellOff className="h-4 w-4 mr-2" />
            )}
            {activeOnly ? t('alerts.activeOnly') : t('alerts.allAlerts')}
          </Button>
        </div>
        {data && data.total > 0 && (
          <p className="text-sm text-muted-foreground">
            {t('common.pageOf', { page, pages: data.pages })}
          </p>
        )}
      </div>

      {/* Alerts List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            <AlertCircle className="mx-auto h-8 w-8 mb-2" />
            {t('alerts.loadFailed')}
          </CardContent>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Bell className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">{t('alerts.noAlerts')}</h3>
            <p className="text-muted-foreground text-sm mt-1">
              {t('alerts.noAlertsDescription')}
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {data?.items.map((alert) => (
              <Card key={alert.id} className="hover:bg-muted/30 transition-colors">
                <CardContent className="py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 className="font-medium">{alert.name}</h3>
                        <Badge variant="outline" className="gap-1">
                          {getChannelIcon(alert.channel)}
                          {getChannelLabel(alert.channel)}
                        </Badge>
                        <Badge variant="outline">
                          {getFrequencyLabel(alert.frequency)}
                        </Badge>
                        {alert.is_active ? (
                          <Badge variant="default" className="gap-1 bg-green-600">
                            <Bell className="h-3 w-3" />
                            {t('alerts.active')}
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="gap-1">
                            <BellOff className="h-3 w-3" />
                            {t('alerts.inactive')}
                          </Badge>
                        )}
                      </div>
                      {alert.saved_search && (
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-1">
                          <span className="flex items-center gap-1">
                            <Search className="h-3 w-3" />
                            {alert.saved_search.name}
                            {alert.saved_search.query && (
                              <code className="bg-muted px-1 rounded ml-1">
                                {alert.saved_search.query}
                              </code>
                            )}
                          </span>
                        </div>
                      )}
                      {alert.description && (
                        <p className="text-sm text-muted-foreground mb-1">
                          {alert.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        {alert.trigger_count > 0 && (
                          <span>{t('alerts.triggeredCount', { count: alert.trigger_count })}</span>
                        )}
                        {alert.last_triggered_at && (
                          <span>{t('alerts.lastTriggered', { date: formatDate(alert.last_triggered_at) })}</span>
                        )}
                        <span>{t('alerts.created', { date: formatDate(alert.created_at) })}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleActive(alert.id, alert.is_active)}
                        disabled={updateAlert.isPending}
                        title={alert.is_active ? t('alerts.deactivateAlert') : t('alerts.activateAlert')}
                      >
                        {alert.is_active ? (
                          <BellOff className="h-4 w-4" />
                        ) : (
                          <Bell className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleTest(alert.id)}
                        disabled={testAlert.isPending}
                        title={t('alerts.testAlert')}
                      >
                        <FlaskConical className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleTrigger(alert.id)}
                        disabled={triggerAlert.isPending}
                        title={t('alerts.triggerAlert')}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewResults(alert.id)}
                        title={t('alerts.viewResults')}
                      >
                        <History className="h-4 w-4" />
                      </Button>
                      {deleteConfirm === alert.id ? (
                        <div className="flex items-center gap-1">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDelete(alert.id)}
                            disabled={deleteAlert.isPending}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteConfirm(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteConfirm(alert.id)}
                          title={t('common.delete')}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {t('alerts.showingResults', { from: (page - 1) * pageSize + 1, to: Math.min(page * pageSize, data.total), total: data.total })}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  {t('common.previous')}
                </Button>
                <span className="text-sm">
                  {t('common.pageOf', { page, pages: data.pages })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= data.pages}
                >
                  {t('common.next')}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Results Panel */}
      {viewResultsAlertId && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <History className="h-5 w-5" />
              {t('alerts.alertResults')}
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setViewResultsAlertId(undefined)}
            >
              <X className="h-4 w-4 mr-1" />
              {t('common.close')}
            </Button>
          </div>

          {resultsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !resultsData?.items.length ? (
            <Card>
              <CardContent className="py-8 text-center">
                <History className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
                <p className="text-muted-foreground text-sm">
                  {t('alerts.noResults')}
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
                <CardContent className="p-0">
                  <div className="divide-y">
                    {resultsData.items.map((result) => (
                      <div
                        key={result.id}
                        className="flex items-center justify-between gap-4 px-4 py-3"
                      >
                        <div className="flex items-center gap-4 min-w-0">
                          {getStatusBadge(result.status)}
                          <div className="text-sm">
                            <span className="text-muted-foreground">
                              {t('alerts.papersFoundNew', { found: result.papers_found, new: result.new_papers })}
                            </span>
                          </div>
                          {result.error_message && (
                            <span className="text-sm text-destructive truncate max-w-xs">
                              {result.error_message}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground shrink-0">
                          {result.delivered_at
                            ? formatDate(result.delivered_at)
                            : formatDate(result.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Results Pagination */}
              {resultsData.pages > 1 && (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    {t('alerts.showingResultsDetail', { from: (resultsPage - 1) * 10 + 1, to: Math.min(resultsPage * 10, resultsData.total), total: resultsData.total })}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setResultsPage(resultsPage - 1)}
                      disabled={resultsPage <= 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      {t('common.previous')}
                    </Button>
                    <span className="text-sm">
                      {t('common.pageOf', { page: resultsPage, pages: resultsData.pages })}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setResultsPage(resultsPage + 1)}
                      disabled={resultsPage >= resultsData.pages}
                    >
                      {t('common.next')}
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
