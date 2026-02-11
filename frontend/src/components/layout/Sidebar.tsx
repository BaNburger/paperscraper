import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useSidebar } from '@/contexts/SidebarContext'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/contexts/AuthContext'
import { NAVIGATION_ITEMS } from '@/config/routes'

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar()
  const { t } = useTranslation()
  const { user } = useAuth()

  const visibleItems = NAVIGATION_ITEMS.filter(
    (item) => !item.adminOnly || user?.role === 'admin'
  )
  const mainNavItems = visibleItems.filter((item) => item.desktopGroup === 'main')
  const secondaryNavItems = visibleItems.filter((item) => item.desktopGroup === 'secondary')

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
      <nav className="flex flex-col gap-1 px-2 flex-1" aria-label={t('nav.mainNavigation')}>
        {mainNavItems.map((item) => {
          const label = t(item.labelKey)
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
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
              <item.icon aria-hidden="true" className="h-4 w-4 shrink-0" />
              {!isCollapsed && <span>{label}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom navigation - Team & Settings always visible */}
      <nav
        className="flex flex-col gap-1 px-2 pb-4 border-t pt-2"
        aria-label={t('nav.secondaryNavigation')}
      >
        {secondaryNavItems.map((item) => {
          const label = t(item.labelKey)
          return (
            <NavLink
              key={item.path}
              to={item.path}
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
              <item.icon aria-hidden="true" className="h-4 w-4 shrink-0" />
              {!isCollapsed && <span>{label}</span>}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
