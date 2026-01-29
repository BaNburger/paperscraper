import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useProjects, useCreateProject, useDeleteProject } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import { FolderKanban, Plus, Loader2, Trash2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export function ProjectsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')

  const { data: projects, isLoading, error } = useProjects()
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()

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
    } catch (err) {
      // Error handled by mutation
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete "${name}"?`)) {
      try {
        await deleteProject.mutateAsync(id)
      } catch (err) {
        // Error handled by mutation
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Projects</h1>
          <p className="text-muted-foreground mt-1">
            Organize papers into research pipelines
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            Failed to load projects. Please try again.
          </CardContent>
        </Card>
      ) : projects?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FolderKanban className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">No projects yet</h3>
            <p className="text-muted-foreground text-sm mt-1">
              Create a project to start organizing your papers
            </p>
            <Button onClick={() => setShowCreateModal(true)} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              Create Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects?.map((project) => (
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
                      {project.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{project.stages.length} stages</span>
                    <span>Created {formatDate(project.created_at)}</span>
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
                        +{project.stages.length - 4} more
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
                  handleDelete(project.id, project.name)
                }}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Create Project</CardTitle>
              <CardDescription>
                Projects help you organize papers through a review pipeline
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreate}>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="name">Project Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Q1 2026 Review"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description (optional)</Label>
                  <Input
                    id="description"
                    placeholder="What is this project for?"
                    value={newProjectDescription}
                    onChange={(e) => setNewProjectDescription(e.target.value)}
                  />
                </div>
              </CardContent>
              <div className="flex justify-end gap-2 p-6 pt-0">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" isLoading={createProject.isPending}>
                  Create Project
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
