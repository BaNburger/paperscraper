import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { authApi, setStoredTokens } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card'
import { Users, Loader2, XCircle } from 'lucide-react'
import { getApiErrorMessage } from '@/types'
import type { InvitationInfo } from '@/types'

export function AcceptInvitePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const token = searchParams.get('token')

  const [invitationInfo, setInvitationInfo] = useState<InvitationInfo | null>(null)
  const [loadingInfo, setLoadingInfo] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    async function loadInvitationInfo() {
      if (!token) {
        setLoadError('Invalid invitation link')
        setLoadingInfo(false)
        return
      }

      try {
        const info = await authApi.getInvitationInfo(token)
        setInvitationInfo(info)
      } catch (err) {
        setLoadError(getApiErrorMessage(err, 'This invitation is invalid or has expired.'))
      } finally {
        setLoadingInfo(false)
      }
    }

    loadInvitationInfo()
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    if (!token) {
      setError('Invalid invitation link')
      return
    }

    setIsLoading(true)

    try {
      const tokens = await authApi.acceptInvitation({
        token,
        password,
        full_name: fullName || undefined,
      })
      setStoredTokens(tokens)
      await refreshUser()
      navigate('/dashboard')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to accept invitation. Please try again.'))
    } finally {
      setIsLoading(false)
    }
  }

  if (loadingInfo) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <Loader2 className="h-12 w-12 text-primary animate-spin" />
            </div>
            <CardTitle className="text-2xl">Loading invitation...</CardTitle>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <XCircle className="h-12 w-12 text-destructive" />
            </div>
            <CardTitle className="text-2xl">Invalid Invitation</CardTitle>
            <CardDescription>
              {loadError}
            </CardDescription>
          </CardHeader>
          <CardFooter className="flex justify-center gap-4">
            <Link to="/login">
              <Button variant="outline">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button>Create account</Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <Users className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-2xl">You're invited!</CardTitle>
          <CardDescription>
            {invitationInfo?.inviter_name ? (
              <>
                <strong>{invitationInfo.inviter_name}</strong> has invited you to join{' '}
              </>
            ) : (
              <>You've been invited to join </>
            )}
            <strong>{invitationInfo?.organization_name}</strong> on Paper Scraper
            {invitationInfo?.role && (
              <> as a <strong>{invitationInfo.role}</strong></>
            )}.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            <div className="rounded-md bg-muted p-3">
              <p className="text-sm">
                <span className="text-muted-foreground">Email:</span>{' '}
                <strong>{invitationInfo?.email}</strong>
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="fullName">Full name (optional)</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm password</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" isLoading={isLoading}>
              Accept & Create Account
            </Button>
            <p className="text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
