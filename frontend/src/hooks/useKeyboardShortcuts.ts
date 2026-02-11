import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

export interface KeyboardShortcut {
  keys: string
  label: string
  description: string
  category: 'navigation' | 'actions' | 'general'
  handler: () => void
}

export const KEYBOARD_SHORTCUTS = {
  // Navigation shortcuts (g + letter)
  'g d': { label: 'Go to Dashboard', category: 'navigation' as const },
  'g p': { label: 'Go to Papers', category: 'navigation' as const },
  'g k': { label: 'Go to Projects (KanBan)', category: 'navigation' as const },
  'g s': { label: 'Go to Search', category: 'navigation' as const },
  'g a': { label: 'Go to Analytics', category: 'navigation' as const },
  'g t': { label: 'Go to Transfer', category: 'navigation' as const },
  'g b': { label: 'Go to Badges', category: 'navigation' as const },
  'g g': { label: 'Go to Groups', category: 'navigation' as const },

  // Action shortcuts (n + letter)
  'n p': { label: 'Import Papers', category: 'actions' as const },
  'n j': { label: 'New Project', category: 'actions' as const },

  // General shortcuts
  '/': { label: 'Focus Search', category: 'general' as const },
  '?': { label: 'Show Keyboard Shortcuts', category: 'general' as const },
} as const

type ShortcutKey = keyof typeof KEYBOARD_SHORTCUTS

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  )
}

function isOverlayOpen(): boolean {
  return (
    document.querySelector('[role="dialog"][aria-modal="true"]') !== null ||
    document.querySelector('[data-state="open"][role="dialog"]') !== null ||
    document.querySelector('[data-state="open"][role="menu"]') !== null ||
    document.querySelector('[data-radix-dropdown-menu-content][data-state="open"]') !== null
  )
}

export function useKeyboardShortcuts(onShowHelp?: () => void) {
  const navigate = useNavigate()

  const handleShortcut = useCallback(
    (shortcut: ShortcutKey) => {
      switch (shortcut) {
        // Navigation
        case 'g d':
          navigate('/')
          break
        case 'g p':
          navigate('/papers')
          break
        case 'g k':
          navigate('/projects')
          break
        case 'g s':
          navigate('/search')
          break
        case 'g a':
          navigate('/analytics')
          break
        case 'g t':
          navigate('/transfer')
          break
        case 'g b':
          navigate('/badges')
          break
        case 'g g':
          navigate('/groups')
          break

        // Actions
        case 'n p':
          navigate('/papers?import=true')
          break
        case 'n j':
          navigate('/projects?new=true')
          break

        // General
        case '/':
          navigate('/search')
          // Focus the search input after navigation
          setTimeout(() => {
            const searchInput = document.querySelector<HTMLInputElement>(
              'input[placeholder*="Search"]'
            )
            searchInput?.focus()
          }, 100)
          break
        case '?':
          onShowHelp?.()
          break
      }
    },
    [navigate, onShowHelp]
  )

  useEffect(() => {
    let pendingKey: string | null = null
    let pendingTimeout: ReturnType<typeof setTimeout> | null = null

    const handleKeyDown = (e: KeyboardEvent) => {
      const typingInField = isTypingTarget(e.target)
      const dialogOpen = isOverlayOpen()

      // Prevent global shortcuts while interacting with dialogs.
      if (dialogOpen) {
        if (e.key === 'Escape') {
          pendingKey = null
          if (pendingTimeout) {
            clearTimeout(pendingTimeout)
            pendingTimeout = null
          }
        }
        return
      }

      // Ignore if command/ctrl/alt is pressed (except for ?)
      if ((e.metaKey || e.ctrlKey || e.altKey) && e.key !== '?') {
        return
      }

      // Ignore shortcuts while typing, except explicit help shortcut.
      if (typingInField && e.key !== '?') {
        return
      }

      // Handle single-key shortcuts
      if (e.key === '?') {
        e.preventDefault()
        handleShortcut('?')
        return
      }

      if (e.key === '/') {
        if (typingInField) {
          return
        }
        e.preventDefault()
        handleShortcut('/')
        return
      }

      // Handle two-key shortcuts (chord)
      const key = e.key.toLowerCase()

      if (pendingKey) {
        // We have a pending first key, try to match chord
        const chord = `${pendingKey} ${key}` as ShortcutKey
        if (chord in KEYBOARD_SHORTCUTS) {
          e.preventDefault()
          handleShortcut(chord)
        }
        // Reset pending state
        pendingKey = null
        if (pendingTimeout) {
          clearTimeout(pendingTimeout)
          pendingTimeout = null
        }
      } else if (key === 'g' || key === 'n') {
        // Start chord sequence
        e.preventDefault()
        pendingKey = key
        // Reset after 1 second if no second key
        pendingTimeout = setTimeout(() => {
          pendingKey = null
          pendingTimeout = null
        }, 1000)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      if (pendingTimeout) {
        clearTimeout(pendingTimeout)
      }
    }
  }, [handleShortcut])
}

export function getShortcutsByCategory() {
  const byCategory: Record<string, { keys: string; label: string }[]> = {
    navigation: [],
    actions: [],
    general: [],
  }

  for (const [keys, config] of Object.entries(KEYBOARD_SHORTCUTS)) {
    byCategory[config.category].push({ keys, label: config.label })
  }

  // Add the Cmd+K shortcut to general
  byCategory.general.unshift({ keys: '⌘K', label: 'Open Command Palette' })

  return byCategory
}
