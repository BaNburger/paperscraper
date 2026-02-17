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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { useToast } from '@/components/ui/Toast'
import type { CreateModelConfigurationRequest, ModelConfiguration } from '@/types'
import {
  MODEL_CATALOG,
  getModelsForProvider,
  getModel,
  getProvider,
  formatContextWindow,
  formatPrice,
  WORKFLOW_OPTIONS,
  type ModelInfo,
} from '@/lib/modelCatalog'
import {
  Bot,
  Plus,
  Trash2,
  Loader2,
  Zap,
  DollarSign,
  Activity,
  ChevronRight,
  ChevronLeft,
  Settings2,
  Sparkles,
  Check,
  ArrowRight,
} from 'lucide-react'

type ModalStep = 'provider' | 'model' | 'confirm'

export function ModelSettingsPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const { data: configsData, isLoading: configsLoading } = useModelConfigurations()
  const { data: usageData, isLoading: usageLoading } = useModelUsage(30)
  const createModel = useCreateModelConfiguration()
  const updateModel = useUpdateModelConfiguration()
  const deleteModel = useDeleteModelConfiguration()

  // Add model modal state
  const [showAddModal, setShowAddModal] = useState(false)
  const [modalStep, setModalStep] = useState<ModalStep>('provider')
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [customModelName, setCustomModelName] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [maxTokens, setMaxTokens] = useState(4096)
  const [temperature, setTemperature] = useState(0.3)
  const [isDefault, setIsDefault] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Delete state
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const configs = configsData?.items ?? []

  // --------------------------------------------------
  // Modal helpers
  // --------------------------------------------------
  function resetModal() {
    setModalStep('provider')
    setSelectedProvider('')
    setSelectedModelId('')
    setCustomModelName('')
    setApiKey('')
    setMaxTokens(4096)
    setTemperature(0.3)
    setIsDefault(false)
    setShowAdvanced(false)
  }

  function openAddModal() {
    resetModal()
    setShowAddModal(true)
  }

  function handleSelectProvider(providerId: string) {
    setSelectedProvider(providerId)
    setSelectedModelId('')
    setCustomModelName('')
    setApiKey('')
    setModalStep('model')
  }

  const providerInfo = selectedProvider ? getProvider(selectedProvider) : undefined
  const catalogModels = selectedProvider ? getModelsForProvider(selectedProvider) : []
  const isFreeText = providerInfo?.freeTextModel ?? false
  const selectedModelInfo: ModelInfo | undefined = selectedModelId
    ? getModel(selectedProvider, selectedModelId)
    : undefined

  const resolvedModelName = isFreeText ? customModelName : selectedModelId

  const handleCreate = async () => {
    const data: CreateModelConfigurationRequest = {
      provider: selectedProvider,
      model_name: resolvedModelName,
      is_default: isDefault,
      api_key: apiKey || undefined,
      max_tokens: maxTokens,
      temperature,
    }
    try {
      await createModel.mutateAsync(data)
      toast.success(t('modelSettings.modelAdded'), t('modelSettings.modelAddedDescription'))
      setShowAddModal(false)
      resetModal()
    } catch {
      toast.error(t('common.error'), t('modelSettings.createFailed'))
    }
  }

  const handleSetDefault = async (config: ModelConfiguration) => {
    try {
      await updateModel.mutateAsync({ id: config.id, data: { is_default: true } })
      toast.success(
        t('modelSettings.defaultUpdated'),
        t('modelSettings.defaultUpdatedDescription', { name: config.model_name }),
      )
    } catch {
      toast.error(t('common.error'), t('modelSettings.updateDefaultFailed'))
    }
  }

  const handleWorkflowChange = async (configId: string, workflow: string) => {
    // Clear workflow from any other config that has it
    const existingConfig = configs.find((c) => c.workflow === workflow && c.id !== configId)
    if (existingConfig) {
      await updateModel.mutateAsync({ id: existingConfig.id, data: { workflow: '' } })
    }
    try {
      await updateModel.mutateAsync({ id: configId, data: { workflow: workflow || '' } })
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

  // --------------------------------------------------
  // Welcome state (no models configured)
  // --------------------------------------------------
  if (!configsLoading && configs.length === 0) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
            <Bot className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">{t('modelSettings.welcomeTitle')}</h1>
          <p className="mt-2 text-muted-foreground">
            {t('modelSettings.welcomeDescription')}
          </p>
          <Button className="mt-6" size="lg" onClick={openAddModal}>
            {t('modelSettings.getStarted')}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>

        {/* Add Model Modal (rendered for welcome state too) */}
        <AddModelModal />
      </div>
    )
  }

  // --------------------------------------------------
  // Full page layout
  // --------------------------------------------------
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('modelSettings.title')}</h1>
          <p className="text-muted-foreground">{t('modelSettings.subtitle')}</p>
        </div>
        <Button onClick={openAddModal}>
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

      {/* Workflow Assignment */}
      {configs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5" />
              {t('modelSettings.workflowAssignment')}
            </CardTitle>
            <CardDescription>{t('modelSettings.workflowAssignmentDescription')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {WORKFLOW_OPTIONS.map((wf) => {
                const assignedConfig = configs.find((c) => c.workflow === wf.id)
                return (
                  <div
                    key={wf.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="font-medium">{t(wf.labelKey)}</p>
                      <p className="text-sm text-muted-foreground">{t(wf.descKey)}</p>
                    </div>
                    <select
                      value={assignedConfig?.id ?? ''}
                      onChange={(e) => {
                        const newId = e.target.value
                        if (newId) {
                          handleWorkflowChange(newId, wf.id)
                        } else if (assignedConfig) {
                          // Unassign
                          updateModel.mutate({
                            id: assignedConfig.id,
                            data: { workflow: '' },
                          })
                        }
                      }}
                      className="w-[200px] rounded-md border bg-background px-3 py-1.5 text-sm"
                    >
                      <option value="">{t('modelSettings.useDefault')}</option>
                      {configs.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.model_name} ({c.provider})
                        </option>
                      ))}
                    </select>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configured Models */}
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
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {configs.map((config) => {
                const catalogModel = getModel(config.provider, config.model_name)
                const workflowLabels = WORKFLOW_OPTIONS.filter(
                  (wf) => configs.find((c) => c.workflow === wf.id)?.id === config.id,
                )
                return (
                  <div
                    key={config.id}
                    className="group relative rounded-lg border p-4 transition-colors hover:bg-muted/50"
                  >
                    {/* Provider + model */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                          <Bot className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{config.model_name}</p>
                          <p className="text-sm text-muted-foreground capitalize">
                            {config.provider}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 opacity-0 group-hover:opacity-100"
                        onClick={() => setDeleteTarget(config.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>

                    {/* Badges */}
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {config.is_default && <Badge variant="default">Default</Badge>}
                      {config.has_api_key && <Badge variant="secondary">Key set</Badge>}
                      {workflowLabels.map((wf) => (
                        <Badge key={wf.id} variant="outline">
                          {t(wf.labelKey)}
                        </Badge>
                      ))}
                    </div>

                    {/* Catalog info */}
                    {catalogModel && (
                      <div className="mt-3 grid grid-cols-3 gap-2 rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
                        <div>
                          <p className="font-medium text-foreground">
                            {formatContextWindow(catalogModel.contextWindow)}
                          </p>
                          <p>{t('modelSettings.contextWindow')}</p>
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {formatPrice(catalogModel.inputPrice)}
                          </p>
                          <p>Input/1M</p>
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {formatPrice(catalogModel.outputPrice)}
                          </p>
                          <p>Output/1M</p>
                        </div>
                      </div>
                    )}

                    {/* Set default action */}
                    {!config.is_default && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-3 w-full"
                        onClick={() => handleSetDefault(config)}
                      >
                        {t('modelSettings.setDefault')}
                      </Button>
                    )}
                  </div>
                )
              })}

              {/* Add model card */}
              <button
                onClick={openAddModal}
                className="flex min-h-[180px] flex-col items-center justify-center rounded-lg border-2 border-dashed p-4 text-muted-foreground transition-colors hover:border-primary hover:text-primary"
              >
                <Plus className="mb-2 h-8 w-8" />
                <p className="text-sm font-medium">{t('modelSettings.addModel')}</p>
              </button>
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
                <div
                  key={operation}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
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

      {/* Add Model Modal */}
      <AddModelModal />
    </div>
  )

  // --------------------------------------------------
  // Add Model Modal (3-step wizard)
  // --------------------------------------------------
  function AddModelModal() {
    const stepNumber = modalStep === 'provider' ? 1 : modalStep === 'model' ? 2 : 3
    const canProceedToConfirm = isFreeText ? customModelName.trim() !== '' : selectedModelId !== ''

    return (
      <Dialog
        open={showAddModal}
        onOpenChange={(open) => {
          if (!open) {
            setShowAddModal(false)
            resetModal()
          }
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {modalStep === 'provider' && t('modelSettings.selectProvider')}
              {modalStep === 'model' && t('modelSettings.selectModel')}
              {modalStep === 'confirm' && t('modelSettings.confirmConfig')}
            </DialogTitle>
            <DialogDescription>
              {t('modelSettings.step', { current: stepNumber, total: 3 })}
            </DialogDescription>
          </DialogHeader>

          {/* Step 1: Provider selection */}
          {modalStep === 'provider' && (
            <div className="grid grid-cols-2 gap-3 py-2">
              {MODEL_CATALOG.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => handleSelectProvider(provider.id)}
                  className="flex items-center gap-3 rounded-lg border p-4 text-left transition-colors hover:bg-muted/50 hover:border-primary"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{provider.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {provider.models.length > 0
                        ? `${provider.models.length} models`
                        : provider.freeTextModel
                          ? t('modelSettings.enterModelName')
                          : ''}
                    </p>
                  </div>
                  <ChevronRight className="ml-auto h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Model selection + API key */}
          {modalStep === 'model' && (
            <div className="space-y-4 py-2">
              {/* Model selection */}
              {isFreeText ? (
                <div>
                  <label htmlFor="custom_model" className="text-sm font-medium">
                    {selectedProvider === 'azure'
                      ? t('modelSettings.enterDeploymentName')
                      : t('modelSettings.enterModelName')}
                  </label>
                  <input
                    id="custom_model"
                    type="text"
                    value={customModelName}
                    onChange={(e) => setCustomModelName(e.target.value)}
                    placeholder={
                      selectedProvider === 'azure' ? 'my-gpt4-deployment' : 'llama3.2'
                    }
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
              ) : (
                <div>
                  <label htmlFor="model_select" className="text-sm font-medium">
                    {t('modelSettings.selectModel')}
                  </label>
                  <select
                    id="model_select"
                    value={selectedModelId}
                    onChange={(e) => setSelectedModelId(e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  >
                    <option value="">-- {t('modelSettings.selectModel')} --</option>
                    {catalogModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Model info card */}
              {selectedModelInfo && (
                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className="font-medium">{selectedModelInfo.name}</p>
                  <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">{t('modelSettings.contextWindow')}</p>
                      <p className="font-medium">
                        {formatContextWindow(selectedModelInfo.contextWindow)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">{t('modelSettings.inputPrice')}</p>
                      <p className="font-medium">
                        {formatPrice(selectedModelInfo.inputPrice)}/1M
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">{t('modelSettings.outputPrice')}</p>
                      <p className="font-medium">
                        {formatPrice(selectedModelInfo.outputPrice)}/1M
                      </p>
                    </div>
                  </div>
                  {selectedModelInfo.strengths.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {selectedModelInfo.strengths.map((s) => (
                        <Badge key={s} variant="secondary" className="text-xs">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* API Key */}
              {providerInfo?.requiresApiKey && (
                <div>
                  <label htmlFor="api_key_input" className="text-sm font-medium">
                    {t('modelSettings.apiKey')}
                  </label>
                  <input
                    id="api_key_input"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={providerInfo.apiKeyPlaceholder ?? ''}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
              )}

              {/* Advanced toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              >
                <Settings2 className="h-3.5 w-3.5" />
                {t('modelSettings.advancedSettings')}
                <ChevronRight
                  className={`h-3.5 w-3.5 transition-transform ${showAdvanced ? 'rotate-90' : ''}`}
                />
              </button>
              {showAdvanced && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="max_tokens_input" className="text-sm font-medium">
                      {t('modelSettings.maxTokens')}
                    </label>
                    <input
                      id="max_tokens_input"
                      type="number"
                      min={1}
                      max={128000}
                      value={maxTokens}
                      onChange={(e) =>
                        setMaxTokens(e.target.value === '' ? 4096 : parseInt(e.target.value, 10))
                      }
                      className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="temperature_input" className="text-sm font-medium">
                      {t('modelSettings.temperature')}
                    </label>
                    <input
                      id="temperature_input"
                      type="number"
                      min={0}
                      max={2}
                      step={0.1}
                      value={temperature}
                      onChange={(e) =>
                        setTemperature(e.target.value === '' ? 0.3 : parseFloat(e.target.value))
                      }
                      className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Confirm */}
          {modalStep === 'confirm' && (
            <div className="space-y-4 py-2">
              <div className="rounded-lg border p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Check className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{resolvedModelName}</p>
                    <p className="text-sm text-muted-foreground capitalize">{selectedProvider}</p>
                  </div>
                </div>

                {selectedModelInfo && (
                  <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">{t('modelSettings.contextWindow')}</p>
                      <p className="font-medium">
                        {formatContextWindow(selectedModelInfo.contextWindow)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">{t('modelSettings.inputPrice')}</p>
                      <p className="font-medium">
                        {formatPrice(selectedModelInfo.inputPrice)}/1M
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">{t('modelSettings.outputPrice')}</p>
                      <p className="font-medium">
                        {formatPrice(selectedModelInfo.outputPrice)}/1M
                      </p>
                    </div>
                  </div>
                )}

                <div className="mt-3 text-sm text-muted-foreground">
                  Max tokens: {maxTokens} | Temperature: {temperature}
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isDefault}
                  onChange={(e) => setIsDefault(e.target.checked)}
                  className="rounded border"
                />
                {t('modelSettings.setAsDefault')}
              </label>
            </div>
          )}

          {/* Footer with navigation */}
          <DialogFooter className="gap-2 sm:gap-0">
            {modalStep !== 'provider' && (
              <Button
                variant="outline"
                onClick={() =>
                  setModalStep(modalStep === 'confirm' ? 'model' : 'provider')
                }
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                {t('common.back')}
              </Button>
            )}
            <div className="flex-1" />
            <Button
              variant="outline"
              onClick={() => {
                setShowAddModal(false)
                resetModal()
              }}
            >
              {t('common.cancel')}
            </Button>
            {modalStep === 'model' && (
              <Button disabled={!canProceedToConfirm} onClick={() => setModalStep('confirm')}>
                {t('common.next')}
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            )}
            {modalStep === 'confirm' && (
              <Button onClick={handleCreate} isLoading={createModel.isPending}>
                {t('modelSettings.addModel')}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }
}
