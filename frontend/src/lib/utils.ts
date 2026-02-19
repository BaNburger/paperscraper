import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

type ScoreLevel = 'high' | 'good' | 'moderate' | 'low'

function getScoreLevel(score: number): ScoreLevel {
  if (score >= 8) return 'high'
  if (score >= 6) return 'good'
  if (score >= 4) return 'moderate'
  return 'low'
}

const SCORE_TEXT_COLORS: Record<ScoreLevel, string> = {
  high: 'text-green-600',
  good: 'text-yellow-600',
  moderate: 'text-orange-600',
  low: 'text-red-600',
}

const SCORE_BG_COLORS: Record<ScoreLevel, string> = {
  high: 'bg-green-100',
  good: 'bg-yellow-100',
  moderate: 'bg-orange-100',
  low: 'bg-red-100',
}

export function getScoreColor(score: number): string {
  return SCORE_TEXT_COLORS[getScoreLevel(score)]
}

export function getScoreBgColor(score: number): string {
  return SCORE_BG_COLORS[getScoreLevel(score)]
}

export function safeExternalUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return undefined
    return url
  } catch {
    return undefined
  }
}
