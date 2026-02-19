import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import DOMPurify from 'dompurify'
import { useParams, useNavigate } from 'react-router-dom'
import {
  useConversation,
  useChangeStage,
  useSendMessage,
  useNextSteps,
  useMessageTemplates,
} from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Textarea } from '@/components/ui/Textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { useToast } from '@/components/ui/Toast'
import {
  ArrowLeft,
  Send,
  Lightbulb,
  Clock,
  FileText,
  ChevronRight,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { TransferStage } from '@/types'

const STAGE_KEYS: Record<TransferStage, string> = {
  initial_contact: 'transfer.stageInitialContact',
  discovery: 'transfer.stageDiscovery',
  evaluation: 'transfer.stageEvaluation',
  negotiation: 'transfer.stageNegotiation',
  closed_won: 'transfer.stageClosedWon',
  closed_lost: 'transfer.stageClosedLost',
}

const STAGE_ORDER: TransferStage[] = [
  'initial_contact',
  'discovery',
  'evaluation',
  'negotiation',
  'closed_won',
]

const STAGE_COLORS: Record<TransferStage, string> = {
  initial_contact: 'bg-gray-100 text-gray-800',
  discovery: 'bg-blue-100 text-blue-800',
  evaluation: 'bg-yellow-100 text-yellow-800',
  negotiation: 'bg-orange-100 text-orange-800',
  closed_won: 'bg-green-100 text-green-800',
  closed_lost: 'bg-red-100 text-red-800',
}

export function TransferDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [messageContent, setMessageContent] = useState('')
  const [stageNotes, setStageNotes] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('')

  const { data: conversation, isLoading } = useConversation(id || '')
  const { data: nextSteps } = useNextSteps(id || '')
  const { data: templates } = useMessageTemplates(conversation?.stage)
  const changeStage = useChangeStage()
  const sendMessage = useSendMessage()
  const { success, error: showError } = useToast()

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t('transfer.notFound')}
      </div>
    )
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!messageContent.trim() || !id) return
    try {
      await sendMessage.mutateAsync({
        conversationId: id,
        content: messageContent,
      })
      setMessageContent('')
    } catch {
      showError(t('transfer.sendFailed'), t('transfer.tryAgain'))
    }
  }

  const handleStageChange = async (newStage: string) => {
    if (!id) return
    try {
      await changeStage.mutateAsync({
        id,
        stage: newStage,
        notes: stageNotes || undefined,
      })
      setStageNotes('')
      success(t('transfer.stageUpdated'), t('transfer.movedToStage', { stage: t(STAGE_KEYS[newStage as TransferStage]) }))
    } catch {
      showError(t('transfer.stageChangeFailed'), t('transfer.tryAgain'))
    }
  }

  const handleTemplateSelect = (templateId: string) => {
    const template = templates?.find((t) => t.id === templateId)
    if (template) {
      setMessageContent(template.content)
    }
    setSelectedTemplate('')
  }

  const currentStageIndex = STAGE_ORDER.indexOf(conversation.stage)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate('/transfer')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{conversation.title}</h1>
          <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
            {conversation.paper_title && (
              <span>{t('transfer.paper')}: {conversation.paper_title}</span>
            )}
            {conversation.researcher_name && (
              <span>{t('transfer.researcher')}: {conversation.researcher_name}</span>
            )}
          </div>
        </div>
        <span className={`text-sm px-3 py-1 rounded-full ${STAGE_COLORS[conversation.stage]}`}>
          {t(STAGE_KEYS[conversation.stage])}
        </span>
      </div>

      {/* Stage Pipeline */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center gap-1">
            {STAGE_ORDER.map((stage, i) => {
              const isActive = stage === conversation.stage
              const isPast = i < currentStageIndex
              return (
                <div key={stage} className="flex items-center flex-1">
                  <div
                    className={`flex-1 h-2 rounded-full ${
                      isPast || isActive
                        ? 'bg-primary'
                        : 'bg-muted'
                    }`}
                  />
                  {i < STAGE_ORDER.length - 1 && (
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                </div>
              )
            })}
          </div>
          <div className="flex justify-between mt-2">
            {STAGE_ORDER.map((stage) => (
              <span
                key={stage}
                className={`text-xs ${
                  stage === conversation.stage ? 'font-semibold text-primary' : 'text-muted-foreground'
                }`}
              >
                {t(STAGE_KEYS[stage])}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Messages */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t('transfer.messages')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-[500px] overflow-y-auto mb-4">
                {conversation.messages.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    {t('transfer.noMessages')}
                  </p>
                ) : (
                  conversation.messages.map((msg) => (
                    <div key={msg.id} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">
                          {msg.sender_name || 'Unknown'}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(msg.created_at)}
                        </span>
                      </div>
                      <p
                        className="text-sm whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(msg.content, { ALLOWED_TAGS: [] }),
                        }}
                      />
                    </div>
                  ))
                )}
              </div>

              {/* Message Input */}
              <form onSubmit={handleSendMessage}>
                <div className="flex gap-2 mb-2">
                  {templates && templates.length > 0 && (
                    <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder={t('transfer.useTemplate')} />
                      </SelectTrigger>
                      <SelectContent>
                        {templates.map((t) => (
                          <SelectItem key={t.id} value={t.id}>
                            {t.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
                <div className="flex gap-2">
                  <Textarea
                    className="flex-1 min-h-[80px] resize-none"
                    placeholder={t('transfer.messagePlaceholder')}
                    value={messageContent}
                    onChange={(e) => setMessageContent(e.target.value)}
                  />
                  <Button
                    type="submit"
                    size="icon"
                    className="self-end"
                    disabled={!messageContent.trim()}
                    isLoading={sendMessage.isPending}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Resources */}
          {conversation.resources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{t('transfer.resources')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {conversation.resources.map((res) => (
                    <div
                      key={res.id}
                      className="flex items-center gap-3 p-2 rounded border"
                    >
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{res.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {res.resource_type} - {formatDate(res.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Stage Change */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t('transfer.changeStage')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                placeholder={t('transfer.stageNotesPlaceholder')}
                value={stageNotes}
                onChange={(e) => setStageNotes(e.target.value)}
              />
              <Select onValueChange={handleStageChange} value="">
                <SelectTrigger>
                  <SelectValue placeholder={t('transfer.moveTo')} />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(STAGE_KEYS)
                    .filter(([key]) => key !== conversation.stage)
                    .map(([value, key]) => (
                      <SelectItem key={value} value={value}>
                        {t(key)}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* AI Next Steps */}
          {nextSteps && nextSteps.steps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-yellow-500" />
                  {t('transfer.suggestedNextSteps')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">{nextSteps.summary}</p>
                <div className="space-y-2">
                  {nextSteps.steps.map((step, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant={
                            step.priority === 'high'
                              ? 'destructive'
                              : step.priority === 'medium'
                                ? 'default'
                                : 'secondary'
                          }
                          className="text-xs"
                        >
                          {step.priority}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium">{step.action}</p>
                      <p className="text-xs text-muted-foreground mt-1">{step.rationale}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Stage History */}
          {conversation.stage_history.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {t('transfer.stageHistory')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {conversation.stage_history.map((change) => (
                    <div key={change.id} className="text-sm border-l-2 pl-3 border-muted">
                      <p className="font-medium">
                        {t(STAGE_KEYS[change.from_stage])} → {t(STAGE_KEYS[change.to_stage])}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {change.changed_by_name || 'System'} - {formatDate(change.changed_at)}
                      </p>
                      {change.notes && (
                        <p className="text-xs mt-1">{change.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
