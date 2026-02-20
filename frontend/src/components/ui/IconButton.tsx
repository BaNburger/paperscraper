import { forwardRef } from 'react'
import { Button, type ButtonProps } from './Button'
import { cn } from '@/lib/utils'

export interface IconButtonProps extends Omit<ButtonProps, 'size'> {
  size?: 'sm' | 'default' | 'lg'
  'aria-label': string
}

const sizeMap = {
  sm: 'icon-sm' as const,
  default: 'icon' as const,
  lg: 'icon-lg' as const,
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ size = 'default', className, ...props }, ref) => (
    <Button
      ref={ref}
      size={sizeMap[size]}
      className={cn('shrink-0', className)}
      {...props}
    />
  )
)
IconButton.displayName = 'IconButton'
