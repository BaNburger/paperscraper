import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Building2,
  Users,
  CreditCard,
  Shield,
  Loader2,
  Check,
  AlertTriangle,
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

export const OrganizationSettingsPage = () => {
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
      success('Organization updated', 'Settings have been saved successfully.')
      queryClient.invalidateQueries({ queryKey: ['user'] })
      setTimeout(() => setSaved(false), 3000)
    },
    onError: () => {
      showError('Update failed', 'Failed to update organization settings.')
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
              <h2 className="text-xl font-semibold">Admin Access Required</h2>
              <p className="text-muted-foreground max-w-md">
                Only organization administrators can access organization settings.
                Contact your admin if you need to make changes.
              </p>
              <Button variant="outline" onClick={() => navigate('/settings')}>
                Go to User Settings
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
        <h1 className="text-3xl font-bold">Organization Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your organization's profile and settings
        </p>
      </div>

      <div className="space-y-6">
        {/* Organization Profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              <CardTitle>Organization Profile</CardTitle>
            </div>
            <CardDescription>
              Basic information about your organization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="orgName">Organization Name</Label>
              <Input
                id="orgName"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="Enter organization name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="orgType">Organization Type</Label>
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
              {saved ? 'Saved' : 'Save Changes'}
            </Button>
          </CardContent>
        </Card>

        {/* Team Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                <CardTitle>Team Management</CardTitle>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/team')}
              >
                Manage Team
              </Button>
            </div>
            <CardDescription>
              Invite and manage team members
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Go to the Team Members page to invite new users, manage roles,
              and view pending invitations.
            </p>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              <CardTitle>Subscription</CardTitle>
            </div>
            <CardDescription>
              Your current plan and usage limits
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
                <p className="text-sm text-muted-foreground">Papers</p>
                <p className="font-medium">{features.papers}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Team Members</p>
                <p className="font-medium">{features.users}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">AI Scoring</p>
                <p className="font-medium">{features.scoring}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Projects</p>
                <p className="font-medium">{features.projects}</p>
              </div>
            </div>

            {currentTier !== 'enterprise' && (
              <Button variant="outline" className="w-full">
                Upgrade Plan
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Security & Compliance */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              <CardTitle>Security & Compliance</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">Data Encryption</span>
              <span className="font-medium text-green-600">Enabled</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">Two-Factor Authentication</span>
              <span className="font-medium text-muted-foreground">
                Coming Soon
              </span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">SSO / SAML</span>
              <span className="font-medium text-muted-foreground">
                {currentTier === 'enterprise' ? 'Available' : 'Enterprise Only'}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Data Residency</span>
              <span className="font-medium">EU (Frankfurt)</span>
            </div>
          </CardContent>
        </Card>

        {/* Organization ID */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Organization ID
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
