import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import {
  X,
  ArrowRightLeft,
  BarChart3,
  BookOpen,
  Bot,
  Inbox,
  Settings,
  Trophy,
  Users,
  UsersRound,
  LogOut,
  Building2,
  Code2,
} from 'lucide-react'

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
}

const menuItems = [
  { to: '/groups', icon: UsersRound, label: 'Groups' },
  { to: '/transfer', icon: ArrowRightLeft, label: 'Transfer' },
  { to: '/submissions', icon: Inbox, label: 'Submissions' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/badges', icon: Trophy, label: 'Badges' },
  { to: '/knowledge', icon: BookOpen, label: 'Knowledge' },
  { to: '/team', icon: Users, label: 'Team' },
]

const settingsItems = [
  { to: '/settings', icon: Settings, label: 'User Settings' },
  { to: '/settings/organization', icon: Building2, label: 'Organization', adminOnly: true },
  { to: '/settings/models', icon: Bot, label: 'AI Models' },
  { to: '/settings/developer', icon: Code2, label: 'Developer' },
]

export function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  const { user, logout } = useAuth()

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  // Close menu on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  const handleLogout = () => {
    logout()
    onClose()
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        role="presentation"
        aria-hidden="true"
        className="fixed inset-0 bg-black/50 z-50 md:hidden"
        onClick={onClose}
      />

      {/* Slide-out menu */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Navigation Menu"
        className={cn(
          'fixed inset-y-0 right-0 w-[280px] bg-background border-l z-50 md:hidden',
          'transform transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <p className="font-medium">{user?.full_name || 'User'}</p>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-accent transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="py-2 overflow-y-auto h-[calc(100%-140px)]">
          {/* Main menu items */}
          <div className="px-2">
            <p className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase">
              Menu
            </p>
            {menuItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-accent'
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>

          {/* Settings */}
          <div className="px-2 mt-4">
            <p className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase">
              Settings
            </p>
            {settingsItems
              .filter((item) => !item.adminOnly || user?.role === 'admin')
              .map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-foreground hover:bg-accent'
                    )
                  }
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
          </div>
        </div>

        {/* Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-background">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
          >
            <LogOut className="h-5 w-5" />
            <span>Log out</span>
          </button>
        </div>
      </div>
    </>
  )
}
