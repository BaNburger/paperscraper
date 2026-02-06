import { useState, useCallback, useEffect, type ReactNode } from 'react'
import confetti from 'canvas-confetti'
import { Trophy, Sparkles, X } from 'lucide-react'
import {
  CelebrationContext,
  type CelebrationConfig,
  type CelebrationEvent,
  generateCelebrationId,
} from '@/hooks/useCelebration'
import { cn } from '@/lib/utils'

const DEFAULT_COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444']

function fireConfetti(config: CelebrationConfig = {}) {
  const {
    particleCount = 100,
    spread = 70,
    colors = DEFAULT_COLORS,
    duration = 3000,
  } = config

  const end = Date.now() + duration

  // Create multiple bursts
  const frame = () => {
    confetti({
      particleCount: particleCount / 10,
      spread,
      origin: { x: Math.random(), y: Math.random() - 0.2 },
      colors,
      startVelocity: 30,
      gravity: 1,
      ticks: 100,
      disableForReducedMotion: true,
    })

    if (Date.now() < end) {
      requestAnimationFrame(frame)
    }
  }

  // Initial burst
  confetti({
    particleCount: particleCount / 2,
    spread: 90,
    origin: { y: 0.6 },
    colors,
    startVelocity: 45,
    gravity: 1.2,
    ticks: 200,
    disableForReducedMotion: true,
  })

  // Side cannons
  confetti({
    particleCount: particleCount / 4,
    angle: 60,
    spread: 55,
    origin: { x: 0 },
    colors,
    disableForReducedMotion: true,
  })
  confetti({
    particleCount: particleCount / 4,
    angle: 120,
    spread: 55,
    origin: { x: 1 },
    colors,
    disableForReducedMotion: true,
  })

  // Continue with smaller bursts
  requestAnimationFrame(frame)
}

function fireStars(config: CelebrationConfig = {}) {
  const { particleCount = 50, colors = DEFAULT_COLORS } = config

  // Star-shaped confetti
  const defaults = {
    spread: 360,
    ticks: 100,
    gravity: 0,
    decay: 0.94,
    startVelocity: 30,
    shapes: ['star'] as confetti.Shape[],
    colors,
    disableForReducedMotion: true,
  }

  function shoot() {
    confetti({
      ...defaults,
      particleCount: particleCount / 3,
      scalar: 1.2,
      shapes: ['star'] as confetti.Shape[],
    })

    confetti({
      ...defaults,
      particleCount: particleCount / 3,
      scalar: 0.75,
      shapes: ['circle'],
    })
  }

  setTimeout(shoot, 0)
  setTimeout(shoot, 100)
  setTimeout(shoot, 200)
}

function fireSparkles(config: CelebrationConfig = {}) {
  const { particleCount = 30, colors = ['#ffd700', '#ffec8b', '#fff8dc'] } = config

  const defaults = {
    origin: { y: 0.7 },
    spread: 50,
    startVelocity: 55,
    gravity: 1.2,
    ticks: 120,
    colors,
    shapes: ['circle'] as confetti.Shape[],
    scalar: 0.6,
    disableForReducedMotion: true,
  }

  confetti({
    ...defaults,
    particleCount,
    origin: { x: 0.5, y: 0.5 },
    spread: 360,
    startVelocity: 25,
    gravity: 0.5,
  })
}

interface CelebrationProviderProps {
  children: ReactNode
}

export function CelebrationProvider({ children }: CelebrationProviderProps) {
  const [isAnimating, setIsAnimating] = useState(false)
  const [currentEvent, setCurrentEvent] = useState<CelebrationEvent | null>(null)

  const celebrate = useCallback((config: CelebrationConfig = {}) => {
    const { type = 'confetti', duration = 3000 } = config

    setIsAnimating(true)

    switch (type) {
      case 'confetti':
        fireConfetti(config)
        break
      case 'stars':
        fireStars(config)
        break
      case 'sparkles':
        fireSparkles(config)
        break
    }

    setTimeout(() => {
      setIsAnimating(false)
    }, duration)
  }, [])

  const celebrateWithMessage = useCallback(
    (title: string, description?: string, config: CelebrationConfig = {}) => {
      const event: CelebrationEvent = {
        id: generateCelebrationId(),
        title,
        description,
        type: config.type || 'confetti',
        timestamp: Date.now(),
      }

      setCurrentEvent(event)
      celebrate(config)

      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        setCurrentEvent((current) => (current?.id === event.id ? null : current))
      }, 5000)
    },
    [celebrate]
  )

  const dismissEvent = useCallback(() => {
    setCurrentEvent(null)
  }, [])

  return (
    <CelebrationContext.Provider
      value={{
        celebrate,
        celebrateWithMessage,
        isAnimating,
        currentEvent,
        dismissEvent,
      }}
    >
      {children}
      {currentEvent && (
        <CelebrationToast event={currentEvent} onDismiss={dismissEvent} />
      )}
    </CelebrationContext.Provider>
  )
}

function CelebrationToast({
  event,
  onDismiss,
}: {
  event: CelebrationEvent
  onDismiss: () => void
}) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Trigger enter animation
    const timer = setTimeout(() => setIsVisible(true), 10)
    return () => clearTimeout(timer)
  }, [])

  const handleDismiss = () => {
    setIsVisible(false)
    setTimeout(onDismiss, 200)
  }

  return (
    <div
      className={cn(
        'fixed bottom-6 left-1/2 -translate-x-1/2 z-[100]',
        'bg-gradient-to-r from-primary to-primary/80 text-primary-foreground',
        'rounded-lg shadow-lg shadow-primary/20',
        'px-6 py-4 flex items-center gap-4',
        'transform transition-all duration-200',
        isVisible
          ? 'translate-y-0 opacity-100'
          : 'translate-y-4 opacity-0'
      )}
    >
      <div className="p-2 bg-primary-foreground/20 rounded-full">
        {event.type === 'stars' ? (
          <Trophy className="h-6 w-6" />
        ) : (
          <Sparkles className="h-6 w-6" />
        )}
      </div>
      <div>
        <p className="font-semibold">{event.title}</p>
        {event.description && (
          <p className="text-sm text-primary-foreground/80">{event.description}</p>
        )}
      </div>
      <button
        onClick={handleDismiss}
        className="ml-2 p-1 rounded-full hover:bg-primary-foreground/20 transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

// Export a standalone function for simple confetti triggering
export function triggerConfetti(config?: CelebrationConfig) {
  fireConfetti(config)
}
