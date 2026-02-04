import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  FileText,
  FolderKanban,
  Home,
  Search,
  Settings,
  Users,
} from 'lucide-react'
import { useSidebar } from '@/contexts/SidebarContext'
import { Button } from '@/components/ui/Button'

const navItems = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/papers', icon: FileText, label: 'Papers' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/search', icon: Search, label: 'Search' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

const bottomNavItems = [
  { to: '/team', icon: Users, label: 'Team' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar()

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
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
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
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            title={isCollapsed ? item.label : undefined}
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
            {!isCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom navigation - Team & Settings always visible */}
      <nav className="flex flex-col gap-1 px-2 pb-4 border-t pt-2">
        {bottomNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={isCollapsed ? item.label : undefined}
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
            {!isCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
