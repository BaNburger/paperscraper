export interface ModelInfo {
  id: string
  name: string
  contextWindow: number
  inputPrice: number   // per 1M tokens USD
  outputPrice: number  // per 1M tokens USD
  strengths: string[]
}

export interface ProviderInfo {
  id: string
  name: string
  icon?: string
  models: ModelInfo[]
  requiresApiKey: boolean
  apiKeyPlaceholder?: string
  freeTextModel?: boolean // Azure/Ollama: user types model name
}

export const MODEL_CATALOG: ProviderInfo[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    requiresApiKey: true,
    apiKeyPlaceholder: 'sk-...',
    models: [
      {
        id: 'gpt-5-mini',
        name: 'GPT-5 Mini',
        contextWindow: 128_000,
        inputPrice: 0.15,
        outputPrice: 0.60,
        strengths: ['Fast', 'Cost-effective'],
      },
      {
        id: 'gpt-4o',
        name: 'GPT-4o',
        contextWindow: 128_000,
        inputPrice: 2.50,
        outputPrice: 10.00,
        strengths: ['Most capable', 'Multimodal'],
      },
      {
        id: 'gpt-4o-mini',
        name: 'GPT-4o Mini',
        contextWindow: 128_000,
        inputPrice: 0.15,
        outputPrice: 0.60,
        strengths: ['Balanced', 'Fast'],
      },
    ],
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    requiresApiKey: true,
    apiKeyPlaceholder: 'sk-ant-...',
    models: [
      {
        id: 'claude-sonnet-4-20250514',
        name: 'Claude Sonnet 4',
        contextWindow: 200_000,
        inputPrice: 3.00,
        outputPrice: 15.00,
        strengths: ['Analytical', 'Long context'],
      },
      {
        id: 'claude-3-haiku',
        name: 'Claude 3 Haiku',
        contextWindow: 200_000,
        inputPrice: 0.25,
        outputPrice: 1.25,
        strengths: ['Fast', 'Affordable'],
      },
    ],
  },
  {
    id: 'google',
    name: 'Google',
    requiresApiKey: true,
    apiKeyPlaceholder: 'AIza...',
    models: [
      {
        id: 'gemini-2.0-flash',
        name: 'Gemini 2.0 Flash',
        contextWindow: 1_048_576,
        inputPrice: 0.10,
        outputPrice: 0.40,
        strengths: ['Very fast', 'Huge context'],
      },
      {
        id: 'gemini-2.0-pro',
        name: 'Gemini 2.0 Pro',
        contextWindow: 2_097_152,
        inputPrice: 1.25,
        outputPrice: 5.00,
        strengths: ['Most capable', '2M context'],
      },
    ],
  },
  {
    id: 'azure',
    name: 'Azure OpenAI',
    requiresApiKey: true,
    apiKeyPlaceholder: 'Azure API key...',
    freeTextModel: true,
    models: [],
  },
  {
    id: 'ollama',
    name: 'Ollama (Self-hosted)',
    requiresApiKey: false,
    freeTextModel: true,
    models: [],
  },
]

export function getProvider(providerId: string): ProviderInfo | undefined {
  return MODEL_CATALOG.find((p) => p.id === providerId)
}

export function getModel(providerId: string, modelId: string): ModelInfo | undefined {
  return getProvider(providerId)?.models.find((m) => m.id === modelId)
}

export function getModelsForProvider(providerId: string): ModelInfo[] {
  return getProvider(providerId)?.models ?? []
}

export function formatContextWindow(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  return `${(tokens / 1_000).toFixed(0)}K`
}

export function formatPrice(pricePerMillion: number): string {
  return `$${pricePerMillion.toFixed(2)}`
}

export const WORKFLOW_OPTIONS = [
  { id: 'scoring', labelKey: 'modelSettings.workflowScoring', descKey: 'modelSettings.workflowScoringDescription' },
  { id: 'summary', labelKey: 'modelSettings.workflowSummary', descKey: 'modelSettings.workflowSummaryDescription' },
  { id: 'classification', labelKey: 'modelSettings.workflowClassification', descKey: 'modelSettings.workflowClassificationDescription' },
  { id: 'embedding', labelKey: 'modelSettings.workflowEmbedding', descKey: 'modelSettings.workflowEmbeddingDescription' },
] as const
