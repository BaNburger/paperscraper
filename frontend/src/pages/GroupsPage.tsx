import { useState } from 'react'
import { useGroups, useCreateGroup, useDeleteGroup, useGroup, useRemoveMember } from '@/hooks'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { Users, Plus, Trash2, AlertTriangle, UserMinus, Download } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { groupsApi } from '@/lib/api'
import { exportApi } from '@/lib/api'
import type { GroupType } from '@/types'

const GROUP_TYPE_LABELS: Record<GroupType, string> = {
  custom: 'Custom',
  mailing_list: 'Mailing List',
  speaker_pool: 'Speaker Pool',
}

const GROUP_TYPE_COLORS: Record<GroupType, string> = {
  custom: 'bg-blue-100 text-blue-800',
  mailing_list: 'bg-green-100 text-green-800',
  speaker_pool: 'bg-purple-100 text-purple-800',
}

export function GroupsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null)
  const [removeMemberConfirm, setRemoveMemberConfirm] = useState<{
    groupId: string
    researcherId: string
    name: string
  } | null>(null)

  // Form state
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newType, setNewType] = useState<GroupType>('custom')
  const [newKeywords, setNewKeywords] = useState('')

  const { data: groups, isLoading, error } = useGroups()
  const { data: selectedGroup } = useGroup(selectedGroupId || '')
  const createGroup = useCreateGroup()
  const deleteGroup = useDeleteGroup()
  const removeMember = useRemoveMember()
  const { success, error: showError } = useToast()

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createGroup.mutateAsync({
        name: newName,
        description: newDescription || undefined,
        type: newType,
        keywords: newKeywords ? newKeywords.split(',').map((k) => k.trim()).filter(Boolean) : [],
      })
      setNewName('')
      setNewDescription('')
      setNewType('custom')
      setNewKeywords('')
      setShowCreateModal(false)
      success('Group created', `"${newName}" has been created successfully.`)
    } catch {
      showError('Failed to create group', 'Please try again.')
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      await deleteGroup.mutateAsync(deleteConfirm.id)
      if (selectedGroupId === deleteConfirm.id) setSelectedGroupId(null)
      success('Group deleted', `"${deleteConfirm.name}" has been deleted.`)
      setDeleteConfirm(null)
    } catch {
      showError('Failed to delete group', 'Please try again.')
    }
  }

  const handleRemoveMember = async () => {
    if (!removeMemberConfirm) return
    try {
      await removeMember.mutateAsync({
        groupId: removeMemberConfirm.groupId,
        researcherId: removeMemberConfirm.researcherId,
      })
      success('Member removed', `${removeMemberConfirm.name} has been removed from the group.`)
      setRemoveMemberConfirm(null)
    } catch {
      showError('Failed to remove member', 'Please try again.')
    }
  }

  const handleExportCsv = async (groupId: string, groupName: string) => {
    try {
      const blob = await groupsApi.exportCsv(groupId)
      const safeFilename = groupName.replace(/[^a-z0-9_-]/gi, '_')
      exportApi.downloadFile(blob, `${safeFilename}-members.csv`)
      success('Export complete', 'Group members exported as CSV.')
    } catch {
      showError('Export failed', 'Please try again.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Researcher Groups</h1>
          <p className="text-muted-foreground mt-1">
            Organize researchers into groups for outreach and collaboration
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Group
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Groups List */}
        <div className="lg:col-span-1 space-y-4">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          ) : error ? (
            <Card>
              <CardContent className="py-8 text-center text-destructive">
                Failed to load groups.
              </CardContent>
            </Card>
          ) : !groups?.items?.length ? (
            <Card>
              <CardContent>
                <EmptyState
                  icon={<Users className="h-12 w-12" />}
                  title="No groups yet"
                  description="Create a group to organize researchers."
                  action={{
                    label: 'Create Group',
                    onClick: () => setShowCreateModal(true),
                  }}
                />
              </CardContent>
            </Card>
          ) : (
            groups.items.map((group) => (
              <Card
                key={group.id}
                className={`cursor-pointer transition-colors hover:border-primary ${
                  selectedGroupId === group.id ? 'border-primary bg-accent/50' : ''
                }`}
                onClick={() => setSelectedGroupId(group.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{group.name}</CardTitle>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${GROUP_TYPE_COLORS[group.type]}`}>
                      {GROUP_TYPE_LABELS[group.type]}
                    </span>
                  </div>
                  {group.description && (
                    <CardDescription className="line-clamp-2">{group.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{group.member_count} members</span>
                    <span>{formatDate(group.created_at)}</span>
                  </div>
                  {group.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {group.keywords.slice(0, 3).map((kw) => (
                        <Badge key={kw} variant="outline" className="text-xs">
                          {kw}
                        </Badge>
                      ))}
                      {group.keywords.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{group.keywords.length - 3}
                        </Badge>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Group Detail */}
        <div className="lg:col-span-2">
          {selectedGroup ? (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-xl">{selectedGroup.name}</CardTitle>
                    {selectedGroup.description && (
                      <CardDescription className="mt-1">{selectedGroup.description}</CardDescription>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExportCsv(selectedGroup.id, selectedGroup.name)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Export CSV
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setDeleteConfirm({ id: selectedGroup.id, name: selectedGroup.name })
                      }
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <h3 className="font-semibold mb-3">
                  Members ({selectedGroup.members.length})
                </h3>
                {selectedGroup.members.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No members yet.</p>
                ) : (
                  <div className="space-y-2">
                    {selectedGroup.members.map((member) => (
                      <div
                        key={member.researcher_id}
                        className="flex items-center justify-between p-3 rounded-lg border"
                      >
                        <div>
                          <p className="font-medium text-sm">{member.researcher_name}</p>
                          <div className="flex gap-3 text-xs text-muted-foreground mt-0.5">
                            {member.researcher_email && <span>{member.researcher_email}</span>}
                            {member.h_index != null && <span>h-index: {member.h_index}</span>}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            setRemoveMemberConfirm({
                              groupId: selectedGroup.id,
                              researcherId: member.researcher_id,
                              name: member.researcher_name,
                            })
                          }
                        >
                          <UserMinus className="h-4 w-4 text-muted-foreground" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Select a group to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteConfirm}
        onOpenChange={(open) => !open && setDeleteConfirm(null)}
        title="Delete Group"
        description={`Are you sure you want to delete "${deleteConfirm?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteGroup.isPending}
        icon={<AlertTriangle className="h-6 w-6 text-destructive" />}
      />

      {/* Remove Member Confirmation */}
      <ConfirmDialog
        open={!!removeMemberConfirm}
        onOpenChange={(open) => !open && setRemoveMemberConfirm(null)}
        title="Remove Member"
        description={`Remove ${removeMemberConfirm?.name} from this group?`}
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleRemoveMember}
        isLoading={removeMember.isPending}
      />

      {/* Create Group Dialog */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Group</DialogTitle>
            <DialogDescription>
              Create a new researcher group for organizing outreach
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="groupName">Group Name</Label>
                <Input
                  id="groupName"
                  placeholder="e.g., AI Research Leads"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="groupDescription">Description (optional)</Label>
                <Input
                  id="groupDescription"
                  placeholder="Purpose of this group"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="groupType">Type</Label>
                <Select value={newType} onValueChange={(v) => setNewType(v as GroupType)}>
                  <SelectTrigger id="groupType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="custom">Custom</SelectItem>
                    <SelectItem value="mailing_list">Mailing List</SelectItem>
                    <SelectItem value="speaker_pool">Speaker Pool</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="groupKeywords">Keywords (comma-separated)</Label>
                <Input
                  id="groupKeywords"
                  placeholder="e.g., machine learning, NLP, computer vision"
                  value={newKeywords}
                  onChange={(e) => setNewKeywords(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={createGroup.isPending}>
                Create Group
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
