import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useSidebar } from '@/contexts/SidebarContext'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/contexts/AuthContext'
import { NAVIGATION_ITEMS, SIDEBAR_GROUPS } from '@/config/routes'
import type { SidebarGroup } from '@/config/routes'
import { prefetchRoute } from '@/lib/prefetch'

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar()
  const { t } = useTranslation()
  const { user } = useAuth()

  const visibleItems = NAVIGATION_ITEMS.filter(
    (item) => !item.adminOnly || user?.role === 'admin'
  )

  const getGroupItems = (groupKey: SidebarGroup) =>
    visibleItems.filter((item) => item.sidebarGroup === groupKey)

  const settingsItems = visibleItems.filter((item) => item.sidebarGroup === 'settings')

  return (
    <aside
      className={cn(
        'sticky top-0 h-screen shrink-0 border-r bg-muted/40 hidden md:flex md:flex-col transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Collapse toggle button */}
      <div className={cn('flex shrink-0 p-2', isCollapsed ? 'justify-center' : 'justify-end')}>
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

      {/* Scrollable grouped navigation */}
      <nav className="flex-1 min-h-0 overflow-y-auto flex flex-col px-2 py-1" aria-label={t('nav.mainNavigation')}>
        {SIDEBAR_GROUPS.map((group, groupIndex) => {
          const items = getGroupItems(group.key)
          if (items.length === 0) return null

          return (
            <div key={group.key} className={cn(groupIndex > 0 && 'mt-3')}>
              {isCollapsed ? (
                groupIndex > 0 && <div className="h-px bg-border mx-2 mb-2" />
              ) : (
                <p className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                  {t(group.labelKey, { defaultValue: group.key })}
                </p>
              )}
              <div className="flex flex-col gap-0.5">
                {items.map((item) => {
                  const label = t(item.labelKey)
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === '/'}
                      title={isCollapsed ? label : undefined}
                      onMouseEnter={() => prefetchRoute(item.path)}
                      onFocus={() => prefetchRoute(item.path)}
                      className={({ isActive }) =>
                        cn(
                          'flex items-center rounded-lg px-3 py-1.5 text-sm font-medium transition-colors shrink-0',
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
              </div>
            </div>
          )
        })}
      </nav>

      {/* Settings - pinned to bottom */}
      {settingsItems.length > 0 && (
        <nav
          className="shrink-0 flex flex-col gap-0.5 px-2 pb-4 border-t pt-2"
          aria-label={t('nav.secondaryNavigation')}
        >
          {settingsItems.map((item) => {
            const label = t(item.labelKey)
            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={isCollapsed ? label : undefined}
                onMouseEnter={() => prefetchRoute(item.path)}
                onFocus={() => prefetchRoute(item.path)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
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
      )}
    </aside>
  )
}
