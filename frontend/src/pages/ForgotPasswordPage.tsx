import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { AuthShell } from '@/components/auth/AuthShell'
import { FileText, ArrowLeft, CheckCircle } from 'lucide-react'
import { getApiErrorMessage } from '@/types'

export function ForgotPasswordPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await authApi.forgotPassword(email)
      setIsSubmitted(true)
    } catch (err) {
      setError(getApiErrorMessage(err, t('auth.forgotPasswordFailed')))
    } finally {
      setIsLoading(false)
    }
  }

  if (isSubmitted) {
    return (
      <AuthShell
        title={t('auth.checkYourEmail')}
        description={t('auth.resetEmailSent', { email })}
        icon={<CheckCircle className="h-12 w-12 text-green-500" />}
        contentClassName="space-y-4"
      >
        <p className="text-sm text-muted-foreground text-center">
          {t('auth.resetEmailExpiry')}
        </p>
        <Link to="/login" className="w-full block">
          <Button variant="outline" className="w-full">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('auth.backToLogin')}
          </Button>
        </Link>
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title={t('auth.forgotPassword')}
      description={t('auth.forgotPasswordDescription')}
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
          <Label htmlFor="email">{t('auth.email')}</Label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <Button type="submit" className="w-full" isLoading={isLoading}>
          {t('auth.sendResetLink')}
        </Button>
        <Link to="/login" className="text-sm text-primary hover:underline block text-center">
          <ArrowLeft className="inline mr-1 h-4 w-4" />
          {t('auth.backToLogin')}
        </Link>
      </form>
    </AuthShell>
  )
}
