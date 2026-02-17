import { ArrowRight } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { BenchmarkMetric, FunnelStage } from '@/types'

export function SimpleBarChart({
  data,
  height = 200,
  label,
}: {
  data: { name: string; value: number }[]
  height?: number
  label?: string
}) {
  const maxValue = Math.max(...data.map((d) => d.value), 1)

  return (
    <div className="space-y-2">
      {label && <p className="text-sm text-muted-foreground mb-4">{label}</p>}
      <div className="flex items-end gap-2" style={{ height }}>
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-xs font-medium">{item.value}</span>
            <div
              className="w-full bg-primary/80 rounded-t transition-all hover:bg-primary"
              style={{
                height: `${(item.value / maxValue) * (height - 40)}px`,
                minHeight: item.value > 0 ? '4px' : '0px',
              }}
            />
            <span className="text-xs text-muted-foreground truncate w-full text-center">
              {item.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ComparisonBarChart({ data }: { data: BenchmarkMetric[] }) {
  const maxValue = Math.max(...data.flatMap((d) => [d.org_value, d.benchmark_value]), 1)

  return (
    <div className="space-y-4">
      {data.map((metric, index) => (
        <div key={index} className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{metric.label}</span>
            <span className="text-muted-foreground">
              {metric.org_value.toFixed(1)}{metric.unit} vs {metric.benchmark_value.toFixed(1)}
              {metric.unit}
            </span>
          </div>
          <div className="flex gap-2" style={{ height: 24 }}>
            <div className="flex-1 bg-muted rounded overflow-hidden">
              <div
                className={cn(
                  'h-full transition-all',
                  metric.higher_is_better
                    ? metric.org_value >= metric.benchmark_value
                      ? 'bg-green-500'
                      : 'bg-orange-500'
                    : metric.org_value <= metric.benchmark_value
                      ? 'bg-green-500'
                      : 'bg-orange-500'
                )}
                style={{ width: `${(metric.org_value / maxValue) * 100}%` }}
              />
            </div>
            <div className="flex-1 bg-muted rounded overflow-hidden">
              <div
                className="h-full bg-blue-500/50"
                style={{ width: `${(metric.benchmark_value / maxValue) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-primary" />
              Your org
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-blue-500/50" />
              Platform avg
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function SimpleLineChart({
  data,
  height = 150,
}: {
  data: { date: string; count: number }[]
  height?: number
}) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground" style={{ height }}>
        No data available
      </div>
    )
  }

  const maxValue = Math.max(...data.map((d) => d.count), 1)
  const points = data.map((d, i) => ({
    x: (i / Math.max(data.length - 1, 1)) * 100,
    y: 100 - (d.count / maxValue) * 100,
    value: d.count,
    date: d.date,
  }))

  const pathD = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')

  return (
    <div className="relative" style={{ height }}>
      <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
        <line x1="0" y1="25" x2="100" y2="25" stroke="currentColor" strokeOpacity="0.1" />
        <line x1="0" y1="50" x2="100" y2="50" stroke="currentColor" strokeOpacity="0.1" />
        <line x1="0" y1="75" x2="100" y2="75" stroke="currentColor" strokeOpacity="0.1" />

        <path
          d={pathD}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />

        <path d={`${pathD} L 100 100 L 0 100 Z`} fill="hsl(var(--primary))" fillOpacity="0.1" />

        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="2"
            fill="hsl(var(--primary))"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className="flex justify-between text-xs text-muted-foreground mt-2">
        <span>{data[0]?.date}</span>
        <span>{data[data.length - 1]?.date}</span>
      </div>
    </div>
  )
}

export function SimpleDonutChart({
  data,
  size = 120,
}: {
  data: { name: string; value: number; color: string }[]
  size?: number
}) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  if (total === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground" style={{ width: size, height: size }}>
        No data
      </div>
    )
  }

  let currentAngle = -90

  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} viewBox="0 0 100 100">
        {data.map((item, index) => {
          const angle = (item.value / total) * 360
          const startAngle = currentAngle
          currentAngle += angle

          const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180)
          const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180)
          const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180)
          const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180)

          const largeArcFlag = angle > 180 ? 1 : 0

          return (
            <path
              key={index}
              d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
              fill={item.color}
              stroke="white"
              strokeWidth="1"
            />
          )
        })}
        <circle cx="50" cy="50" r="25" fill="white" />
        <text x="50" y="50" textAnchor="middle" dominantBaseline="middle" className="text-lg font-bold" fill="currentColor">
          {total}
        </text>
      </svg>
      <div className="space-y-1">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
            <span className="text-muted-foreground">{item.name}</span>
            <span className="font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function FunnelChart({ stages }: { stages: FunnelStage[] }) {
  const maxCount = Math.max(...stages.map((s) => s.count), 1)
  const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']

  return (
    <div className="space-y-3">
      {stages.map((stage, index) => (
        <div key={stage.stage} className="relative">
          <div className="flex items-center gap-4">
            <div className="w-32 text-sm font-medium text-right">{stage.label}</div>
            <div className="flex-1">
              <div
                className="h-10 rounded-r-lg flex items-center justify-end pr-3 transition-all"
                style={{
                  width: `${Math.max((stage.count / maxCount) * 100, 10)}%`,
                  backgroundColor: colors[index % colors.length],
                }}
              >
                <span className="text-white font-bold text-sm">{stage.count}</span>
              </div>
            </div>
            <div className="w-16 text-sm text-muted-foreground text-right">
              {stage.percentage.toFixed(1)}%
            </div>
          </div>
          {index < stages.length - 1 && (
            <div className="flex items-center gap-4 py-1 text-xs text-muted-foreground">
              <div className="w-32" />
              <ArrowRight className="h-3 w-3 ml-2" />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
