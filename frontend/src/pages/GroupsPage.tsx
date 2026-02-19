import { useState } from 'react'
import { useTranslation } from 'react-i18next'
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
import { groupsApi } from '@/api'
import { exportApi } from '@/api'
import type { GroupType } from '@/types'

const GROUP_TYPE_KEYS: Record<GroupType, string> = {
  custom: 'groups.typeCustom',
  mailing_list: 'groups.typeMailingList',
  speaker_pool: 'groups.typeSpeakerPool',
}

const GROUP_TYPE_COLORS: Record<GroupType, string> = {
  custom: 'bg-blue-100 text-blue-800',
  mailing_list: 'bg-green-100 text-green-800',
  speaker_pool: 'bg-purple-100 text-purple-800',
}

export function GroupsPage() {
  const { t } = useTranslation()
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
      success(t('groups.createSuccess'), t('groups.createSuccessDescription', { name: newName }))
    } catch {
      showError(t('groups.createFailed'), t('groups.tryAgain'))
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      await deleteGroup.mutateAsync(deleteConfirm.id)
      if (selectedGroupId === deleteConfirm.id) setSelectedGroupId(null)
      success(t('groups.deleteSuccess'), t('groups.deleteSuccessDescription', { name: deleteConfirm.name }))
      setDeleteConfirm(null)
    } catch {
      showError(t('groups.deleteFailed'), t('groups.tryAgain'))
    }
  }

  const handleRemoveMember = async () => {
    if (!removeMemberConfirm) return
    try {
      await removeMember.mutateAsync({
        groupId: removeMemberConfirm.groupId,
        researcherId: removeMemberConfirm.researcherId,
      })
      success(t('groups.memberRemoved'), t('groups.memberRemovedDescription', { name: removeMemberConfirm.name }))
      setRemoveMemberConfirm(null)
    } catch {
      showError(t('groups.removeMemberFailed'), t('groups.tryAgain'))
    }
  }

  const handleExportCsv = async (groupId: string, groupName: string) => {
    try {
      const blob = await groupsApi.exportCsv(groupId)
      const safeFilename = groupName.replace(/[^a-z0-9_-]/gi, '_')
      exportApi.downloadFile(blob, `${safeFilename}-members.csv`)
      success(t('groups.exportComplete'), t('groups.exportCompleteDescription'))
    } catch {
      showError(t('groups.exportFailed'), t('groups.tryAgain'))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('groups.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('groups.subtitle')}
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('groups.newGroup')}
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
                {t('groups.loadFailed')}
              </CardContent>
            </Card>
          ) : !groups?.items?.length ? (
            <Card>
              <CardContent>
                <EmptyState
                  icon={<Users className="h-12 w-12" />}
                  title={t('groups.noGroups')}
                  description={t('groups.noGroupsDescription')}
                  action={{
                    label: t('groups.createGroup'),
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
                      {t(GROUP_TYPE_KEYS[group.type])}
                    </span>
                  </div>
                  {group.description && (
                    <CardDescription className="line-clamp-2">{group.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{t('groups.memberCount', { count: group.member_count })}</span>
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
                      {t('groups.exportCsv')}
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
                  {t('groups.members')} ({selectedGroup.members.length})
                </h3>
                {selectedGroup.members.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t('groups.noMembers')}</p>
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
                <p>{t('groups.selectGroup')}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteConfirm}
        onOpenChange={(open) => !open && setDeleteConfirm(null)}
        title={t('groups.deleteGroup')}
        description={t('groups.deleteConfirm', { name: deleteConfirm?.name })}
        confirmLabel={t('common.delete')}
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteGroup.isPending}
        icon={<AlertTriangle className="h-6 w-6 text-destructive" />}
      />

      {/* Remove Member Confirmation */}
      <ConfirmDialog
        open={!!removeMemberConfirm}
        onOpenChange={(open) => !open && setRemoveMemberConfirm(null)}
        title={t('groups.removeMember')}
        description={t('groups.removeMemberConfirm', { name: removeMemberConfirm?.name })}
        confirmLabel={t('groups.remove')}
        variant="destructive"
        onConfirm={handleRemoveMember}
        isLoading={removeMember.isPending}
      />

      {/* Create Group Dialog */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('groups.createGroup')}</DialogTitle>
            <DialogDescription>
              {t('groups.createDescription')}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="groupName">{t('groups.groupName')}</Label>
                <Input
                  id="groupName"
                  placeholder="e.g., AI Research Leads"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="groupDescription">{t('groups.descriptionOptional')}</Label>
                <Input
                  id="groupDescription"
                  placeholder={t('groups.descriptionPlaceholder')}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="groupType">{t('groups.type')}</Label>
                <Select value={newType} onValueChange={(v) => setNewType(v as GroupType)}>
                  <SelectTrigger id="groupType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="custom">{t('groups.typeCustom')}</SelectItem>
                    <SelectItem value="mailing_list">{t('groups.typeMailingList')}</SelectItem>
                    <SelectItem value="speaker_pool">{t('groups.typeSpeakerPool')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="groupKeywords">{t('groups.keywordsLabel')}</Label>
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
                {t('common.cancel')}
              </Button>
              <Button type="submit" isLoading={createGroup.isPending}>
                {t('groups.createGroup')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
