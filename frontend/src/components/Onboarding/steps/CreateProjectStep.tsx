import { useState } from 'react'
import { Check, Loader2, FolderKanban } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { projectsApi } from '@/lib/api'

interface CreateProjectStepProps {
  projectId: string | null
  onProjectCreated: (id: string) => void
  onNext: () => void
  onSkip: () => void
}

const defaultStages = [
  { id: 'inbox', name: 'Inbox', color: '#6B7280', order: 0 },
  { id: 'review', name: 'Under Review', color: '#3B82F6', order: 1 },
  { id: 'shortlist', name: 'Shortlisted', color: '#10B981', order: 2 },
  { id: 'rejected', name: 'Rejected', color: '#EF4444', order: 3 },
]

export const CreateProjectStep = ({
  projectId,
  onProjectCreated,
  onNext,
  onSkip,
}: CreateProjectStepProps) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState(false)

  const handleCreate = async () => {
    if (!name.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const project = await projectsApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        stages: defaultStages,
      })
      onProjectCreated(project.id)
      setCreated(true)
    } catch (err) {
      setError('Failed to create project. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  if (created || projectId) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <div className="text-center">
            <h3 className="font-semibold text-lg">Project Created!</h3>
            <p className="text-muted-foreground mt-1">
              Your project "{name}" is ready with a KanBan pipeline
            </p>
          </div>
        </div>

        <div className="flex justify-center gap-4 pt-4">
          <Button onClick={onNext}>Continue</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-center text-muted-foreground">
        Create a project to organize papers in a KanBan-style pipeline
      </p>

      <div className="max-w-md mx-auto space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Project name</Label>
          <Input
            id="name"
            placeholder="e.g., Q1 2026 Deep Tech Scout"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description (optional)</Label>
          <Input
            id="description"
            placeholder="What is this project for?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isLoading}
          />
        </div>

        {/* Pipeline Preview */}
        <div className="space-y-2">
          <Label>Pipeline stages</Label>
          <div className="flex gap-2 flex-wrap">
            {defaultStages.map((stage) => (
              <div
                key={stage.id}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm bg-muted"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: stage.color }}
                />
                {stage.name}
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            You can customize stages later in project settings
          </p>
        </div>

        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</div>
        )}
      </div>

      <div className="flex justify-center gap-4 pt-4">
        <Button variant="outline" onClick={onSkip}>
          Skip for now
        </Button>
        <Button onClick={handleCreate} disabled={!name.trim() || isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Creating...
            </>
          ) : (
            <>
              <FolderKanban className="h-4 w-4 mr-2" />
              Create Project
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
