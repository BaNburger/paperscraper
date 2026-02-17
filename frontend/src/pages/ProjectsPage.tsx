import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useProjects, useCreateProject, useDeleteProject, useConversations } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
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
import { useToast } from '@/components/ui/Toast'
import { FolderKanban, Plus, Trash2, AlertTriangle, ArrowRightLeft } from 'lucide-react'
import { WorkflowBanner } from '@/components/workflow/WorkflowBanner'
import { formatDate } from '@/lib/utils'

export function ProjectsPage() {
  const { t } = useTranslation()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null)

  const { data: projects, isLoading, error } = useProjects()
  const { data: conversationsData } = useConversations({ page: 1, page_size: 1 })
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const { success, error: showError } = useToast()

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createProject.mutateAsync({
        name: newProjectName,
        description: newProjectDescription || undefined,
      })
      setNewProjectName('')
      setNewProjectDescription('')
      setShowCreateModal(false)
      success(t('projects.createSuccess'), t('projects.createSuccessDescription', { name: newProjectName }))
    } catch {
      showError(t('projects.createFailed'), t('projects.tryAgain'))
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      await deleteProject.mutateAsync(deleteConfirm.id)
      success(t('projects.deleteSuccess'), t('projects.deleteSuccessDescription', { name: deleteConfirm.name }))
      setDeleteConfirm(null)
    } catch {
      showError(t('projects.deleteFailed'), t('projects.tryAgain'))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('projects.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('projects.subtitle')}
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('projects.newProject')}
        </Button>
      </div>

      {/* Workflow banner: projects -> transfer */}
      <WorkflowBanner
        bannerId="projects-to-transfer"
        icon={ArrowRightLeft}
        message={t('workflow.banner.readyToTransfer', 'Your projects are set up. Start a transfer conversation to begin outreach.')}
        ctaLabel={t('workflow.banner.readyToTransferCta', 'Start Transfer')}
        ctaPath="/transfer"
        condition={(projects?.total ?? 0) > 0 && (conversationsData?.total ?? 0) === 0}
        variant="purple"
      />

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            {t('projects.loadFailed')}
          </CardContent>
        </Card>
      ) : !projects?.items?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<FolderKanban className="h-16 w-16" />}
              title={t('projects.noProjects')}
              description={t('projects.noProjectsDescription')}
              action={{
                label: t('projects.createProject'),
                onClick: () => setShowCreateModal(true),
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects?.items?.map((project) => (
            <Card key={project.id} className="group relative">
              <Link to={`/projects/${project.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <FolderKanban className="h-5 w-5 text-primary" />
                        {project.name}
                      </CardTitle>
                      {project.description && (
                        <CardDescription className="mt-2 line-clamp-2">
                          {project.description}
                        </CardDescription>
                      )}
                    </div>
                    <Badge variant={project.is_active ? 'default' : 'secondary'}>
                      {project.is_active ? t('projects.active') : t('projects.inactive')}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{t('projects.stageCount', { count: project.stages.length })}</span>
                    <span>{t('projects.created', { date: formatDate(project.created_at) })}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {project.stages.slice(0, 4).map((stage) => (
                      <Badge
                        key={stage.id}
                        variant="outline"
                        className="text-xs"
                        style={{ borderColor: stage.color, color: stage.color }}
                      >
                        {stage.name}
                      </Badge>
                    ))}
                    {project.stages.length > 4 && (
                      <Badge variant="outline" className="text-xs">
                        {t('projects.moreStages', { count: project.stages.length - 4 })}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => {
                  e.preventDefault()
                  setDeleteConfirm({ id: project.id, name: project.name })
                }}
                aria-label={t('projects.deleteProject')}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!deleteConfirm}
        onOpenChange={(open) => !open && setDeleteConfirm(null)}
        title={t('projects.deleteProject')}
        description={t('projects.deleteConfirm', { name: deleteConfirm?.name })}
        confirmLabel={t('common.delete')}
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteProject.isPending}
        icon={<AlertTriangle className="h-6 w-6 text-destructive" />}
      />

      {/* Create Project Dialog */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('projects.createProject')}</DialogTitle>
            <DialogDescription>
              {t('projects.createDescription')}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">{t('projects.projectName')}</Label>
                <Input
                  id="name"
                  placeholder="e.g., Q1 2026 Review"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">{t('projects.descriptionOptional')}</Label>
                <Input
                  id="description"
                  placeholder={t('projects.descriptionPlaceholder')}
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateModal(false)}
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit" isLoading={createProject.isPending}>
                {t('projects.createProject')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
