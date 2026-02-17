import { useState } from 'react'
import { Check, Loader2, UsersRound } from 'lucide-react'
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

export function CreateProjectStep({
  projectId,
  onProjectCreated,
  onNext,
  onSkip,
}: CreateProjectStepProps) {
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
      const group = await projectsApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
      })
      onProjectCreated(group.id)
      setCreated(true)
    } catch {
      setError('Failed to create research group. Please try again.')
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
            <h3 className="font-semibold text-lg">Research Group Created!</h3>
            <p className="text-muted-foreground mt-1">
              Your research group &ldquo;{name}&rdquo; is ready. You can search for institutions or
              researchers later to import publications.
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
        Create a research group to track publications from an institution or researcher
      </p>

      <div className="max-w-md mx-auto space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Group name</Label>
          <Input
            id="name"
            placeholder="e.g., ML Lab @ MIT"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description (optional)</Label>
          <Input
            id="description"
            placeholder="What does this group research?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isLoading}
          />
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
              <UsersRound className="h-4 w-4 mr-2" />
              Create Research Group
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
