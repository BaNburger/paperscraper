import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Clock,
  Shield,
  Database,
  Download,
  Play,
  Plus,
  Trash2,
  Check,
  Loader2,
  ChevronDown,
  ChevronRight,
  Info,
} from 'lucide-react'
import { complianceApi, exportApi } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToast } from '@/components/ui/Toast'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type {
  RetentionPolicy,
  RetentionEntityType,
  RetentionAction,
  SOC2ControlStatus,
  CreateRetentionPolicyRequest,
} from '@/types'

type TabType = 'audit-logs' | 'retention' | 'data-processing' | 'soc2'

const ENTITY_TYPE_LABELS: Record<RetentionEntityType, string> = {
  papers: 'Papers',
  audit_logs: 'Audit Logs',
  conversations: 'Transfer Conversations',
  submissions: 'Research Submissions',
  alerts: 'Alert Results',
  knowledge: 'Knowledge Sources',
}

const ACTION_LABELS: Record<RetentionAction, string> = {
  archive: 'Archive',
  anonymize: 'Anonymize',
  delete: 'Delete',
}

const SOC2_STATUS_STYLES: Record<SOC2ControlStatus, { bg: string; text: string; icon: React.ReactNode }> = {
  implemented: { bg: 'bg-green-100', text: 'text-green-800', icon: <Check className="h-3 w-3" /> },
  in_progress: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  pending: { bg: 'bg-gray-100', text: 'text-gray-800', icon: <Clock className="h-3 w-3" /> },
  not_applicable: { bg: 'bg-blue-100', text: 'text-blue-800', icon: <Info className="h-3 w-3" /> },
}

export function CompliancePage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('audit-logs')

  const tabs = [
    { id: 'audit-logs' as TabType, label: t('compliance.auditLogs'), icon: FileText },
    { id: 'retention' as TabType, label: t('compliance.dataRetention'), icon: Clock },
    { id: 'data-processing' as TabType, label: t('compliance.dataProcessing'), icon: Database },
    { id: 'soc2' as TabType, label: t('compliance.soc2Status'), icon: Shield },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('compliance.title')}</h1>
        <p className="text-muted-foreground">
          {t('compliance.subtitle')}
        </p>
      </div>

      <div className="border-b">
        <nav className="flex space-x-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2 border-b-2 transition-colors
                ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }
              `}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'audit-logs' && <AuditLogsTab />}
      {activeTab === 'retention' && <RetentionTab />}
      {activeTab === 'data-processing' && <DataProcessingTab />}
      {activeTab === 'soc2' && <SOC2Tab />}
    </div>
  )
}

// =============================================================================
// Audit Logs Tab
// =============================================================================

function AuditLogsTab() {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [actionFilter, setActionFilter] = useState<string>('')
  const toast = useToast()

  const { data: logs, isLoading } = useQuery({
    queryKey: ['compliance', 'audit-logs', page, actionFilter],
    queryFn: () =>
      complianceApi.searchAuditLogs({
        page,
        page_size: 50,
        action: actionFilter || undefined,
      }),
  })

  const { data: summary } = useQuery({
    queryKey: ['compliance', 'audit-logs-summary'],
    queryFn: () => complianceApi.getAuditLogSummary(),
  })

  const handleExport = async () => {
    try {
      const blob = await complianceApi.exportAuditLogs()
      exportApi.downloadFile(blob, `audit_logs_${new Date().toISOString().split('T')[0]}.csv`)
      toast.success(t('compliance.auditExportSuccess'))
    } catch {
      toast.error(t('compliance.auditExportFailed'))
    }
  }

  return (
    <div className="space-y-6">
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.totalLogs')}</p>
            <p className="text-2xl font-bold">{summary.total_logs.toLocaleString()}</p>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.actionTypes')}</p>
            <p className="text-2xl font-bold">{Object.keys(summary.logs_by_action).length}</p>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.activeUsers')}</p>
            <p className="text-2xl font-bold">{summary.logs_by_user.length}</p>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.timeRange')}</p>
            <p className="text-sm font-medium">
              {summary.time_range.earliest
                ? new Date(summary.time_range.earliest).toLocaleDateString()
                : 'N/A'}
              {' - '}
              {summary.time_range.latest
                ? new Date(summary.time_range.latest).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="border rounded-md px-3 py-1.5 text-sm"
          >
            <option value="">{t('compliance.allActions')}</option>
            {summary?.logs_by_action &&
              Object.keys(summary.logs_by_action).map((action) => (
                <option key={action} value={action}>
                  {action.replace(/_/g, ' ')}
                </option>
              ))}
          </select>
        </div>
        <Button onClick={handleExport} variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          {t('compliance.exportCsv')}
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : logs?.items.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-12 w-12" />}
          title={t('compliance.noAuditLogs')}
          description={t('compliance.noAuditLogsDescription')}
        />
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-4 py-3 font-medium">{t('compliance.timestamp')}</th>
                <th className="text-left px-4 py-3 font-medium">{t('compliance.action')}</th>
                <th className="text-left px-4 py-3 font-medium">{t('compliance.resource')}</th>
                <th className="text-left px-4 py-3 font-medium">{t('compliance.ipAddress')}</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {logs?.items.map((log) => (
                <tr key={log.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      {log.action.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {log.resource_type && (
                      <span className="text-muted-foreground">
                        {log.resource_type}
                        {log.resource_id && <span className="ml-1 text-xs">#{log.resource_id.slice(0, 8)}</span>}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                    {log.ip_address || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {logs && logs.pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            {t('compliance.previous')}
          </Button>
          <span className="px-4 py-2 text-sm text-muted-foreground">
            {t('common.page')} {page} {t('common.of')} {logs.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= logs.pages}
          >
            {t('compliance.next')}
          </Button>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Retention Tab
// =============================================================================

function RetentionTab() {
  const { t } = useTranslation()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [deletePolicy, setDeletePolicy] = useState<RetentionPolicy | null>(null)
  const [applyConfirm, setApplyConfirm] = useState(false)
  const toast = useToast()
  const queryClient = useQueryClient()

  const { data: policies, isLoading } = useQuery({
    queryKey: ['compliance', 'retention-policies'],
    queryFn: () => complianceApi.listRetentionPolicies(),
  })

  const { data: logs } = useQuery({
    queryKey: ['compliance', 'retention-logs'],
    queryFn: () => complianceApi.listRetentionLogs({ page: 1, page_size: 10 }),
  })

  const deleteMutation = useMutation({
    mutationFn: (policyId: string) => complianceApi.deleteRetentionPolicy(policyId),
    onSuccess: () => {
      toast.success(t('compliance.policyDeleted'))
      queryClient.invalidateQueries({ queryKey: ['compliance', 'retention-policies'] })
      setDeletePolicy(null)
    },
    onError: () => toast.error(t('compliance.policyDeleteFailed')),
  })

  const applyMutation = useMutation({
    mutationFn: (dryRun: boolean) => complianceApi.applyRetentionPolicies({ dry_run: dryRun }),
    onSuccess: (data) => {
      if (data.is_dry_run) {
        toast.success(t('compliance.dryRunComplete', { count: data.total_affected }))
      } else {
        toast.success(t('compliance.retentionApplied', { count: data.total_affected }))
      }
      queryClient.invalidateQueries({ queryKey: ['compliance'] })
      setApplyConfirm(false)
    },
    onError: () => toast.error(t('compliance.retentionApplyFailed')),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-medium">{t('compliance.retentionPolicies')}</h3>
          <p className="text-sm text-muted-foreground">
            {t('compliance.retentionPoliciesDescription')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => applyMutation.mutate(true)}>
            <Play className="h-4 w-4 mr-2" />
            {t('compliance.dryRun')}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setApplyConfirm(true)}>
            <Play className="h-4 w-4 mr-2" />
            {t('compliance.applyNow')}
          </Button>
          <Button size="sm" onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {t('compliance.addPolicy')}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : policies?.items.length === 0 ? (
        <EmptyState
          icon={<Clock className="h-12 w-12" />}
          title={t('compliance.noPolicies')}
          description={t('compliance.noPoliciesDescription')}
          action={{
            label: t('compliance.createPolicy'),
            onClick: () => setShowCreateDialog(true),
          }}
        />
      ) : (
        <div className="grid gap-4">
          {policies?.items.map((policy) => (
            <div key={policy.id} className="bg-card border rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium">{ENTITY_TYPE_LABELS[policy.entity_type]}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {policy.retention_days} days retention, then {ACTION_LABELS[policy.action].toLowerCase()}
                  </p>
                  {policy.description && (
                    <p className="text-sm text-muted-foreground mt-1">{policy.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      policy.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {policy.is_active ? t('compliance.active') : t('compliance.inactive')}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeletePolicy(policy)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              {policy.last_applied_at && (
                <p className="text-xs text-muted-foreground mt-3">
                  {t('compliance.lastApplied')}: {new Date(policy.last_applied_at).toLocaleString()} ({policy.records_affected} {t('compliance.records')})
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {logs && logs.items.length > 0 && (
        <div className="mt-8">
          <h3 className="font-medium mb-4">{t('compliance.recentRetentionLogs')}</h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">{t('compliance.date')}</th>
                  <th className="text-left px-4 py-3 font-medium">{t('compliance.entityType')}</th>
                  <th className="text-left px-4 py-3 font-medium">{t('compliance.action')}</th>
                  <th className="text-left px-4 py-3 font-medium">{t('compliance.records')}</th>
                  <th className="text-left px-4 py-3 font-medium">{t('compliance.status')}</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {logs.items.map((log) => (
                  <tr key={log.id}>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(log.started_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">{log.entity_type}</td>
                    <td className="px-4 py-3">{log.action}</td>
                    <td className="px-4 py-3">{log.records_affected}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          log.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : log.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {log.is_dry_run ? t('compliance.dryRunLabel') : log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!deletePolicy}
        onOpenChange={() => setDeletePolicy(null)}
        title={t('compliance.deletePolicyTitle')}
        description={t('compliance.deletePolicyDescription', { entity: deletePolicy ? ENTITY_TYPE_LABELS[deletePolicy.entity_type] : '' })}
        variant="destructive"
        confirmLabel={t('common.delete')}
        onConfirm={() => { if (deletePolicy) deleteMutation.mutate(deletePolicy.id) }}
      />

      <ConfirmDialog
        open={applyConfirm}
        onOpenChange={setApplyConfirm}
        title={t('compliance.applyPoliciesTitle')}
        description={t('compliance.applyPoliciesDescription')}
        variant="destructive"
        confirmLabel={t('compliance.applyNow')}
        onConfirm={() => applyMutation.mutate(false)}
      />

      {showCreateDialog && (
        <CreateRetentionPolicyDialog onClose={() => setShowCreateDialog(false)} />
      )}
    </div>
  )
}

function CreateRetentionPolicyDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation()
  const [entityType, setEntityType] = useState<RetentionEntityType>('papers')
  const [retentionDays, setRetentionDays] = useState(365)
  const [action, setAction] = useState<RetentionAction>('archive')
  const [description, setDescription] = useState('')
  const toast = useToast()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data: CreateRetentionPolicyRequest) => complianceApi.createRetentionPolicy(data),
    onSuccess: () => {
      toast.success(t('compliance.policyCreated'))
      queryClient.invalidateQueries({ queryKey: ['compliance', 'retention-policies'] })
      onClose()
    },
    onError: () => toast.error(t('compliance.policyCreateFailed')),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      entity_type: entityType,
      retention_days: retentionDays,
      action,
      description: description || undefined,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">{t('compliance.createRetentionPolicy')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('compliance.entityType')}</label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as RetentionEntityType)}
              className="w-full border rounded-md px-3 py-2"
            >
              {Object.entries(ENTITY_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('compliance.retentionPeriod')}</label>
            <input
              type="number"
              value={retentionDays}
              onChange={(e) => setRetentionDays(parseInt(e.target.value) || 0)}
              min={1}
              max={3650}
              className="w-full border rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('compliance.action')}</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value as RetentionAction)}
              className="w-full border rounded-md px-3 py-2"
            >
              {Object.entries(ACTION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('compliance.descriptionOptional')}</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full border rounded-md px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {t('common.create')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// =============================================================================
// Data Processing Tab
// =============================================================================

function DataProcessingTab() {
  const { t } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['compliance', 'data-processing'],
    queryFn: () => complianceApi.getDataProcessingInfo(),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-8">
      <div className="bg-card border rounded-lg p-6">
        <h3 className="font-medium mb-4">{t('compliance.hostingInformation')}</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">{t('compliance.provider')}</p>
            <p className="font-medium">{data.hosting_info.provider as string}</p>
          </div>
          <div>
            <p className="text-muted-foreground">{t('compliance.region')}</p>
            <p className="font-medium">{data.hosting_info.region as string}</p>
          </div>
          <div>
            <p className="text-muted-foreground">{t('compliance.certifications')}</p>
            <p className="font-medium">{(data.hosting_info.certifications as string[]).join(', ')}</p>
          </div>
          <div>
            <p className="text-muted-foreground">{t('compliance.dataLocations')}</p>
            <p className="font-medium">{data.data_locations.join(', ')}</p>
          </div>
        </div>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <h3 className="font-medium mb-4">{t('compliance.dataProcessors')}</h3>
        <div className="space-y-4">
          {data.processors.map((processor, i) => (
            <div key={i} className="border-b last:border-0 pb-4 last:pb-0">
              <div className="flex justify-between">
                <p className="font-medium">{processor.name}</p>
                <span className="text-sm text-muted-foreground">{processor.location}</span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{processor.purpose}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {t('compliance.dataTypes')}: {processor.data_types.join(', ')}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <h3 className="font-medium mb-4">{t('compliance.dataCategories')}</h3>
        <div className="space-y-4">
          {data.data_categories.map((category, i) => (
            <div key={i} className="border-b last:border-0 pb-4 last:pb-0">
              <div className="flex justify-between">
                <p className="font-medium">{category.category}</p>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                  {category.legal_basis}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{category.purpose}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {t('compliance.types')}: {category.types.join(', ')}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <h3 className="font-medium mb-4">{t('compliance.legalBasisRights')}</h3>
        <div className="space-y-4 text-sm">
          <div>
            <p className="text-muted-foreground">{t('compliance.processingGrounds')}</p>
            <p className="font-medium">{data.legal_basis.processing_grounds}</p>
          </div>
          <div>
            <p className="text-muted-foreground">{t('compliance.dpoContact')}</p>
            <p className="font-medium">{data.legal_basis.dpo_contact}</p>
          </div>
          <div>
            <p className="text-muted-foreground">{t('compliance.dataSubjectRights')}</p>
            <div className="flex flex-wrap gap-2 mt-1">
              {data.legal_basis.data_subject_rights.map((right) => (
                <span
                  key={right}
                  className="px-2 py-0.5 bg-muted rounded text-xs font-medium"
                >
                  {right}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// SOC2 Tab
// =============================================================================

function SOC2Tab() {
  const { t } = useTranslation()
  const [expandedCategories, setExpandedCategories] = useState<string[]>([])
  const toast = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['compliance', 'soc2-status'],
    queryFn: () => complianceApi.getSOC2Status(),
  })

  const handleExport = async () => {
    try {
      const report = await complianceApi.exportSOC2Report(true)
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
      exportApi.downloadFile(blob, `soc2_report_${new Date().toISOString().split('T')[0]}.json`)
      toast.success(t('compliance.soc2ReportExported'))
    } catch {
      toast.error(t('compliance.soc2ExportFailed'))
    }
  }

  const toggleCategory = (code: string) => {
    setExpandedCategories((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    )
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 flex-1">
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.totalControls')}</p>
            <p className="text-2xl font-bold">{data.summary.total_controls}</p>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.implemented')}</p>
            <p className="text-2xl font-bold text-green-600">
              {data.summary.status_counts.implemented}
            </p>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.inProgress')}</p>
            <p className="text-2xl font-bold text-yellow-600">
              {data.summary.status_counts.in_progress}
            </p>
          </div>
          <div className="bg-card border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">{t('compliance.compliancePercent')}</p>
            <p className="text-2xl font-bold">{data.summary.compliance_percentage}%</p>
          </div>
        </div>
        <Button onClick={handleExport} variant="outline" size="sm" className="ml-4">
          <Download className="h-4 w-4 mr-2" />
          {t('compliance.exportReport')}
        </Button>
      </div>

      <div className="space-y-4">
        {data.categories.map((category) => (
          <div key={category.code} className="border rounded-lg overflow-hidden">
            <button
              onClick={() => toggleCategory(category.code)}
              className="w-full flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                {expandedCategories.includes(category.code) ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                <span className="font-mono text-sm text-muted-foreground">{category.code}</span>
                <span className="font-medium">{category.name}</span>
              </div>
              <div className="flex gap-2">
                {['implemented', 'in_progress', 'pending'].map((status) => {
                  const count = category.controls.filter((c) => c.status === status).length
                  if (count === 0) return null
                  const style = SOC2_STATUS_STYLES[status as SOC2ControlStatus]
                  return (
                    <span
                      key={status}
                      className={`px-2 py-0.5 rounded text-xs font-medium ${style.bg} ${style.text}`}
                    >
                      {count}
                    </span>
                  )
                })}
              </div>
            </button>

            {expandedCategories.includes(category.code) && (
              <div className="divide-y">
                {category.controls.map((control) => {
                  const style = SOC2_STATUS_STYLES[control.status]
                  return (
                    <div key={control.id} className="p-4 flex items-start gap-4">
                      <span className="font-mono text-xs text-muted-foreground w-16 shrink-0">
                        {control.id}
                      </span>
                      <div className="flex-1">
                        <p className="text-sm">{control.description}</p>
                        {control.notes && (
                          <p className="text-xs text-muted-foreground mt-1">{control.notes}</p>
                        )}
                      </div>
                      <span
                        className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium shrink-0 ${style.bg} ${style.text}`}
                      >
                        {style.icon}
                        {control.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
