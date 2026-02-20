import { cn } from '@/lib/utils'

interface RadarScores {
  novelty: number
  ip_potential: number
  marketability: number
  feasibility: number
  commercialization: number
  team_readiness: number
}

interface InnovationRadarProps {
  scores: RadarScores
  size?: number
  className?: string
}

const DIMENSIONS = [
  { key: 'novelty', label: 'Novelty', color: '#8b5cf6' },
  { key: 'ip_potential', label: 'IP Potential', color: '#3b82f6' },
  { key: 'marketability', label: 'Marketability', color: '#10b981' },
  { key: 'feasibility', label: 'Feasibility', color: '#f59e0b' },
  { key: 'commercialization', label: 'Commercialization', color: '#ec4899' },
  { key: 'team_readiness', label: 'Team Ready', color: '#06b6d4' },
] as const

function polarToCartesian(
  cx: number,
  cy: number,
  radius: number,
  angleInDegrees: number
): { x: number; y: number } {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180
  return {
    x: cx + radius * Math.cos(angleInRadians),
    y: cy + radius * Math.sin(angleInRadians),
  }
}

function getScore(scores: RadarScores, key: typeof DIMENSIONS[number]['key']): number {
  return scores[key] || 0
}

export function InnovationRadar({ scores, size = 200, className }: InnovationRadarProps) {
  const cx = size / 2
  const cy = size / 2
  const maxRadius = size * 0.38
  const levels = [2, 4, 6, 8, 10]
  const angleStep = 360 / DIMENSIONS.length

  // Build polygon path for scores
  const scorePoints = DIMENSIONS.map((dim, i) => {
    const radius = (getScore(scores, dim.key) / 10) * maxRadius
    return polarToCartesian(cx, cy, radius, i * angleStep)
  })
  const scorePath = scorePoints.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + 'Z'

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={`Innovation radar: ${DIMENSIONS.map(d => `${d.label} ${getScore(scores, d.key).toFixed(1)}`).join(', ')}`}
      >
        {/* Grid levels */}
        {levels.map((level) => {
          const r = (level / 10) * maxRadius
          const points = DIMENSIONS.map((_, i) => polarToCartesian(cx, cy, r, i * angleStep))
          const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ') + 'Z'
          return (
            <path
              key={level}
              d={path}
              fill="none"
              stroke="currentColor"
              strokeWidth={0.5}
              className="text-muted-foreground/20"
            />
          )
        })}

        {/* Axis lines */}
        {DIMENSIONS.map((_, i) => {
          const end = polarToCartesian(cx, cy, maxRadius, i * angleStep)
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={end.x}
              y2={end.y}
              stroke="currentColor"
              strokeWidth={0.5}
              className="text-muted-foreground/20"
            />
          )
        })}

        {/* Score polygon */}
        <path
          d={scorePath}
          fill="hsl(var(--primary) / 0.15)"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          className="animate-scale-in"
          style={{ transformOrigin: `${cx}px ${cy}px` }}
        />

        {/* Score dots */}
        {scorePoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={3}
            fill={DIMENSIONS[i].color}
            stroke="white"
            strokeWidth={1}
          >
            <title>{`${DIMENSIONS[i].label}: ${getScore(scores, DIMENSIONS[i].key).toFixed(1)}`}</title>
          </circle>
        ))}

        {/* Labels */}
        {DIMENSIONS.map((dim, i) => {
          const pos = polarToCartesian(cx, cy, maxRadius + 18, i * angleStep)
          return (
            <text
              key={dim.key}
              x={pos.x}
              y={pos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-muted-foreground"
              fontSize={8}
              fontWeight={500}
            >
              <tspan x={pos.x} dy="-0.4em">{dim.label}</tspan>
              <tspan x={pos.x} dy="1.2em" fontSize={7} fontWeight={700} fill={dim.color}>
                {getScore(scores, dim.key).toFixed(1)}
              </tspan>
            </text>
          )
        })}
      </svg>
    </div>
  )
}
