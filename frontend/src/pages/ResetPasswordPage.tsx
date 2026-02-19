import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { authApi } from '@/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { AuthShell } from '@/components/auth/AuthShell'
import { FileText, CheckCircle } from 'lucide-react'
import { getApiErrorMessage } from '@/types'

export function ResetPasswordPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

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
      setError(t('auth.invalidResetLink'))
      return
    }

    setIsLoading(true)

    try {
      await authApi.resetPassword(token, password)
      setIsSuccess(true)
    } catch (err) {
      setError(getApiErrorMessage(err, t('auth.resetPasswordFailed')))
    } finally {
      setIsLoading(false)
    }
  }

  if (!token) {
    return (
      <AuthShell
        title={t('auth.invalidLink')}
        description={t('auth.invalidLinkDescription')}
        contentClassName="space-y-4"
      >
        <div className="flex justify-center">
          <Link to="/forgot-password">
            <Button>{t('auth.requestNewLink')}</Button>
          </Link>
        </div>
      </AuthShell>
    )
  }

  if (isSuccess) {
    return (
      <AuthShell
        title={t('auth.resetPasswordSuccess')}
        description={t('auth.resetPasswordSuccessDescription')}
        icon={<CheckCircle className="h-12 w-12 text-green-500" />}
        contentClassName="space-y-4"
      >
        <div className="flex justify-center">
          <Button onClick={() => navigate('/login')}>
            {t('auth.signIn')}
          </Button>
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title={t('auth.resetYourPassword')}
      description={t('auth.resetYourPasswordDescription')}
      icon={<FileText className="h-12 w-12 text-primary" />}
      contentClassName="space-y-4"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="password">{t('auth.newPassword')}</Label>
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
          <Label htmlFor="confirmPassword">{t('auth.confirmNewPassword')}</Label>
          <Input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        <Button type="submit" className="w-full" isLoading={isLoading}>
          {t('auth.resetPassword')}
        </Button>
      </form>
    </AuthShell>
  )
}
