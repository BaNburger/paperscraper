import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { AuthShell } from '@/components/auth/AuthShell'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { getApiErrorMessage } from '@/types'

export function VerifyEmailPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function verifyEmail() {
      if (!token) {
        if (isMounted) {
          setStatus('error')
          setError(t('auth.invalidVerificationLink'))
        }
        return
      }

      try {
        await authApi.verifyEmail(token)
        if (isMounted) setStatus('success')
      } catch (err) {
        if (isMounted) {
          setStatus('error')
          setError(getApiErrorMessage(err, t('auth.verificationFailed')))
        }
      }
    }

    verifyEmail()
    return () => { isMounted = false }
  }, [token, t])

  if (status === 'loading') {
    return (
      <AuthShell
        title={t('auth.verifyingEmail')}
        description={t('auth.verifyingEmailDescription')}
        icon={<Loader2 className="h-12 w-12 text-primary animate-spin" />}
      />
    )
  }

  if (status === 'success') {
    return (
      <AuthShell
        title={t('auth.emailVerified')}
        description={t('auth.emailVerifiedDescription')}
        icon={<CheckCircle className="h-12 w-12 text-green-500" />}
        contentClassName="space-y-4"
      >
        <div className="flex justify-center">
          <Link to="/dashboard">
            <Button>{t('auth.goToDashboard')}</Button>
          </Link>
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title={t('auth.verificationFailedTitle')}
      description={error}
      icon={<XCircle className="h-12 w-12 text-destructive" />}
      contentClassName="space-y-4"
    >
      <p className="text-sm text-muted-foreground text-center">
        {t('auth.verificationFailedHint')}
      </p>
      <div className="flex justify-center gap-4">
        <Link to="/login">
          <Button variant="outline">{t('auth.signIn')}</Button>
        </Link>
        <Link to="/register">
          <Button>{t('auth.createAccount')}</Button>
        </Link>
      </div>
    </AuthShell>
  )
}
