import { useState, useEffect } from 'react'

const MOBILE_BREAKPOINT = 768 // md breakpoint in Tailwind

export function useMobileBreakpoint() {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.innerWidth < MOBILE_BREAKPOINT
  })

  useEffect(() => {
    // Use matchMedia for more efficient listening
    const mediaQuery = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)

    // Named handler to ensure proper cleanup
    const handleChange = (e: MediaQueryListEvent) => setIsMobile(e.matches)
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)

    // Set initial value
    setIsMobile(mediaQuery.matches)

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    } else {
      // Fallback for older browsers
      window.addEventListener('resize', handleResize)
      return () => window.removeEventListener('resize', handleResize)
    }
  }, [])

  return isMobile
}

// Additional breakpoint hooks for more granular control
export function useBreakpoint() {
  const [breakpoint, setBreakpoint] = useState<'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'>('lg')

  useEffect(() => {
    const getBreakpoint = (): 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' => {
      const width = window.innerWidth
      if (width < 640) return 'xs'
      if (width < 768) return 'sm'
      if (width < 1024) return 'md'
      if (width < 1280) return 'lg'
      if (width < 1536) return 'xl'
      return '2xl'
    }

    const handleResize = () => {
      setBreakpoint(getBreakpoint())
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return breakpoint
}

// Check if touch device
export function useTouchDevice() {
  const [isTouch, setIsTouch] = useState(false)

  useEffect(() => {
    const checkTouch = () => {
      setIsTouch(
        'ontouchstart' in window ||
        navigator.maxTouchPoints > 0
      )
    }
    checkTouch()
  }, [])

  return isTouch
}
