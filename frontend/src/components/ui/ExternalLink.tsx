import type { AnchorHTMLAttributes, ReactNode } from 'react'

import { safeExternalUrl } from '@/lib/utils'

interface ExternalLinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> {
  href: string | null | undefined
  children: ReactNode
}

export function ExternalLink({ href, children, ...props }: ExternalLinkProps) {
  const safeHref = safeExternalUrl(href)
  if (!safeHref) return null

  return (
    <a href={safeHref} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  )
}
