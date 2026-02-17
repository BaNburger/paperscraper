import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { TFunction } from 'i18next'

export interface KeyboardShortcutDef {
  labelKey: string
  category: 'navigation' | 'actions' | 'general'
}

export const KEYBOARD_SHORTCUTS: Record<string, KeyboardShortcutDef> = {
  // Navigation shortcuts (g + letter)
  'g d': { labelKey: 'shortcuts.goToDashboard', category: 'navigation' },
  'g p': { labelKey: 'shortcuts.goToPapers', category: 'navigation' },
  'g k': { labelKey: 'shortcuts.goToProjects', category: 'navigation' },
  'g s': { labelKey: 'shortcuts.goToSearch', category: 'navigation' },
  'g a': { labelKey: 'shortcuts.goToAnalytics', category: 'navigation' },
  'g t': { labelKey: 'shortcuts.goToTransfer', category: 'navigation' },
  'g b': { labelKey: 'shortcuts.goToBadges', category: 'navigation' },
  'g g': { labelKey: 'shortcuts.goToGroups', category: 'navigation' },
  'g r': { labelKey: 'shortcuts.goToTrends', category: 'navigation' },
  'g n': { labelKey: 'shortcuts.goToNotifications', category: 'navigation' },

  // Action shortcuts (n + letter)
  'n p': { labelKey: 'shortcuts.importPapers', category: 'actions' },
  'n j': { labelKey: 'shortcuts.newProject', category: 'actions' },
  'n t': { labelKey: 'shortcuts.newTransfer', category: 'actions' },
  'n g': { labelKey: 'shortcuts.newGroup', category: 'actions' },

  // General shortcuts
  '/': { labelKey: 'shortcuts.focusSearch', category: 'general' },
  '?': { labelKey: 'shortcuts.showShortcuts', category: 'general' },
}

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
        case 'g r':
          navigate('/trends')
          break
        case 'g n':
          navigate('/notifications')
          break

        // Actions
        case 'n p':
          navigate('/papers?import=true')
          break
        case 'n j':
          navigate('/projects?new=true')
          break
        case 'n t':
          navigate('/transfer?new=true')
          break
        case 'n g':
          navigate('/groups?new=true')
          break

        // General
        case '/':
          navigate('/search')
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

export function getShortcutsByCategory(t?: TFunction) {
  const byCategory: Record<string, { keys: string; label: string }[]> = {
    navigation: [],
    actions: [],
    general: [],
  }

  for (const [keys, config] of Object.entries(KEYBOARD_SHORTCUTS)) {
    const label = t ? t(config.labelKey) : config.labelKey
    byCategory[config.category].push({ keys, label })
  }

  // Add the Cmd+K shortcut to general
  const cmdKLabel = t ? t('shortcuts.openCommandPalette') : 'Open Command Palette'
  byCategory.general.unshift({ keys: '⌘K', label: cmdKLabel })

  return byCategory
}
