import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { NotificationCenter } from '@/components/NotificationCenter'
import { FileText, LogOut, User, Settings, Building2, ChevronDown, Sun, Moon, Monitor, Command } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { OrganizationBranding } from '@/types'

type Theme = 'light' | 'dark' | 'system'

interface ThemeOption {
  value: Theme
  label: string
  icon: LucideIcon
}

const themeOptions: ThemeOption[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
]

export function Navbar() {
  const { user, logout } = useAuth()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const navigate = useNavigate()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isThemeDropdownOpen, setIsThemeDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const themeDropdownRef = useRef<HTMLDivElement>(null)

  const branding = user?.organization?.branding as OrganizationBranding | undefined

  // Apply org branding colors as CSS custom properties (validated hex only)
  useEffect(() => {
    const hexPattern = /^#[0-9a-fA-F]{3,8}$/
    if (branding?.primary_color && hexPattern.test(branding.primary_color)) {
      document.documentElement.style.setProperty('--org-primary', branding.primary_color)
    }
    if (branding?.accent_color && hexPattern.test(branding.accent_color)) {
      document.documentElement.style.setProperty('--org-accent', branding.accent_color)
    }
    return () => {
      document.documentElement.style.removeProperty('--org-primary')
      document.documentElement.style.removeProperty('--org-accent')
    }
  }, [branding?.primary_color, branding?.accent_color])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent): void {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
      if (themeDropdownRef.current && !themeDropdownRef.current.contains(event.target as Node)) {
        setIsThemeDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleThemeSelect(selectedTheme: Theme): void {
    setTheme(selectedTheme)
    setIsThemeDropdownOpen(false)
  }

  function handleNavigate(path: string): void {
    setIsDropdownOpen(false)
    navigate(path)
  }

  function handleLogout(): void {
    setIsDropdownOpen(false)
    logout()
  }

  function openCommandPalette(): void {
    // Dispatch Cmd+K event to open command palette
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      metaKey: true,
      bubbles: true,
    })
    document.dispatchEvent(event)
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          {branding?.logo_url ? (
            <img
              src={branding.logo_url}
              alt={user?.organization?.name || 'Logo'}
              className="h-7 w-7 object-contain rounded"
            />
          ) : (
            <FileText className="h-6 w-6 text-primary" />
          )}
          <span className="hidden sm:inline">
            {user?.organization?.name || 'Paper Scraper'}
          </span>
        </Link>

        {/* Command Palette Hint */}
        <button
          onClick={openCommandPalette}
          className="hidden md:flex items-center gap-2 ml-4 px-3 py-1.5 text-sm text-muted-foreground bg-muted/50 hover:bg-muted rounded-lg transition-colors"
        >
          <Command className="h-3.5 w-3.5" />
          <span>Search...</span>
          <kbd className="ml-2 px-1.5 py-0.5 text-[10px] font-mono bg-background rounded border">
            ⌘K
          </kbd>
        </button>

        <div className="ml-auto flex items-center gap-2">
          {/* Notifications */}
          {user && <NotificationCenter />}

          {/* Theme Toggle */}
          <div className="relative" ref={themeDropdownRef}>
            <button
              onClick={() => setIsThemeDropdownOpen(!isThemeDropdownOpen)}
              className="flex items-center justify-center w-9 h-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              aria-label="Toggle theme"
            >
              {resolvedTheme === 'dark' ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
            </button>

            {isThemeDropdownOpen && (
              <div className="absolute right-0 mt-2 w-36 rounded-md border bg-popover shadow-lg">
                <div className="p-1">
                  {themeOptions.map((option) => {
                    const Icon = option.icon
                    return (
                      <button
                        key={option.value}
                        onClick={() => handleThemeSelect(option.value)}
                        className={`flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent ${
                          theme === option.value ? 'bg-accent' : ''
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        {option.label}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {user && (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors rounded-lg px-2 py-1"
              >
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-4 w-4 text-primary" />
                </div>
                <span className="hidden sm:inline">{user.full_name || user.email}</span>
                <ChevronDown className="h-4 w-4" />
              </button>

              {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-md border bg-popover shadow-lg">
                  <div className="p-2 border-b">
                    <p className="text-sm font-medium">{user.full_name || 'User'}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                    <p className="text-xs text-muted-foreground mt-1 capitalize">
                      {user.role} at {user.organization?.name}
                    </p>
                  </div>
                  <div className="p-1">
                    <button
                      onClick={() => handleNavigate('/settings')}
                      className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                    >
                      <Settings className="h-4 w-4" />
                      User Settings
                    </button>
                    {user.role === 'admin' && (
                      <button
                        onClick={() => handleNavigate('/settings/organization')}
                        className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
                      >
                        <Building2 className="h-4 w-4" />
                        Organization Settings
                      </button>
                    )}
                  </div>
                  <div className="p-1 border-t">
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950"
                    >
                      <LogOut className="h-4 w-4" />
                      Log out
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
