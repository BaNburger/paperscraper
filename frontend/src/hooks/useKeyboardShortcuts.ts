import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { TFunction } from 'i18next'

import { NAVIGATION_SHORTCUTS } from '@/config/routes'

export interface KeyboardShortcutDef {
  labelKey: string
  category: 'navigation' | 'actions' | 'general'
}

const NAVIGATION_SHORTCUT_MAP = NAVIGATION_SHORTCUTS.reduce<
  Record<string, { path: string; labelKey: string }>
>((acc, shortcut) => {
  acc[shortcut.keys] = {
    path: shortcut.path,
    labelKey: shortcut.labelKey,
  }
  return acc
}, {})

const ACTION_SHORTCUTS: Record<string, KeyboardShortcutDef> = {
  'n p': { labelKey: 'shortcuts.importPapers', category: 'actions' },
  'n j': { labelKey: 'shortcuts.newProject', category: 'actions' },
  'n t': { labelKey: 'shortcuts.newTransfer', category: 'actions' },
  'n g': { labelKey: 'shortcuts.newGroup', category: 'actions' },
}

const GENERAL_SHORTCUTS: Record<string, KeyboardShortcutDef> = {
  '/': { labelKey: 'shortcuts.focusSearch', category: 'general' },
  '?': { labelKey: 'shortcuts.showShortcuts', category: 'general' },
}

export const KEYBOARD_SHORTCUTS: Record<string, KeyboardShortcutDef> = {
  ...Object.fromEntries(
    Object.entries(NAVIGATION_SHORTCUT_MAP).map(([keys, shortcut]) => [
      keys,
      { labelKey: shortcut.labelKey, category: 'navigation' as const },
    ])
  ),
  ...ACTION_SHORTCUTS,
  ...GENERAL_SHORTCUTS,
}

const CHORD_PREFIXES = new Set(
  Object.keys(KEYBOARD_SHORTCUTS)
    .filter((shortcut) => shortcut.includes(' '))
    .map((shortcut) => shortcut.split(' ')[0])
)

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
    (shortcut: string) => {
      const navigationShortcut = NAVIGATION_SHORTCUT_MAP[shortcut]
      if (navigationShortcut) {
        navigate(navigationShortcut.path)
        return
      }

      switch (shortcut) {
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
        default:
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

      // Handle multi-key shortcuts (e.g. g + x, n + x)
      const key = e.key.toLowerCase()

      if (pendingKey) {
        const chord = `${pendingKey} ${key}`
        if (chord in KEYBOARD_SHORTCUTS) {
          e.preventDefault()
          handleShortcut(chord)
        }

        pendingKey = null
        if (pendingTimeout) {
          clearTimeout(pendingTimeout)
          pendingTimeout = null
        }
      } else if (CHORD_PREFIXES.has(key)) {
        e.preventDefault()
        pendingKey = key
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
