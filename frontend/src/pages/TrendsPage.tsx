import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useTrendTopics, useCreateTrendTopic } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Textarea } from '@/components/ui/Textarea'
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
import { Plus, TrendingUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const DEFAULT_TOPIC_COLOR = '#6366f1'

export function TrendsPage() {
  const { t } = useTranslation()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newColor, setNewColor] = useState(DEFAULT_TOPIC_COLOR)

  const { data: topics, isLoading, error } = useTrendTopics()
  const createTopic = useCreateTrendTopic()
  const { success, error: showError } = useToast()

  const resetForm = () => {
    setNewName('')
    setNewDescription('')
    setNewColor(DEFAULT_TOPIC_COLOR)
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createTopic.mutateAsync({
        name: newName,
        description: newDescription,
        color: newColor || undefined,
      })
      resetForm()
      setShowCreateDialog(false)
      success(
        t('trends.createSuccess'),
        t('trends.createSuccessDescription', { name: newName })
      )
    } catch {
      showError(t('trends.createFailed'), t('trends.tryAgain'))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('trends.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('trends.subtitle')}
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('trends.newTopic')}
        </Button>
      </div>

      {/* Topics Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            {t('trends.loadFailed')}
          </CardContent>
        </Card>
      ) : !topics?.items?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<TrendingUp className="h-16 w-16" />}
              title={t('trends.noTopics')}
              description={t('trends.noTopicsDescription')}
              action={{
                label: t('trends.newTopic'),
                onClick: () => setShowCreateDialog(true),
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {topics.items.map((topic) => (
            <Link key={topic.id} to={`/trends/${topic.id}`} className="block">
              <Card className="h-full transition-colors hover:border-primary">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <span
                        className="inline-block h-3 w-3 rounded-full shrink-0"
                        style={{ backgroundColor: topic.color || DEFAULT_TOPIC_COLOR }}
                        aria-hidden="true"
                      />
                      {topic.name}
                    </CardTitle>
                    {!topic.is_active && (
                      <Badge variant="secondary">
                        {t('trends.inactive')}
                      </Badge>
                    )}
                  </div>
                  {topic.description && (
                    <CardDescription className="line-clamp-2">
                      {topic.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>
                      {t('trends.papersCount', { count: topic.matched_papers_count })}
                    </span>
                    <span>
                      {t('trends.patentsCount', { count: topic.patent_count })}
                    </span>
                    <span>
                      {t('trends.avgScore', {
                        score: topic.avg_overall_score != null
                          ? topic.avg_overall_score.toFixed(1)
                          : '—',
                      })}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">
                    {topic.last_analyzed_at
                      ? t('trends.lastAnalyzed', {
                          time: formatDistanceToNow(new Date(topic.last_analyzed_at), {
                            addSuffix: true,
                          }),
                        })
                      : t('trends.neverAnalyzed')}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Create Trend Topic Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('trends.createTopic')}</DialogTitle>
            <DialogDescription>
              {t('trends.createDescription')}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="topicName">{t('trends.topicName')}</Label>
                <Input
                  id="topicName"
                  placeholder={t('trends.topicNamePlaceholder')}
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="topicDescription">
                  {t('trends.semanticDescription')}
                </Label>
                <Textarea
                  id="topicDescription"
                  className="min-h-[100px] resize-none"
                  placeholder={t('trends.semanticDescriptionPlaceholder')}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  {t('trends.semanticDescriptionHint')}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="topicColor">{t('trends.color')}</Label>
                <div className="flex items-center gap-3">
                  <div
                    className="h-10 w-10 rounded-md border border-input shrink-0"
                    style={{ backgroundColor: newColor }}
                    aria-hidden="true"
                  />
                  <Input
                    id="topicColor"
                    type="text"
                    placeholder="#6366f1"
                    value={newColor}
                    onChange={(e) => setNewColor(e.target.value)}
                    pattern="^#[0-9a-fA-F]{6}$"
                    title={t('trends.colorFormatHint')}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit" isLoading={createTopic.isPending}>
                {t('trends.createTopic')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
