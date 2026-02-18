import type { ReactNode } from 'react'

import { Loader2 } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/Card'

interface AsyncStateProps {
  isLoading?: boolean
  error?: boolean
  isEmpty?: boolean
  loadingFallback?: ReactNode
  errorFallback?: ReactNode
  emptyFallback?: ReactNode
  children: ReactNode
}

export function AsyncState({
  isLoading,
  error,
  isEmpty,
  loadingFallback,
  errorFallback,
  emptyFallback,
  children,
}: AsyncStateProps) {
  if (isLoading) {
    return (
      loadingFallback ?? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )
    )
  }

  if (error) {
    return (
      errorFallback ?? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            Something went wrong.
          </CardContent>
        </Card>
      )
    )
  }

  if (isEmpty) {
    return (
      emptyFallback ?? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No data available.
          </CardContent>
        </Card>
      )
    )
  }

  return <>{children}</>
}
