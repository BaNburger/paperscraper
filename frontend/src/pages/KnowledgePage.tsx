import { useState } from 'react'
import {
  usePersonalKnowledge,
  useOrganizationKnowledge,
  useCreatePersonalKnowledge,
  useUpdatePersonalKnowledge,
  useDeletePersonalKnowledge,
  useCreateOrganizationKnowledge,
  useUpdateOrganizationKnowledge,
  useDeleteOrganizationKnowledge,
} from '@/hooks'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { useToast } from '@/components/ui/Toast'
import { BookOpen, Plus, Trash2, AlertTriangle, Pencil } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { KnowledgeType, KnowledgeScope, KnowledgeSource } from '@/types'

const TYPE_LABELS: Record<KnowledgeType, string> = {
  research_focus: 'Research Focus',
  industry_context: 'Industry Context',
  evaluation_criteria: 'Evaluation Criteria',
  domain_expertise: 'Domain Expertise',
  custom: 'Custom',
}

export function KnowledgePage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [activeTab, setActiveTab] = useState<KnowledgeScope>('personal')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingSource, setEditingSource] = useState<KnowledgeSource | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; title: string; scope: KnowledgeScope } | null>(null)

  // Form state
  const [formTitle, setFormTitle] = useState('')
  const [formContent, setFormContent] = useState('')
  const [formType, setFormType] = useState<KnowledgeType>('custom')
  const [formTags, setFormTags] = useState('')

  const { data: personal, isLoading: loadingPersonal } = usePersonalKnowledge()
  const { data: organization, isLoading: loadingOrg } = useOrganizationKnowledge()
  const createPersonal = useCreatePersonalKnowledge()
  const updatePersonal = useUpdatePersonalKnowledge()
  const deletePersonal = useDeletePersonalKnowledge()
  const createOrg = useCreateOrganizationKnowledge()
  const updateOrg = useUpdateOrganizationKnowledge()
  const deleteOrg = useDeleteOrganizationKnowledge()
  const { success, error: showError } = useToast()

  const sources = activeTab === 'personal' ? personal : organization
  const isLoading = activeTab === 'personal' ? loadingPersonal : loadingOrg

  const resetForm = () => {
    setFormTitle('')
    setFormContent('')
    setFormType('custom')
    setFormTags('')
    setEditingSource(null)
  }

  const openEdit = (source: KnowledgeSource) => {
    setEditingSource(source)
    setFormTitle(source.title)
    setFormContent(source.content)
    setFormType(source.type)
    setFormTags(source.tags.join(', '))
    setShowCreateModal(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      title: formTitle,
      content: formContent,
      type: formType,
      tags: formTags ? formTags.split(',').map((t) => t.trim()).filter(Boolean) : [],
    }

    try {
      if (editingSource) {
        // Update existing
        if (editingSource.scope === 'personal') {
          await updatePersonal.mutateAsync({ id: editingSource.id, data })
        } else {
          await updateOrg.mutateAsync({ id: editingSource.id, data })
        }
        success('Updated', 'Knowledge source has been updated.')
      } else {
        // Create new
        if (activeTab === 'personal') {
          await createPersonal.mutateAsync(data)
        } else {
          await createOrg.mutateAsync(data)
        }
        success('Created', 'Knowledge source has been created.')
      }
      setShowCreateModal(false)
      resetForm()
    } catch {
      showError('Failed to save', 'Please try again.')
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      if (deleteConfirm.scope === 'personal') {
        await deletePersonal.mutateAsync(deleteConfirm.id)
      } else {
        await deleteOrg.mutateAsync(deleteConfirm.id)
      }
      success('Deleted', `"${deleteConfirm.title}" has been deleted.`)
      setDeleteConfirm(null)
    } catch {
      showError('Failed to delete', 'Please try again.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">
            Manage knowledge sources to personalize AI scoring and analysis
          </p>
        </div>
        <Button
          onClick={() => {
            resetForm()
            setShowCreateModal(true)
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Source
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b pb-1">
        <Button
          variant={activeTab === 'personal' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('personal')}
        >
          Personal
        </Button>
        {isAdmin && (
          <Button
            variant={activeTab === 'organization' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setActiveTab('organization')}
          >
            Organization
          </Button>
        )}
      </div>

      {/* Sources List */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : !sources?.items?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<BookOpen className="h-12 w-12" />}
              title={`No ${activeTab} knowledge sources`}
              description="Add knowledge sources to help the AI understand your context better."
              action={{
                label: 'Add Source',
                onClick: () => {
                  resetForm()
                  setShowCreateModal(true)
                },
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {sources.items.map((source) => (
            <Card key={source.id} className="group relative">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">{source.title}</CardTitle>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {TYPE_LABELS[source.type]}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(source.updated_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {(source.scope === 'personal' || isAdmin) && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => openEdit(source)}
                      >
                        <Pencil className="h-3 w-3" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() =>
                        setDeleteConfirm({
                          id: source.id,
                          title: source.title,
                          scope: source.scope,
                        })
                      }
                    >
                      <Trash2 className="h-3 w-3 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground line-clamp-3">{source.content}</p>
                {source.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {source.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteConfirm}
        onOpenChange={(open) => !open && setDeleteConfirm(null)}
        title="Delete Knowledge Source"
        description={`Are you sure you want to delete "${deleteConfirm?.title}"?`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deletePersonal.isPending || deleteOrg.isPending}
        icon={<AlertTriangle className="h-6 w-6 text-destructive" />}
      />

      {/* Create/Edit Dialog */}
      <Dialog
        open={showCreateModal}
        onOpenChange={(open) => {
          if (!open) resetForm()
          setShowCreateModal(open)
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingSource ? 'Edit Knowledge Source' : 'Add Knowledge Source'}
            </DialogTitle>
            <DialogDescription>
              {activeTab === 'personal'
                ? 'Personal sources customize AI analysis for you'
                : 'Organization sources are shared across your team'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="ksTitle">Title</Label>
                <Input
                  id="ksTitle"
                  placeholder="e.g., Our Research Focus Areas"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ksContent">Content</Label>
                <textarea
                  id="ksContent"
                  className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Describe the knowledge..."
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ksType">Type</Label>
                <Select value={formType} onValueChange={(v) => setFormType(v as KnowledgeType)}>
                  <SelectTrigger id="ksType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(TYPE_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ksTags">Tags (comma-separated)</Label>
                <Input
                  id="ksTags"
                  placeholder="e.g., AI, biomedicine, patents"
                  value={formTags}
                  onChange={(e) => setFormTags(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateModal(false)
                  resetForm()
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                isLoading={
                  createPersonal.isPending ||
                  updatePersonal.isPending ||
                  createOrg.isPending ||
                  updateOrg.isPending
                }
              >
                {editingSource ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
