import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  useModelConfigurations,
  useModelUsage,
  useCreateModelConfiguration,
  useUpdateModelConfiguration,
  useDeleteModelConfiguration,
} from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToast } from '@/components/ui/Toast'
import type { CreateModelConfigurationRequest, ModelConfiguration } from '@/types'
import { Bot, Plus, Trash2, Loader2, Zap, DollarSign, Activity } from 'lucide-react'

const PROVIDERS = ['openai', 'anthropic', 'azure', 'ollama'] as const

export function ModelSettingsPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const { data: configsData, isLoading: configsLoading } = useModelConfigurations()
  const { data: usageData, isLoading: usageLoading } = useModelUsage(30)
  const createModel = useCreateModelConfiguration()
  const updateModel = useUpdateModelConfiguration()
  const deleteModel = useDeleteModelConfiguration()

  const [showAddForm, setShowAddForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [formData, setFormData] = useState<CreateModelConfigurationRequest>({
    provider: 'openai',
    model_name: '',
    is_default: false,
    api_key: '',
    max_tokens: 4096,
    temperature: 0.3,
  })

  const configs = configsData?.items ?? []

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createModel.mutateAsync(formData)
      toast.success(t('modelSettings.modelAdded'), t('modelSettings.modelAddedDescription'))
      setShowAddForm(false)
      setFormData({
        provider: 'openai',
        model_name: '',
        is_default: false,
        api_key: '',
        max_tokens: 4096,
        temperature: 0.3,
      })
    } catch {
      toast.error(t('common.error'), t('modelSettings.createFailed'))
    }
  }

  const handleSetDefault = async (config: ModelConfiguration) => {
    try {
      await updateModel.mutateAsync({
        id: config.id,
        data: { is_default: true },
      })
      toast.success(t('modelSettings.defaultUpdated'), t('modelSettings.defaultUpdatedDescription', { name: config.model_name }))
    } catch {
      toast.error(t('common.error'), t('modelSettings.updateDefaultFailed'))
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteModel.mutateAsync(deleteTarget)
      toast.success(t('modelSettings.modelRemoved'), t('modelSettings.modelRemovedDescription'))
      setDeleteTarget(null)
    } catch {
      toast.error(t('common.error'), t('modelSettings.deleteFailed'))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('modelSettings.title')}</h1>
          <p className="text-muted-foreground">{t('modelSettings.subtitle')}</p>
        </div>
        <Button onClick={() => setShowAddForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('modelSettings.addModel')}
        </Button>
      </div>

      {/* Usage Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {t('modelSettings.totalRequests')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usageLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <p className="text-2xl font-bold">{usageData?.total_requests ?? 0}</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <Activity className="h-3 w-3" />
              {t('modelSettings.totalTokens')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usageLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <p className="text-2xl font-bold">
                {(usageData?.total_tokens ?? 0).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              {t('modelSettings.totalCost')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usageLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <p className="text-2xl font-bold">
                ${(usageData?.total_cost_usd ?? 0).toFixed(4)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Add Model Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>{t('modelSettings.addModelConfig')}</CardTitle>
            <CardDescription>{t('modelSettings.addModelConfigDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label htmlFor="provider" className="text-sm font-medium">{t('modelSettings.provider')}</label>
                  <select
                    id="provider"
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  >
                    {PROVIDERS.map((p) => (
                      <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="model_name" className="text-sm font-medium">{t('modelSettings.modelName')}</label>
                  <input
                    id="model_name"
                    type="text"
                    required
                    value={formData.model_name}
                    onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                    placeholder="e.g. gpt-4o-mini"
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="api_key" className="text-sm font-medium">{t('modelSettings.apiKey')}</label>
                  <input
                    id="api_key"
                    type="password"
                    value={formData.api_key ?? ''}
                    onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                    placeholder="sk-..."
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="max_tokens" className="text-sm font-medium">{t('modelSettings.maxTokens')}</label>
                  <input
                    id="max_tokens"
                    type="number"
                    min={1}
                    max={128000}
                    value={formData.max_tokens ?? 4096}
                    onChange={(e) => setFormData({ ...formData, max_tokens: e.target.value === '' ? 4096 : parseInt(e.target.value, 10) })}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="temperature" className="text-sm font-medium">{t('modelSettings.temperature')}</label>
                  <input
                    id="temperature"
                    type="number"
                    min={0}
                    max={2}
                    step={0.1}
                    value={formData.temperature ?? 0.3}
                    onChange={(e) => setFormData({ ...formData, temperature: e.target.value === '' ? 0.3 : parseFloat(e.target.value) })}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={formData.is_default ?? false}
                      onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                      className="rounded border"
                    />
                    {t('modelSettings.setAsDefault')}
                  </label>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  {t('common.cancel')}
                </Button>
                <Button type="submit" isLoading={createModel.isPending}>
                  {t('modelSettings.addModel')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Model Configurations */}
      <Card>
        <CardHeader>
          <CardTitle>{t('modelSettings.configuredModels')}</CardTitle>
          <CardDescription>{t('modelSettings.configuredModelsDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {configsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : configs.length === 0 ? (
            <EmptyState
              icon={<Bot className="h-16 w-16" />}
              title={t('modelSettings.noModels')}
              description={t('modelSettings.noModelsDescription')}
              action={{
                label: t('modelSettings.addModel'),
                onClick: () => setShowAddForm(true),
              }}
            />
          ) : (
            <div className="space-y-3">
              {configs.map((config) => (
                <div
                  key={config.id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Bot className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{config.model_name}</p>
                        <Badge variant="outline">{config.provider}</Badge>
                        {config.is_default && (
                          <Badge variant="default">Default</Badge>
                        )}
                        {config.has_api_key && (
                          <Badge variant="secondary">Key set</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Max tokens: {config.max_tokens} | Temperature: {config.temperature}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!config.is_default && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSetDefault(config)}
                      >
                        {t('modelSettings.setDefault')}
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setDeleteTarget(config.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage by Operation */}
      {usageData && Object.keys(usageData.by_operation).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t('modelSettings.usageByOperation')}</CardTitle>
            <CardDescription>{t('modelSettings.usageByOperationDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(usageData.by_operation).map(([operation, stats]) => (
                <div key={operation} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="font-medium capitalize">{operation}</p>
                    <p className="text-sm text-muted-foreground">
                      {stats.requests} requests | {stats.tokens.toLocaleString()} tokens
                    </p>
                  </div>
                  <p className="text-sm font-medium">${stats.cost_usd.toFixed(4)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={t('modelSettings.deleteTitle')}
        description={t('modelSettings.deleteDescription')}
        confirmLabel={t('common.delete')}
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteModel.isPending}
        icon={<Trash2 className="h-6 w-6 text-destructive" />}
      />
    </div>
  )
}
