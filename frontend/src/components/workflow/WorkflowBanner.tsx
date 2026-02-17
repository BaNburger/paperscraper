import { useState } from 'react'
import { Link } from 'react-router-dom'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface WorkflowBannerProps {
  bannerId: string
  icon: LucideIcon
  message: string
  ctaLabel: string
  ctaPath: string
  condition: boolean
  variant?: 'blue' | 'green' | 'purple'
}

const variantStyles = {
  blue: 'border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/30',
  green: 'border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/30',
  purple: 'border-purple-200 bg-purple-50/50 dark:border-purple-900 dark:bg-purple-950/30',
}

const iconVariantStyles = {
  blue: 'text-blue-600 dark:text-blue-400',
  green: 'text-green-600 dark:text-green-400',
  purple: 'text-purple-600 dark:text-purple-400',
}

function isDismissed(bannerId: string): boolean {
  try {
    return sessionStorage.getItem(`ps_workflow_banner_dismissed_${bannerId}`) === 'true'
  } catch {
    return false
  }
}

function dismiss(bannerId: string) {
  try {
    sessionStorage.setItem(`ps_workflow_banner_dismissed_${bannerId}`, 'true')
  } catch {
    // Private browsing or storage full - silently ignore
  }
}

export function WorkflowBanner({
  bannerId,
  icon: Icon,
  message,
  ctaLabel,
  ctaPath,
  condition,
  variant = 'blue',
}: WorkflowBannerProps) {
  const [dismissed, setDismissed] = useState(() => isDismissed(bannerId))

  if (!condition || dismissed) return null

  const handleDismiss = () => {
    dismiss(bannerId)
    setDismissed(true)
  }

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border px-4 py-3',
        variantStyles[variant]
      )}
    >
      <Icon className={cn('h-5 w-5 shrink-0', iconVariantStyles[variant])} aria-hidden="true" />
      <p className="flex-1 text-sm">{message}</p>
      <Link to={ctaPath}>
        <Button size="sm" variant="outline" className="shrink-0">
          {ctaLabel}
        </Button>
      </Link>
      <button
        type="button"
        onClick={handleDismiss}
        className="shrink-0 rounded-md p-1 hover:bg-accent transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4 text-muted-foreground" />
      </button>
    </div>
  )
}
