import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { getApiErrorMessage } from '@/types'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    async function verifyEmail() {
      if (!token) {
        setStatus('error')
        setError('Invalid verification link')
        return
      }

      try {
        await authApi.verifyEmail(token)
        setStatus('success')
      } catch (err) {
        setStatus('error')
        setError(getApiErrorMessage(err, 'Verification failed. The link may have expired.'))
      }
    }

    verifyEmail()
  }, [token])

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <Loader2 className="h-12 w-12 text-primary animate-spin" />
            </div>
            <CardTitle className="text-2xl">Verifying your email...</CardTitle>
            <CardDescription>
              Please wait while we verify your email address.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle className="h-12 w-12 text-green-500" />
            </div>
            <CardTitle className="text-2xl">Email verified!</CardTitle>
            <CardDescription>
              Your email address has been successfully verified. You can now use all features of Paper Scraper.
            </CardDescription>
          </CardHeader>
          <CardFooter className="flex justify-center">
            <Link to="/dashboard">
              <Button>Go to Dashboard</Button>
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
            <XCircle className="h-12 w-12 text-destructive" />
          </div>
          <CardTitle className="text-2xl">Verification failed</CardTitle>
          <CardDescription>
            {error}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-sm text-muted-foreground">
            If your link has expired, you can request a new verification email from your account settings.
          </p>
        </CardContent>
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
