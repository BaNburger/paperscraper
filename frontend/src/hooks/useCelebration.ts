import { createContext, useContext } from 'react'

export type CelebrationType = 'confetti' | 'stars' | 'sparkles'

export interface CelebrationConfig {
  type?: CelebrationType
  duration?: number
  particleCount?: number
  spread?: number
  colors?: string[]
}

export interface CelebrationEvent {
  id: string
  title: string
  description?: string
  type: CelebrationType
  timestamp: number
}

interface CelebrationContextType {
  celebrate: (config?: CelebrationConfig) => void
  celebrateWithMessage: (title: string, description?: string, config?: CelebrationConfig) => void
  isAnimating: boolean
  currentEvent: CelebrationEvent | null
  dismissEvent: () => void
}

export const CelebrationContext = createContext<CelebrationContextType | null>(null)

export function useCelebration() {
  const context = useContext(CelebrationContext)
  if (!context) {
    throw new Error('useCelebration must be used within a CelebrationProvider')
  }
  return context
}

// Helper to generate unique IDs
let celebrationId = 0
export function generateCelebrationId() {
  return `celebration-${++celebrationId}`
}
