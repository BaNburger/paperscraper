import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { NotificationCenter } from '@/components/NotificationCenter'
import { Button } from '@/components/ui/Button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu'
import {
  Building2,
  Check,
  ChevronDown,
  Command,
  FileText,
  LogOut,
  Monitor,
  Moon,
  Settings,
  Sun,
  User,
} from 'lucide-react'
import type { OrganizationBranding } from '@/types'

type Theme = 'light' | 'dark' | 'system'

interface ThemeOption {
  value: Theme
  label: string
  icon: typeof Sun
}

export function Navbar() {
  const { user, logout } = useAuth()
  const { t } = useTranslation()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const navigate = useNavigate()

  const branding = user?.organization?.branding as OrganizationBranding | undefined

  const themeOptions: ThemeOption[] = [
    { value: 'light', label: t('theme.light'), icon: Sun },
    { value: 'dark', label: t('theme.dark'), icon: Moon },
    { value: 'system', label: t('theme.system'), icon: Monitor },
  ]

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

  function handleThemeSelect(selectedTheme: Theme): void {
    setTheme(selectedTheme)
  }

  function handleNavigate(path: string): void {
    navigate(path)
  }

  async function handleLogout(): Promise<void> {
    await logout()
  }

  function openCommandPalette(): void {
    document.dispatchEvent(new CustomEvent('paper-scraper:open-command-palette'))
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded">
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
          type="button"
          onClick={openCommandPalette}
          aria-label={t('nav.openCommandPalette')}
          className="hidden md:flex items-center gap-2 ml-4 px-3 py-1.5 text-sm text-muted-foreground bg-muted/50 hover:bg-muted rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <Command className="h-3.5 w-3.5" />
          <span>{t('nav.search')}</span>
          <kbd className="ml-2 px-1.5 py-0.5 text-[10px] font-mono bg-background rounded border">
            ⌘K
          </kbd>
        </button>

        <div className="ml-auto flex items-center gap-2">
          {user && <NotificationCenter />}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label={t('theme.toggle')}
                className="w-9 h-9"
              >
                {resolvedTheme === 'dark' ? (
                  <Moon className="h-5 w-5" />
                ) : (
                  <Sun className="h-5 w-5" />
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuLabel>{t('theme.title')}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {themeOptions.map((option) => {
                const Icon = option.icon
                return (
                  <DropdownMenuItem
                    key={option.value}
                    onSelect={() => handleThemeSelect(option.value)}
                    className="flex items-center gap-2"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{option.label}</span>
                    {theme === option.value && <Check className="ml-auto h-4 w-4" />}
                  </DropdownMenuItem>
                )
              })}
            </DropdownMenuContent>
          </DropdownMenu>

          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2 h-auto px-2 py-1">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                  <span className="hidden sm:inline truncate max-w-[180px]">
                    {user.full_name || user.email}
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="space-y-1">
                  <p className="text-sm font-medium leading-none">{user.full_name || 'User'}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {user.role} {t('common.at')} {user.organization?.name}
                  </p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={() => handleNavigate('/settings')}>
                  <Settings className="h-4 w-4 mr-2" />
                  {t('nav.settings')}
                </DropdownMenuItem>
                {user.role === 'admin' && (
                  <DropdownMenuItem onSelect={() => handleNavigate('/settings/organization')}>
                    <Building2 className="h-4 w-4 mr-2" />
                    {t('orgSettings.title')}
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={() => {
                    void handleLogout()
                  }}
                  className="text-red-600 dark:text-red-400 focus:text-red-700"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  {t('auth.logout')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  )
}
