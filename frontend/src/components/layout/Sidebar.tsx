import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import {
  ArrowRightLeft,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  ChevronLeft,
  ChevronRight,
  FileText,
  FolderKanban,
  Home,
  Inbox,
  Search,
  Settings,
  Shield,
  Trophy,
  Users,
  UsersRound,
} from 'lucide-react'
import { useSidebar } from '@/contexts/SidebarContext'
import { Button } from '@/components/ui/Button'

const navItems = [
  { to: '/', icon: Home, labelKey: 'nav.dashboard' },
  { to: '/papers', icon: FileText, labelKey: 'nav.papers' },
  { to: '/projects', icon: FolderKanban, labelKey: 'nav.projects' },
  { to: '/search', icon: Search, labelKey: 'nav.search' },
  { to: '/groups', icon: UsersRound, labelKey: 'nav.groups' },
  { to: '/transfer', icon: ArrowRightLeft, labelKey: 'nav.transfer' },
  { to: '/submissions', icon: Inbox, labelKey: 'nav.submissions' },
  { to: '/analytics', icon: BarChart3, labelKey: 'nav.analytics' },
  { to: '/alerts', icon: Bell, labelKey: 'nav.alerts' },
]

const bottomNavItems = [
  { to: '/badges', icon: Trophy, labelKey: 'nav.badges' },
  { to: '/team', icon: Users, labelKey: 'nav.team' },
  { to: '/knowledge', icon: BookOpen, labelKey: 'nav.knowledge' },
  { to: '/compliance', icon: Shield, labelKey: 'nav.compliance' },
  { to: '/settings', icon: Settings, labelKey: 'nav.settings' },
  { to: '/settings/models', icon: Bot, labelKey: 'nav.aiModels' },
]

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar()
  const { t } = useTranslation()

  return (
    <aside
      className={cn(
        'sticky top-0 h-screen shrink-0 border-r bg-muted/40 hidden md:flex md:flex-col transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Collapse toggle button */}
      <div className={cn('flex p-2', isCollapsed ? 'justify-center' : 'justify-end')}>
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className="h-8 w-8 p-0"
          aria-label={isCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Main navigation */}
      <nav className="flex flex-col gap-1 px-2 flex-1">
        {navItems.map((item) => {
          const label = t(item.labelKey)
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              title={isCollapsed ? label : undefined}
              className={({ isActive }) =>
                cn(
                  'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isCollapsed ? 'justify-center' : 'gap-3',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!isCollapsed && <span>{label}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom navigation - Team & Settings always visible */}
      <nav className="flex flex-col gap-1 px-2 pb-4 border-t pt-2">
        {bottomNavItems.map((item) => {
          const label = t(item.labelKey)
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={isCollapsed ? label : undefined}
              className={({ isActive }) =>
                cn(
                  'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isCollapsed ? 'justify-center' : 'gap-3',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!isCollapsed && <span>{label}</span>}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
