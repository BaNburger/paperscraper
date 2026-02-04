import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { FileText, LogOut, User, Settings, Building2, ChevronDown, Sun, Moon, Monitor } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

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

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <FileText className="h-6 w-6 text-primary" />
          <span>Paper Scraper</span>
        </Link>

        <div className="ml-auto flex items-center gap-4">
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
