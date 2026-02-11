import type { ReactNode, RefObject } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { cn } from '@/lib/utils'

interface AccessibleModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  children: ReactNode
  className?: string
  contentClassName?: string
  initialFocusRef?: RefObject<HTMLElement | null>
}

export function AccessibleModal({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
  contentClassName,
  initialFocusRef,
}: AccessibleModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn('max-h-[90vh] overflow-y-auto', contentClassName)}
        onOpenAutoFocus={(event) => {
          if (!initialFocusRef?.current) return
          event.preventDefault()
          initialFocusRef.current.focus()
        }}
      >
        <DialogHeader className={className}>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {children}
      </DialogContent>
    </Dialog>
  )
}
