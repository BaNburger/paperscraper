import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export const Skeleton = ({ className }: SkeletonProps) => {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
    />
  )
}

export const SkeletonText = ({ className }: SkeletonProps) => {
  return <Skeleton className={cn('h-4 w-full', className)} />
}

export const SkeletonCard = ({ className }: SkeletonProps) => {
  return (
    <div className={cn('rounded-lg border bg-card p-6 space-y-4', className)}>
      <Skeleton className="h-6 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  )
}

export const SkeletonTable = ({ rows = 5 }: { rows?: number }) => {
  return (
    <div className="space-y-3">
      <div className="flex gap-4 pb-3 border-b">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-2">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/4" />
        </div>
      ))}
    </div>
  )
}

export const SkeletonAvatar = ({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-14 w-14',
  }
  return <Skeleton className={cn('rounded-full', sizeClasses[size])} />
}

export const SkeletonKanban = () => {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {Array.from({ length: 4 }).map((_, columnIndex) => (
        <div key={columnIndex} className="flex-shrink-0 w-72 space-y-3">
          <Skeleton className="h-8 w-full rounded-lg" />
          {Array.from({ length: 3 }).map((_, cardIndex) => (
            <SkeletonCard key={cardIndex} />
          ))}
        </div>
      ))}
    </div>
  )
}

export const SkeletonStats = () => {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-lg border bg-card p-6">
          <Skeleton className="h-4 w-1/2 mb-2" />
          <Skeleton className="h-8 w-3/4" />
        </div>
      ))}
    </div>
  )
}
