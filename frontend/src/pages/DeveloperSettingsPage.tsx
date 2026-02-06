import { useState } from 'react'
import {
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
  useWebhooks,
  useCreateWebhook,
  useTestWebhook,
  useDeleteWebhook,
  useRepositories,
  useCreateRepository,
  useSyncRepository,
  useDeleteRepository,
} from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToast } from '@/components/ui/Toast'
import type {
  CreateAPIKeyRequest,
  CreateWebhookRequest,
  CreateRepositorySourceRequest,
  WebhookEvent,
  RepositoryProvider,
} from '@/types'
import {
  Key,
  Webhook,
  Database,
  Plus,
  Trash2,
  Loader2,
  Copy,
  Play,
  RefreshCw,
  CheckCircle,
} from 'lucide-react'

const WEBHOOK_EVENTS: { value: WebhookEvent; label: string }[] = [
  { value: 'paper.created', label: 'Paper Created' },
  { value: 'paper.updated', label: 'Paper Updated' },
  { value: 'paper.deleted', label: 'Paper Deleted' },
  { value: 'paper.scored', label: 'Paper Scored' },
  { value: 'submission.created', label: 'Submission Created' },
  { value: 'submission.reviewed', label: 'Submission Reviewed' },
  { value: 'project.paper_moved', label: 'Paper Moved in Pipeline' },
  { value: 'author.contacted', label: 'Author Contacted' },
  { value: 'alert.triggered', label: 'Alert Triggered' },
]

const REPOSITORY_PROVIDERS: { value: RepositoryProvider; label: string }[] = [
  { value: 'openalex', label: 'OpenAlex' },
  { value: 'pubmed', label: 'PubMed' },
  { value: 'arxiv', label: 'arXiv' },
  { value: 'crossref', label: 'Crossref' },
  { value: 'semantic_scholar', label: 'Semantic Scholar' },
]

type TabType = 'api-keys' | 'webhooks' | 'repositories'

export function DeveloperSettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('api-keys')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Developer Settings</h1>
        <p className="text-muted-foreground">
          Configure API keys, webhooks, and repository sources
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('api-keys')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 -mb-px transition-colors ${
            activeTab === 'api-keys'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Key className="h-4 w-4" />
          API Keys
        </button>
        <button
          onClick={() => setActiveTab('webhooks')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 -mb-px transition-colors ${
            activeTab === 'webhooks'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Webhook className="h-4 w-4" />
          Webhooks
        </button>
        <button
          onClick={() => setActiveTab('repositories')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 -mb-px transition-colors ${
            activeTab === 'repositories'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Database className="h-4 w-4" />
          Repository Sources
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'api-keys' && <APIKeysTab />}
      {activeTab === 'webhooks' && <WebhooksTab />}
      {activeTab === 'repositories' && <RepositoriesTab />}
    </div>
  )
}

// =============================================================================
// API Keys Tab
// =============================================================================

function APIKeysTab() {
  const toast = useToast()
  const { data, isLoading } = useApiKeys()
  const createApiKey = useCreateApiKey()
  const revokeApiKey = useRevokeApiKey()

  const [showAddForm, setShowAddForm] = useState(false)
  const [revokeTarget, setRevokeTarget] = useState<string | null>(null)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [formData, setFormData] = useState<CreateAPIKeyRequest>({
    name: '',
    permissions: ['papers:read', 'search:query'],
  })

  const apiKeys = data?.items ?? []

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const result = await createApiKey.mutateAsync(formData)
      setNewKey(result.key)
      toast.success('API Key Created', 'Your new API key has been created. Copy it now - it will not be shown again!')
      setFormData({ name: '', permissions: ['papers:read', 'search:query'] })
    } catch {
      toast.error('Failed', 'Could not create API key')
    }
  }

  const handleRevoke = async () => {
    if (!revokeTarget) return
    try {
      await revokeApiKey.mutateAsync(revokeTarget)
      toast.success('API Key Revoked', 'The API key has been revoked')
      setRevokeTarget(null)
    } catch {
      toast.error('Failed', 'Could not revoke API key')
    }
  }

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    toast.success('Copied', 'API key copied to clipboard')
  }

  return (
    <div className="space-y-6">
      {/* New Key Display */}
      {newKey && (
        <Card className="border-green-500 bg-green-50 dark:bg-green-950/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div className="flex-1">
                <p className="font-medium text-green-600">New API Key Created</p>
                <p className="text-sm text-muted-foreground">
                  Copy this key now - it won't be shown again!
                </p>
                <code className="mt-2 block rounded bg-muted p-2 font-mono text-sm break-all">
                  {newKey}
                </code>
              </div>
              <Button
                size="sm"
                onClick={() => copyToClipboard(newKey)}
              >
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setNewKey(null)
                  setShowAddForm(false)
                }}
              >
                Done
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Form */}
      {showAddForm && !newKey && (
        <Card>
          <CardHeader>
            <CardTitle>Create API Key</CardTitle>
            <CardDescription>
              Generate a new API key for programmatic access to Paper Scraper
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label htmlFor="key-name" className="text-sm font-medium">
                  Key Name
                </label>
                <input
                  id="key-name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Production API, Development"
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createApiKey.isPending}>
                  Generate Key
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* API Keys List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>Manage programmatic access to your organization</CardDescription>
          </div>
          {!showAddForm && !newKey && (
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New API Key
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : apiKeys.length === 0 ? (
            <EmptyState
              icon={<Key className="h-16 w-16" />}
              title="No API keys"
              description="Create an API key to enable programmatic access"
              action={{
                label: 'Create API Key',
                onClick: () => setShowAddForm(true),
              }}
            />
          ) : (
            <div className="space-y-3">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Key className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{key.name}</p>
                        <Badge variant="outline">{key.key_prefix}...</Badge>
                        {!key.is_active && (
                          <Badge variant="destructive">Revoked</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Created {new Date(key.created_at).toLocaleDateString()}
                        {key.last_used_at && (
                          <> • Last used {new Date(key.last_used_at).toLocaleDateString()}</>
                        )}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setRevokeTarget(key.id)}
                    disabled={!key.is_active}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={!!revokeTarget}
        onOpenChange={(open) => !open && setRevokeTarget(null)}
        title="Revoke API Key"
        description="Are you sure you want to revoke this API key? Any applications using this key will lose access immediately."
        confirmLabel="Revoke"
        variant="destructive"
        onConfirm={handleRevoke}
        isLoading={revokeApiKey.isPending}
        icon={<Key className="h-6 w-6 text-destructive" />}
      />
    </div>
  )
}

// =============================================================================
// Webhooks Tab
// =============================================================================

function WebhooksTab() {
  const toast = useToast()
  const { data, isLoading } = useWebhooks()
  const createWebhook = useCreateWebhook()
  const testWebhook = useTestWebhook()
  const deleteWebhook = useDeleteWebhook()

  const [showAddForm, setShowAddForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<CreateWebhookRequest>({
    name: '',
    url: '',
    events: ['paper.created'],
  })

  const webhooks = data?.items ?? []

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createWebhook.mutateAsync(formData)
      toast.success('Webhook Created', 'Your webhook has been configured')
      setShowAddForm(false)
      setFormData({ name: '', url: '', events: ['paper.created'] })
    } catch {
      toast.error('Failed', 'Could not create webhook')
    }
  }

  const handleTest = async (id: string) => {
    setTestingId(id)
    try {
      const result = await testWebhook.mutateAsync(id)
      if (result.success) {
        toast.success('Test Successful', `Webhook responded in ${result.response_time_ms}ms`)
      } else {
        toast.error('Test Failed', result.error || 'Webhook did not respond successfully')
      }
    } catch {
      toast.error('Test Failed', 'Could not send test event')
    } finally {
      setTestingId(null)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteWebhook.mutateAsync(deleteTarget)
      toast.success('Webhook Deleted', 'The webhook has been removed')
      setDeleteTarget(null)
    } catch {
      toast.error('Failed', 'Could not delete webhook')
    }
  }

  const toggleEvent = (event: WebhookEvent) => {
    const events = formData.events.includes(event)
      ? formData.events.filter((e) => e !== event)
      : [...formData.events, event]
    setFormData({ ...formData, events })
  }

  return (
    <div className="space-y-6">
      {/* Add Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create Webhook</CardTitle>
            <CardDescription>
              Configure a webhook to receive event notifications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label htmlFor="webhook-name" className="text-sm font-medium">
                    Name
                  </label>
                  <input
                    id="webhook-name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Slack Notifications"
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="webhook-url" className="text-sm font-medium">
                    URL
                  </label>
                  <input
                    id="webhook-url"
                    type="url"
                    required
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    placeholder="https://example.com/webhook"
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Events</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {WEBHOOK_EVENTS.map((event) => (
                    <button
                      key={event.value}
                      type="button"
                      onClick={() => toggleEvent(event.value)}
                      className={`rounded-full px-3 py-1 text-sm transition-colors ${
                        formData.events.includes(event.value)
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground hover:bg-muted/80'
                      }`}
                    >
                      {event.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  isLoading={createWebhook.isPending}
                  disabled={formData.events.length === 0}
                >
                  Create Webhook
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Webhooks List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Webhooks</CardTitle>
            <CardDescription>Receive real-time notifications for events</CardDescription>
          </div>
          {!showAddForm && (
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Webhook
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : webhooks.length === 0 ? (
            <EmptyState
              icon={<Webhook className="h-16 w-16" />}
              title="No webhooks"
              description="Configure webhooks to receive event notifications"
              action={{
                label: 'Add Webhook',
                onClick: () => setShowAddForm(true),
              }}
            />
          ) : (
            <div className="space-y-3">
              {webhooks.map((webhook) => (
                <div
                  key={webhook.id}
                  className="rounded-lg border p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <Webhook className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{webhook.name}</p>
                          {webhook.is_active ? (
                            <Badge variant="default">Active</Badge>
                          ) : (
                            <Badge variant="destructive">Disabled</Badge>
                          )}
                          {webhook.failure_count > 0 && (
                            <Badge variant="secondary">
                              {webhook.failure_count} failures
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground truncate max-w-md">
                          {webhook.url}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTest(webhook.id)}
                        disabled={testingId === webhook.id}
                      >
                        {testingId === webhook.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4 mr-1" />
                        )}
                        Test
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeleteTarget(webhook.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {webhook.events.map((event) => (
                      <Badge key={event} variant="outline" className="text-xs">
                        {event}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Webhook"
        description="Are you sure you want to delete this webhook? You will stop receiving event notifications."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteWebhook.isPending}
        icon={<Webhook className="h-6 w-6 text-destructive" />}
      />
    </div>
  )
}

// =============================================================================
// Repositories Tab
// =============================================================================

function RepositoriesTab() {
  const toast = useToast()
  const { data, isLoading } = useRepositories()
  const createRepository = useCreateRepository()
  const syncRepository = useSyncRepository()
  const deleteRepository = useDeleteRepository()

  const [showAddForm, setShowAddForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [syncingId, setSyncingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<CreateRepositorySourceRequest>({
    name: '',
    provider: 'openalex',
    config: { query: '', max_results: 100 },
  })

  const repositories = data?.items ?? []

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createRepository.mutateAsync(formData)
      toast.success('Repository Added', 'Your data source has been configured')
      setShowAddForm(false)
      setFormData({
        name: '',
        provider: 'openalex',
        config: { query: '', max_results: 100 },
      })
    } catch {
      toast.error('Failed', 'Could not create repository source')
    }
  }

  const handleSync = async (id: string) => {
    setSyncingId(id)
    try {
      const result = await syncRepository.mutateAsync(id)
      toast.success('Sync Started', result.message)
    } catch {
      toast.error('Sync Failed', 'Could not trigger sync')
    } finally {
      setSyncingId(null)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteRepository.mutateAsync(deleteTarget)
      toast.success('Repository Removed', 'The data source has been removed')
      setDeleteTarget(null)
    } catch {
      toast.error('Failed', 'Could not delete repository')
    }
  }

  return (
    <div className="space-y-6">
      {/* Add Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add Repository Source</CardTitle>
            <CardDescription>
              Configure a data source for automatic paper imports
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label htmlFor="repo-name" className="text-sm font-medium">
                    Name
                  </label>
                  <input
                    id="repo-name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Biotech Papers"
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="repo-provider" className="text-sm font-medium">
                    Provider
                  </label>
                  <select
                    id="repo-provider"
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value as RepositoryProvider })}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  >
                    {REPOSITORY_PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label htmlFor="repo-query" className="text-sm font-medium">
                  Search Query
                </label>
                <input
                  id="repo-query"
                  type="text"
                  value={formData.config?.query ?? ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    config: { ...formData.config, query: e.target.value },
                  })}
                  placeholder="e.g., CRISPR gene editing"
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label htmlFor="repo-max-results" className="text-sm font-medium">
                    Max Results per Sync
                  </label>
                  <input
                    id="repo-max-results"
                    type="number"
                    min={1}
                    max={1000}
                    value={formData.config?.max_results ?? 100}
                    onChange={(e) => setFormData({
                      ...formData,
                      config: { ...formData.config, max_results: parseInt(e.target.value, 10) || 100 },
                    })}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="repo-schedule" className="text-sm font-medium">
                    Schedule (Cron)
                  </label>
                  <input
                    id="repo-schedule"
                    type="text"
                    value={formData.schedule ?? ''}
                    onChange={(e) => setFormData({ ...formData, schedule: e.target.value || undefined })}
                    placeholder="e.g., 0 6 * * * (6 AM daily)"
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Leave empty for manual sync only
                  </p>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createRepository.isPending}>
                  Add Source
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Repositories List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Repository Sources</CardTitle>
            <CardDescription>Data sources for automatic paper imports</CardDescription>
          </div>
          {!showAddForm && (
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Source
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : repositories.length === 0 ? (
            <EmptyState
              icon={<Database className="h-16 w-16" />}
              title="No repository sources"
              description="Add a data source to automatically import papers"
              action={{
                label: 'Add Source',
                onClick: () => setShowAddForm(true),
              }}
            />
          ) : (
            <div className="space-y-3">
              {repositories.map((repo) => (
                <div
                  key={repo.id}
                  className="rounded-lg border p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <Database className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{repo.name}</p>
                          <Badge variant="outline">
                            {REPOSITORY_PROVIDERS.find((p) => p.value === repo.provider)?.label ?? repo.provider}
                          </Badge>
                          {repo.is_active ? (
                            <Badge variant="default">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Paused</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {repo.papers_synced.toLocaleString()} papers synced
                          {repo.last_sync_at && (
                            <> • Last sync {new Date(repo.last_sync_at).toLocaleDateString()}</>
                          )}
                          {repo.schedule && <> • {repo.schedule}</>}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSync(repo.id)}
                        disabled={syncingId === repo.id}
                      >
                        {syncingId === repo.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="h-4 w-4 mr-1" />
                        )}
                        Sync Now
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeleteTarget(repo.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                  {repo.config?.query && (
                    <p className="mt-2 text-sm text-muted-foreground">
                      Query: "{repo.config.query}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Remove Repository Source"
        description="Are you sure you want to remove this data source? Papers already imported will not be affected."
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteRepository.isPending}
        icon={<Database className="h-6 w-6 text-destructive" />}
      />
    </div>
  )
}
