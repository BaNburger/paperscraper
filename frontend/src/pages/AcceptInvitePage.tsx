import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
        setLoadError(t('auth.invalidInvitationLink'))
        setLoadingInfo(false)
        return
      }

      try {
        const info = await authApi.getInvitationInfo(token)
        setInvitationInfo(info)
      } catch (err) {
        setLoadError(getApiErrorMessage(err, t('auth.invitationExpired')))
      } finally {
        setLoadingInfo(false)
      }
    }

    loadInvitationInfo()
  }, [token, t])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError(t('auth.passwordsDoNotMatch'))
      return
    }

    if (password.length < 8) {
      setError(t('auth.passwordMinLength'))
      return
    }

    if (!token) {
      setError(t('auth.invalidInvitationLink'))
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
      setError(getApiErrorMessage(err, t('auth.acceptInvitationFailed')))
    } finally {
      setIsLoading(false)
    }
  }

  if (loadingInfo) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <Loader2 className="h-12 w-12 text-primary animate-spin" />
            </div>
            <CardTitle className="text-2xl">{t('auth.loadingInvitation')}</CardTitle>
          </CardHeader>
        </Card>
      </main>
    )
  }

  if (loadError) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <XCircle className="h-12 w-12 text-destructive" />
            </div>
            <CardTitle className="text-2xl">{t('auth.invalidInvitation')}</CardTitle>
            <CardDescription>
              {loadError}
            </CardDescription>
          </CardHeader>
          <CardFooter className="flex justify-center gap-4">
            <Link to="/login">
              <Button variant="outline">{t('auth.signIn')}</Button>
            </Link>
            <Link to="/register">
              <Button>{t('auth.createAccount')}</Button>
            </Link>
          </CardFooter>
        </Card>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <Users className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-2xl">{t('auth.youreInvited')}</CardTitle>
          <CardDescription>
            {invitationInfo?.inviter_name ? (
              <>
                <strong>{invitationInfo.inviter_name}</strong> {t('auth.hasInvitedYouToJoin')}{' '}
              </>
            ) : (
              <>{t('auth.youveBeenInvitedToJoin')}{' '}</>
            )}
            <strong>{invitationInfo?.organization_name}</strong> {t('auth.onPaperScraper')}
            {invitationInfo?.role && (
              <> {t('auth.asRole', { role: invitationInfo.role })}</>
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
              <Label htmlFor="fullName">{t('auth.fullNameOptional')}</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t('auth.password')}</Label>
              <Input
                id="password"
                type="password"
                placeholder={t('auth.passwordPlaceholder')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">{t('auth.confirmPassword')}</Label>
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
              {t('auth.acceptAndCreateAccount')}
            </Button>
            <p className="text-sm text-muted-foreground">
              {t('auth.hasAccount')}{' '}
              <Link to="/login" className="text-primary hover:underline">
                {t('auth.signIn')}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </main>
  )
}
