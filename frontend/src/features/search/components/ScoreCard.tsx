import { cn, getScoreColor } from '@/lib/utils'

type ScoreCardProps = {
  label: string
  value: number
  className?: string
}

export function ScoreCard({ label, value, className }: ScoreCardProps) {
  return (
    <div className={cn('text-center p-2 rounded-lg bg-muted/50', className)}>
      <div className={cn('text-lg font-bold', getScoreColor(value))}>{value.toFixed(1)}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}
