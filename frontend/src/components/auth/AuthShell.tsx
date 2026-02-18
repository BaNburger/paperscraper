import type { ReactNode } from 'react'

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card'

interface AuthShellProps {
  title: string
  description?: ReactNode
  icon?: ReactNode
  footer?: ReactNode
  children?: ReactNode
  contentClassName?: string
  cardClassName?: string
}

export function AuthShell({
  title,
  description,
  icon,
  footer,
  children,
  contentClassName,
  cardClassName,
}: AuthShellProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className={cardClassName ?? 'w-full max-w-md'}>
        <CardHeader className="space-y-1 text-center">
          {icon ? <div className="flex justify-center mb-4">{icon}</div> : null}
          <CardTitle className="text-2xl">{title}</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
        {children ? <CardContent className={contentClassName}>{children}</CardContent> : null}
        {footer ? <CardFooter className="flex flex-col gap-4">{footer}</CardFooter> : null}
      </Card>
    </main>
  )
}
