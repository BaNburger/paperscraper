import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import {
  useProjects,
  useCreateProject,
  useDeleteProject,
  useInstitutionSearch,
  useAuthorSearch,
} from '@/hooks'
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
import { useToast } from '@/components/ui/Toast'
import {
  Plus,
  Trash2,
  AlertTriangle,
  Users,
  Building2,
  User,
  Search,
  FileText,
  Layers,
} from 'lucide-react'
import { formatDate, cn } from '@/lib/utils'
import type {
  Project,
  InstitutionSearchResult,
  AuthorSearchResult,
  CreateProject,
} from '@/types'

type SearchTab = 'institution' | 'author'

function SyncStatusBadge({ status }: { status: Project['sync_status'] }) {
  const { t } = useTranslation()

  const config: Record<
    Project['sync_status'],
    { label: string; className: string }
  > = {
    idle: {
      label: t('projects.syncStatus.idle', 'Idle'),
      className: 'bg-gray-100 text-gray-700 border-gray-200',
    },
    importing: {
      label: t('projects.syncStatus.importing', 'Importing'),
      className: 'bg-blue-100 text-blue-700 border-blue-200 animate-pulse',
    },
    clustering: {
      label: t('projects.syncStatus.clustering', 'Clustering'),
      className: 'bg-blue-100 text-blue-700 border-blue-200 animate-pulse',
    },
    ready: {
      label: t('projects.syncStatus.ready', 'Ready'),
      className: 'bg-green-100 text-green-700 border-green-200',
    },
    failed: {
      label: t('projects.syncStatus.failed', 'Failed'),
      className: 'bg-red-100 text-red-700 border-red-200',
    },
  }

  const { label, className } = config[status]

  return <Badge className={className}>{label}</Badge>
}

function ResearchGroupCard({
  group,
  onDelete,
}: {
  group: Project
  onDelete: (group: { id: string; name: string }) => void
}) {
  const { t } = useTranslation()

  return (
    <Card className="group relative">
      <Link to={`/projects/${group.id}`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="h-5 w-5 text-primary shrink-0" />
                <span className="truncate">{group.name}</span>
              </CardTitle>
              {(group.institution_name || group.pi_name) && (
                <p className="text-sm text-muted-foreground mt-1.5 flex items-center gap-1.5">
                  {group.institution_name ? (
                    <>
                      <Building2 className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">{group.institution_name}</span>
                    </>
                  ) : (
                    <>
                      <User className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">{group.pi_name}</span>
                    </>
                  )}
                </p>
              )}
            </div>
            <SyncStatusBadge status={group.sync_status} />
          </div>
        </CardHeader>
        <CardContent>
          {group.description && (
            <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
              {group.description}
            </p>
          )}
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <FileText className="h-3.5 w-3.5" />
              {t('projects.paperCount', '{{count}} papers', { count: group.paper_count })}
            </span>
            <span className="flex items-center gap-1">
              <Layers className="h-3.5 w-3.5" />
              {t('projects.clusterCount', '{{count}} clusters', { count: group.cluster_count })}
            </span>
          </div>
          {group.last_synced_at && (
            <p className="text-xs text-muted-foreground mt-2">
              {t('projects.lastSynced', 'Last synced: {{date}}', {
                date: formatDate(group.last_synced_at),
              })}
            </p>
          )}
        </CardContent>
      </Link>
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-12 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.preventDefault()
          onDelete({ id: group.id, name: group.name })
        }}
        aria-label={t('projects.deleteGroup', 'Delete research group')}
      >
        <Trash2 className="h-4 w-4 text-destructive" />
      </Button>
    </Card>
  )
}

function CreateResearchGroupDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { t } = useTranslation()
  const { success, error: showError } = useToast()
  const createGroup = useCreateProject()

  const [activeTab, setActiveTab] = useState<SearchTab>('institution')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [maxPapers, setMaxPapers] = useState(100)
  const [selectedInstitution, setSelectedInstitution] = useState<InstitutionSearchResult | null>(
    null
  )
  const [selectedAuthor, setSelectedAuthor] = useState<AuthorSearchResult | null>(null)

  // Search queries
  const { data: institutions, isLoading: isSearchingInstitutions } =
    useInstitutionSearch(activeTab === 'institution' ? debouncedQuery : '')
  const { data: authors, isLoading: isSearchingAuthors } =
    useAuthorSearch(activeTab === 'author' ? debouncedQuery : '')

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const resetForm = useCallback(() => {
    setActiveTab('institution')
    setSearchQuery('')
    setDebouncedQuery('')
    setName('')
    setDescription('')
    setMaxPapers(100)
    setSelectedInstitution(null)
    setSelectedAuthor(null)
  }, [])

  const handleOpenChange = useCallback(
    (isOpen: boolean) => {
      if (!isOpen) {
        resetForm()
      }
      onOpenChange(isOpen)
    },
    [onOpenChange, resetForm]
  )

  const handleTabChange = useCallback((tab: SearchTab) => {
    setActiveTab(tab)
    setSearchQuery('')
    setDebouncedQuery('')
    setSelectedInstitution(null)
    setSelectedAuthor(null)
    setName('')
  }, [])

  const handleSelectInstitution = useCallback((inst: InstitutionSearchResult) => {
    setSelectedInstitution(inst)
    setSelectedAuthor(null)
    setName(inst.display_name)
    setSearchQuery('')
  }, [])

  const handleSelectAuthor = useCallback((author: AuthorSearchResult) => {
    setSelectedAuthor(author)
    setSelectedInstitution(null)
    setName(author.display_name)
    setSearchQuery('')
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()

    const data: CreateProject = {
      name,
      description: description || undefined,
      max_papers: maxPapers,
    }

    if (selectedInstitution) {
      data.openalex_institution_id = selectedInstitution.openalex_id
      data.institution_name = selectedInstitution.display_name
    } else if (selectedAuthor) {
      data.openalex_author_id = selectedAuthor.openalex_id
      data.pi_name = selectedAuthor.display_name
    }

    try {
      await createGroup.mutateAsync(data)
      success(
        t('projects.createSuccess', 'Research group created'),
        t('projects.createSuccessDescription', '"{{name}}" has been created.', { name })
      )
      resetForm()
      onOpenChange(false)
    } catch {
      showError(
        t('projects.createFailed', 'Failed to create research group'),
        t('projects.tryAgain', 'Please try again.')
      )
    }
  }

  const hasSelection = selectedInstitution !== null || selectedAuthor !== null

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t('projects.createGroup', 'Create Research Group')}</DialogTitle>
          <DialogDescription>
            {t(
              'projects.createGroupDescription',
              'Search for an institution or author to track their research publications.'
            )}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleCreate}>
          <div className="space-y-4 py-2">
            {/* Tab selector */}
            <div className="flex rounded-lg border p-1 gap-1">
              <button
                type="button"
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  activeTab === 'institution'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                )}
                onClick={() => handleTabChange('institution')}
              >
                <Building2 className="h-4 w-4" />
                {t('projects.tab.institution', 'Institution')}
              </button>
              <button
                type="button"
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  activeTab === 'author'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                )}
                onClick={() => handleTabChange('author')}
              >
                <User className="h-4 w-4" />
                {t('projects.tab.author', 'Author')}
              </button>
            </div>

            {/* Search input */}
            <div className="space-y-2">
              <Label htmlFor="search">
                {activeTab === 'institution'
                  ? t('projects.searchInstitution', 'Search institution')
                  : t('projects.searchAuthor', 'Search author')}
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  className="pl-9"
                  placeholder={
                    activeTab === 'institution'
                      ? t('projects.searchInstitutionPlaceholder', 'e.g., MIT, Stanford, ETH Zurich...')
                      : t('projects.searchAuthorPlaceholder', 'e.g., John Smith, Jane Doe...')
                  }
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            {/* Search results */}
            {debouncedQuery.length >= 2 && !hasSelection && (
              <div className="max-h-48 overflow-y-auto rounded-md border divide-y">
                {activeTab === 'institution' ? (
                  isSearchingInstitutions ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                      {t('common.searching', 'Searching...')}
                    </div>
                  ) : !institutions?.length ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                      {t('projects.noInstitutionsFound', 'No institutions found')}
                    </div>
                  ) : (
                    institutions.map((inst) => (
                      <button
                        key={inst.openalex_id}
                        type="button"
                        className="w-full text-left px-3 py-2.5 hover:bg-muted/50 transition-colors"
                        onClick={() => handleSelectInstitution(inst)}
                      >
                        <div className="font-medium text-sm">{inst.display_name}</div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                          {inst.country_code && <span>{inst.country_code}</span>}
                          {inst.type && <span>{inst.type}</span>}
                          <span>
                            {t('projects.worksCount', '{{count}} works', {
                              count: inst.works_count,
                            })}
                          </span>
                        </div>
                      </button>
                    ))
                  )
                ) : isSearchingAuthors ? (
                  <div className="p-4 text-center text-sm text-muted-foreground">
                    {t('common.searching', 'Searching...')}
                  </div>
                ) : !authors?.length ? (
                  <div className="p-4 text-center text-sm text-muted-foreground">
                    {t('projects.noAuthorsFound', 'No authors found')}
                  </div>
                ) : (
                  authors.map((author) => (
                    <button
                      key={author.openalex_id}
                      type="button"
                      className="w-full text-left px-3 py-2.5 hover:bg-muted/50 transition-colors"
                      onClick={() => handleSelectAuthor(author)}
                    >
                      <div className="font-medium text-sm">{author.display_name}</div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                        {author.last_known_institution && (
                          <span>{author.last_known_institution}</span>
                        )}
                        <span>
                          {t('projects.worksCount', '{{count}} works', {
                            count: author.works_count,
                          })}
                        </span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}

            {/* Selected entity indicator */}
            {hasSelection && (
              <div className="flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2">
                {selectedInstitution ? (
                  <>
                    <Building2 className="h-4 w-4 text-primary shrink-0" />
                    <span className="text-sm font-medium truncate">
                      {selectedInstitution.display_name}
                    </span>
                    {selectedInstitution.country_code && (
                      <span className="text-xs text-muted-foreground">
                        ({selectedInstitution.country_code})
                      </span>
                    )}
                  </>
                ) : selectedAuthor ? (
                  <>
                    <User className="h-4 w-4 text-primary shrink-0" />
                    <span className="text-sm font-medium truncate">
                      {selectedAuthor.display_name}
                    </span>
                    {selectedAuthor.last_known_institution && (
                      <span className="text-xs text-muted-foreground truncate">
                        ({selectedAuthor.last_known_institution})
                      </span>
                    )}
                  </>
                ) : null}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="ml-auto h-6 px-2 text-xs"
                  onClick={() => {
                    setSelectedInstitution(null)
                    setSelectedAuthor(null)
                    setName('')
                  }}
                >
                  {t('common.change', 'Change')}
                </Button>
              </div>
            )}

            {/* Name override */}
            <div className="space-y-2">
              <Label htmlFor="name">{t('projects.groupName', 'Group name')}</Label>
              <Input
                id="name"
                placeholder={t('projects.groupNamePlaceholder', 'e.g., MIT AI Research')}
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">
                {t('projects.descriptionOptional', 'Description (optional)')}
              </Label>
              <Input
                id="description"
                placeholder={t(
                  'projects.descriptionPlaceholder',
                  'Brief description of this research group...'
                )}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            {/* Max papers slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="maxPapers">
                  {t('projects.maxPapers', 'Max papers to import')}
                </Label>
                <span className="text-sm text-muted-foreground">{maxPapers}</span>
              </div>
              <input
                id="maxPapers"
                type="range"
                min={10}
                max={500}
                step={10}
                value={maxPapers}
                onChange={(e) => setMaxPapers(Number(e.target.value))}
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>10</span>
                <span>500</span>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
            >
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button
              type="submit"
              disabled={!name.trim()}
              isLoading={createGroup.isPending}
            >
              {t('projects.createGroup', 'Create Research Group')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function ProjectsPage() {
  const { t } = useTranslation()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null)

  const { data: groups, isLoading, error } = useProjects()
  const deleteGroup = useDeleteProject()
  const { success, error: showError } = useToast()

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      await deleteGroup.mutateAsync(deleteConfirm.id)
      success(
        t('projects.deleteSuccess', 'Research group deleted'),
        t('projects.deleteSuccessDescription', '"{{name}}" has been deleted.', {
          name: deleteConfirm.name,
        })
      )
      setDeleteConfirm(null)
    } catch {
      showError(
        t('projects.deleteFailed', 'Failed to delete research group'),
        t('projects.tryAgain', 'Please try again.')
      )
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {t('projects.title', 'Research Groups')}
          </h1>
          <p className="text-muted-foreground mt-1">
            {t(
              'projects.subtitle',
              'Discover and track research groups and their publications'
            )}
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('projects.newGroup', 'New Research Group')}
        </Button>
      </div>

      {/* Research Groups Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            {t('projects.loadFailed', 'Failed to load research groups. Please try again.')}
          </CardContent>
        </Card>
      ) : !groups?.items?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<Users className="h-16 w-16" />}
              title={t('projects.noGroups', 'No research groups yet')}
              description={t(
                'projects.noGroupsDescription',
                'Create a research group to start tracking publications from institutions or authors.'
              )}
              action={{
                label: t('projects.createFirstGroup', 'Create Research Group'),
                onClick: () => setShowCreateModal(true),
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {groups.items.map((group) => (
            <ResearchGroupCard
              key={group.id}
              group={group}
              onDelete={setDeleteConfirm}
            />
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!deleteConfirm}
        onOpenChange={(open) => !open && setDeleteConfirm(null)}
        title={t('projects.deleteGroup', 'Delete Research Group')}
        description={t(
          'projects.deleteConfirm',
          'Are you sure you want to delete "{{name}}"? All imported papers and clusters will be removed. This action cannot be undone.',
          { name: deleteConfirm?.name }
        )}
        confirmLabel={t('common.delete', 'Delete')}
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteGroup.isPending}
        icon={<AlertTriangle className="h-6 w-6 text-destructive" />}
      />

      {/* Create Research Group Dialog */}
      <CreateResearchGroupDialog
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
      />
    </div>
  )
}
