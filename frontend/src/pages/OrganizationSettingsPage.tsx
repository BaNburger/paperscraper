import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Building2,
  Users,
  CreditCard,
  Shield,
  Loader2,
  Check,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useToast } from '@/components/ui/Toast'
import type { UpdateOrganizationRequest } from '@/types'
import { useNavigate } from 'react-router-dom'

const organizationTypes = [
  { id: 'university', label: 'University / Research Institution' },
  { id: 'vc', label: 'Venture Capital' },
  { id: 'corporate', label: 'Corporate Innovation' },
  { id: 'startup', label: 'Startup' },
  { id: 'other', label: 'Other' },
]

const subscriptionFeatures = {
  free: {
    papers: '100 papers',
    users: '3 users',
    scoring: '50 scores/month',
    projects: '2 projects',
  },
  pro: {
    papers: '1,000 papers',
    users: '10 users',
    scoring: '500 scores/month',
    projects: 'Unlimited projects',
  },
  enterprise: {
    papers: 'Unlimited papers',
    users: 'Unlimited users',
    scoring: 'Unlimited scoring',
    projects: 'Unlimited projects',
  },
}

const PERMISSION_LABELS: Record<string, string> = {
  'papers:read': 'View Papers',
  'papers:write': 'Create/Edit Papers',
  'papers:delete': 'Delete Papers',
  'scoring:trigger': 'Trigger AI Scoring',
  'groups:read': 'View Groups',
  'groups:manage': 'Manage Groups',
  'transfer:read': 'View Transfers',
  'transfer:manage': 'Manage Transfers',
  'submissions:read': 'View Submissions',
  'submissions:review': 'Review Submissions',
  'badges:manage': 'Manage Badges',
  'knowledge:manage': 'Manage Knowledge',
  'settings:admin': 'Admin Settings',
  'compliance:view': 'View Compliance',
  'developer:manage': 'Developer API',
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  manager: 'Manager',
  member: 'Member',
  viewer: 'Viewer',
}

const ROLE_ORDER = ['admin', 'manager', 'member', 'viewer']

function PermissionMatrix() {
  const { t } = useTranslation()
  const { data, isLoading, error } = useQuery({
    queryKey: ['roles-permissions'],
    queryFn: () => authApi.getRoles(),
    staleTime: 5 * 60 * 1000,
  })

  const { data: myPerms } = useQuery({
    queryKey: ['my-permissions'],
    queryFn: () => authApi.getMyPermissions(),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-600">
        {t('orgSettings.permissionsLoadError')}
      </div>
    )
  }

  const roles = ROLE_ORDER.filter((r) => r in data.roles)
  const allPermissions = [...new Set(roles.flatMap((r) => data.roles[r]))]

  return (
    <div className="space-y-4">
      {myPerms && (
        <div className="rounded-md bg-muted/50 p-3 text-sm">
          <span className="font-medium">{t('orgSettings.yourRole')}:</span>{' '}
          <Badge variant="secondary" className="ml-1">
            {ROLE_LABELS[myPerms.role] || myPerms.role}
          </Badge>
          <span className="ml-2 text-muted-foreground">
            ({myPerms.permissions.length} permissions)
          </span>
        </div>
      )}

      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-3 py-2 text-left font-medium">{t('orgSettings.permission')}</th>
              {roles.map((role) => (
                <th key={role} className="px-3 py-2 text-center font-medium">
                  {ROLE_LABELS[role] || role}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allPermissions.map((perm) => (
              <tr key={perm} className="border-b last:border-0">
                <td className="px-3 py-2 text-muted-foreground">
                  {PERMISSION_LABELS[perm] || perm}
                </td>
                {roles.map((role) => {
                  const has = data.roles[role]?.includes(perm)
                  return (
                    <td key={role} className="px-3 py-2 text-center">
                      {has ? (
                        <Check className="mx-auto h-4 w-4 text-green-600" />
                      ) : (
                        <span className="text-muted-foreground/30">&mdash;</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function OrganizationSettingsPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const navigate = useNavigate()
  const { success, error: showError } = useToast()
  const queryClient = useQueryClient()

  const isAdmin = user?.role === 'admin'
  const org = user?.organization

  // Form state
  const [orgName, setOrgName] = useState(org?.name || '')
  const [orgType, setOrgType] = useState(org?.type || 'university')
  const [saved, setSaved] = useState(false)

  // Update organization mutation
  const updateOrgMutation = useMutation({
    mutationFn: (data: UpdateOrganizationRequest) => authApi.updateOrganization(data),
    onSuccess: () => {
      setSaved(true)
      success(t('orgSettings.updateSuccess'), t('orgSettings.updateSuccessDescription'))
      queryClient.invalidateQueries({ queryKey: ['user'] })
      setTimeout(() => setSaved(false), 3000)
    },
    onError: () => {
      showError(t('orgSettings.updateFailed'), t('orgSettings.updateFailedDescription'))
    },
  })

  const handleSave = () => {
    updateOrgMutation.mutate({
      name: orgName,
      type: orgType,
    })
  }

  if (!isAdmin) {
    return (
      <div className="container max-w-3xl py-8">
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
              </div>
              <h2 className="text-xl font-semibold">{t('orgSettings.adminRequired')}</h2>
              <p className="text-muted-foreground max-w-md">
                {t('orgSettings.adminRequiredDescription')}
              </p>
              <Button variant="outline" onClick={() => navigate('/settings')}>
                {t('orgSettings.goToUserSettings')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const currentTier = (org?.subscription_tier || 'free') as keyof typeof subscriptionFeatures
  const features = subscriptionFeatures[currentTier]

  return (
    <div className="container max-w-3xl py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t('orgSettings.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('orgSettings.subtitle')}
        </p>
      </div>

      <div className="space-y-6">
        {/* Organization Profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              <CardTitle>{t('orgSettings.orgProfile')}</CardTitle>
            </div>
            <CardDescription>
              {t('orgSettings.orgProfileDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="orgName">{t('orgSettings.orgName')}</Label>
              <Input
                id="orgName"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder={t('orgSettings.orgNamePlaceholder')}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="orgType">{t('orgSettings.orgType')}</Label>
              <select
                id="orgType"
                value={orgType}
                onChange={(e) => setOrgType(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {organizationTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <Button
              onClick={handleSave}
              disabled={updateOrgMutation.isPending || !orgName.trim()}
            >
              {updateOrgMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : saved ? (
                <Check className="h-4 w-4 mr-2" />
              ) : null}
              {saved ? t('settings.saved') : t('settings.saveChanges')}
            </Button>
          </CardContent>
        </Card>

        {/* Team Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                <CardTitle>{t('orgSettings.teamManagement')}</CardTitle>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/team')}
              >
                {t('orgSettings.manageTeam')}
              </Button>
            </div>
            <CardDescription>
              {t('orgSettings.teamManagementDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {t('orgSettings.teamManagementInfo')}
            </p>
          </CardContent>
        </Card>

        {/* Role Permissions Matrix */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              <CardTitle>{t('orgSettings.rolePermissions')}</CardTitle>
            </div>
            <CardDescription>
              {t('orgSettings.rolePermissionsDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PermissionMatrix />
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              <CardTitle>{t('orgSettings.subscription')}</CardTitle>
            </div>
            <CardDescription>
              {t('orgSettings.subscriptionDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-lg font-semibold capitalize">{currentTier} Plan</span>
              <Badge variant={currentTier === 'enterprise' ? 'default' : 'secondary'}>
                {currentTier === 'free' ? 'Free' : 'Paid'}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{t('orgSettings.papers')}</p>
                <p className="font-medium">{features.papers}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{t('orgSettings.teamMembers')}</p>
                <p className="font-medium">{features.users}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{t('orgSettings.aiScoring')}</p>
                <p className="font-medium">{features.scoring}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{t('orgSettings.projects')}</p>
                <p className="font-medium">{features.projects}</p>
              </div>
            </div>

            {currentTier !== 'enterprise' && (
              <Button variant="outline" className="w-full">
                {t('orgSettings.upgradePlan')}
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Security & Compliance */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              <CardTitle>{t('orgSettings.securityCompliance')}</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">{t('orgSettings.dataEncryption')}</span>
              <span className="font-medium text-green-600">{t('orgSettings.enabled')}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">{t('orgSettings.twoFactorAuth')}</span>
              <span className="font-medium text-muted-foreground">
                {t('orgSettings.comingSoon')}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">SSO / SAML</span>
              <span className="font-medium text-muted-foreground">
                {currentTier === 'enterprise' ? t('orgSettings.available') : t('orgSettings.enterpriseOnly')}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">{t('orgSettings.dataResidency')}</span>
              <span className="font-medium">EU (Frankfurt)</span>
            </div>
          </CardContent>
        </Card>

        {/* Organization ID */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('orgSettings.organizationId')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <code className="text-sm bg-muted px-2 py-1 rounded">
              {org?.id}
            </code>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
