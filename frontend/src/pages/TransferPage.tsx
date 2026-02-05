import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useConversations, useCreateConversation } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { useToast } from '@/components/ui/Toast'
import { ArrowRightLeft, Plus, MessageSquare, Paperclip } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { TransferType, TransferStage } from '@/types'

const STAGE_LABELS: Record<TransferStage, string> = {
  initial_contact: 'Initial Contact',
  discovery: 'Discovery',
  evaluation: 'Evaluation',
  negotiation: 'Negotiation',
  closed_won: 'Closed Won',
  closed_lost: 'Closed Lost',
}

const STAGE_COLORS: Record<TransferStage, string> = {
  initial_contact: 'bg-gray-100 text-gray-800',
  discovery: 'bg-blue-100 text-blue-800',
  evaluation: 'bg-yellow-100 text-yellow-800',
  negotiation: 'bg-orange-100 text-orange-800',
  closed_won: 'bg-green-100 text-green-800',
  closed_lost: 'bg-red-100 text-red-800',
}

const TYPE_LABELS: Record<TransferType, string> = {
  patent: 'Patent',
  licensing: 'Licensing',
  startup: 'Startup',
  partnership: 'Partnership',
  other: 'Other',
}

export function TransferPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [stageFilter, setStageFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')

  // Form state
  const [newTitle, setNewTitle] = useState('')
  const [newType, setNewType] = useState<TransferType>('licensing')

  const { data: conversations, isLoading, error } = useConversations({
    stage: stageFilter || undefined,
    search: searchQuery || undefined,
  })
  const createConversation = useCreateConversation()
  const { success, error: showError } = useToast()

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createConversation.mutateAsync({
        title: newTitle,
        type: newType,
      })
      setNewTitle('')
      setNewType('licensing')
      setShowCreateModal(false)
      success('Conversation created', `"${newTitle}" has been created.`)
    } catch {
      showError('Failed to create conversation', 'Please try again.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Technology Transfer</h1>
          <p className="text-muted-foreground mt-1">
            Manage transfer conversations with researchers and industry partners
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Conversation
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <Input
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <Select value={stageFilter} onValueChange={setStageFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All stages" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All stages</SelectItem>
            {Object.entries(STAGE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Conversations List */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            Failed to load conversations. Please try again.
          </CardContent>
        </Card>
      ) : !conversations?.items?.length ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={<ArrowRightLeft className="h-16 w-16" />}
              title="No conversations yet"
              description="Start a technology transfer conversation to track outreach with researchers."
              action={{
                label: 'New Conversation',
                onClick: () => setShowCreateModal(true),
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {conversations.items.map((conv) => (
            <Link key={conv.id} to={`/transfer/${conv.id}`}>
              <Card className="hover:border-primary transition-colors h-full">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base line-clamp-2">{conv.title}</CardTitle>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${
                        STAGE_COLORS[conv.stage]
                      }`}
                    >
                      {STAGE_LABELS[conv.stage]}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      {TYPE_LABELS[conv.type]}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      {conv.message_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <Paperclip className="h-3 w-3" />
                      {conv.resource_count}
                    </span>
                    <span className="ml-auto">{formatDate(conv.updated_at)}</span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Conversation</DialogTitle>
            <DialogDescription>
              Start a new technology transfer conversation
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="convTitle">Title</Label>
                <Input
                  id="convTitle"
                  placeholder="e.g., Patent discussion - Novel AI method"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="convType">Transfer Type</Label>
                <Select value={newType} onValueChange={(v) => setNewType(v as TransferType)}>
                  <SelectTrigger id="convType">
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
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={createConversation.isPending}>
                Create
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
