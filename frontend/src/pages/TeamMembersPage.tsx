import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/Dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu'
import { Badge } from '@/components/ui/Badge'
import { Users, UserPlus, MoreHorizontal, Shield, Mail, Clock, Check, X } from 'lucide-react'
import { getApiErrorMessage } from '@/types'
import type { UserRole, TeamInvitation, OrganizationUsers } from '@/types'
import { useTeamMembers } from '@/features/team-members/hooks/useTeamMembers'

const roleLabels: Record<UserRole, string> = {
  admin: 'Admin',
  manager: 'Manager',
  member: 'Member',
  viewer: 'Viewer',
}

const roleColors: Record<UserRole, string> = {
  admin: 'bg-red-100 text-red-800',
  manager: 'bg-blue-100 text-blue-800',
  member: 'bg-green-100 text-green-800',
  viewer: 'bg-gray-100 text-gray-800',
}

export function TeamMembersPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<UserRole>('member')
  const [inviteError, setInviteError] = useState('')

  const {
    usersQuery,
    invitationsQuery,
    inviteMutation,
    updateRoleMutation,
    deactivateMutation,
    reactivateMutation,
    cancelInvitationMutation,
  } = useTeamMembers()

  const usersData = usersQuery.data as OrganizationUsers | undefined
  const loadingUsers = usersQuery.isLoading
  const invitations = invitationsQuery.data as TeamInvitation[] | undefined

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault()
    setInviteError('')
    inviteMutation.mutate(
      { email: inviteEmail, role: inviteRole },
      {
        onSuccess: () => {
          setInviteDialogOpen(false)
          setInviteEmail('')
          setInviteRole('member')
          setInviteError('')
        },
        onError: (err) => {
          setInviteError(getApiErrorMessage(err, 'Failed to send invitation'))
        },
      }
    )
  }

  const isCurrentUser = (userId: string) => user?.id === userId

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8" />
            {t('team.title')}
          </h1>
          <p className="text-muted-foreground mt-1">
            {t('team.subtitle')}
          </p>
        </div>
        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <UserPlus className="mr-2 h-4 w-4" />
              {t('team.inviteMember')}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('team.inviteDialogTitle')}</DialogTitle>
              <DialogDescription>
                {t('team.inviteDialogDescription')}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleInvite}>
              <div className="space-y-4 py-4">
                {inviteError && (
                  <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                    {inviteError}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="email">{t('team.emailAddress')}</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="colleague@example.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">{t('team.role')}</Label>
                  <Select value={inviteRole} onValueChange={(v) => setInviteRole(v as UserRole)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="viewer">{t('team.viewerRole')}</SelectItem>
                      <SelectItem value="member">{t('team.memberRole')}</SelectItem>
                      <SelectItem value="manager">{t('team.managerRole')}</SelectItem>
                      <SelectItem value="admin">{t('team.adminRole')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setInviteDialogOpen(false)}>
                  {t('common.cancel')}
                </Button>
                <Button type="submit" isLoading={inviteMutation.isPending}>
                  {t('team.sendInvitation')}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('team.totalMembers')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usersData?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('team.pendingInvitations')}</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usersData?.pending_invitations || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('team.admins')}</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usersData?.users.filter((u) => u.role === 'admin').length || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Members */}
      <Card>
        <CardHeader>
          <CardTitle>{t('team.activeMembers')}</CardTitle>
          <CardDescription>
            {t('team.activeMembersDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('team.user')}</TableHead>
                <TableHead>{t('team.role')}</TableHead>
                <TableHead>{t('team.status')}</TableHead>
                <TableHead>{t('team.joined')}</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loadingUsers ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    {t('common.loading')}
                  </TableCell>
                </TableRow>
              ) : usersData?.users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    {t('team.noMembers')}
                  </TableCell>
                </TableRow>
              ) : (
                usersData?.users.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">
                          {member.full_name || 'No name'}
                          {isCurrentUser(member.id) && (
                            <span className="ml-2 text-xs text-muted-foreground">(you)</span>
                          )}
                        </p>
                        <p className="text-sm text-muted-foreground">{member.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={roleColors[member.role]}>
                        {roleLabels[member.role]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {member.is_active ? (
                          <Badge variant="outline" className="text-green-600 border-green-600">
                            <Check className="mr-1 h-3 w-3" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-red-600 border-red-600">
                            <X className="mr-1 h-3 w-3" />
                            Inactive
                          </Badge>
                        )}
                        {member.email_verified && (
                          <Badge variant="outline" className="text-blue-600 border-blue-600">
                            Verified
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(member.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {!isCurrentUser(member.id) && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" aria-label="User actions menu">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() =>
                                updateRoleMutation.mutate({ userId: member.id, role: 'viewer' })
                              }
                            >
                              {t('team.setAsViewer')}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() =>
                                updateRoleMutation.mutate({ userId: member.id, role: 'member' })
                              }
                            >
                              {t('team.setAsMember')}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() =>
                                updateRoleMutation.mutate({ userId: member.id, role: 'manager' })
                              }
                            >
                              {t('team.setAsManager')}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() =>
                                updateRoleMutation.mutate({ userId: member.id, role: 'admin' })
                              }
                            >
                              {t('team.setAsAdmin')}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {member.is_active ? (
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => deactivateMutation.mutate(member.id)}
                              >
                                {t('team.deactivate')}
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                onClick={() => reactivateMutation.mutate(member.id)}
                              >
                                {t('team.reactivate')}
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pending Invitations */}
      {(invitations?.length || 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              {t('team.pendingInvitations')}
            </CardTitle>
            <CardDescription>
              {t('team.pendingInvitationsDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('team.email')}</TableHead>
                  <TableHead>{t('team.role')}</TableHead>
                  <TableHead>{t('team.expires')}</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invitations?.map((invitation) => (
                  <TableRow key={invitation.id}>
                    <TableCell className="font-medium">{invitation.email}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={roleColors[invitation.role]}>
                        {roleLabels[invitation.role]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(invitation.expires_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => cancelInvitationMutation.mutate(invitation.id)}
                        aria-label="Cancel invitation"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
