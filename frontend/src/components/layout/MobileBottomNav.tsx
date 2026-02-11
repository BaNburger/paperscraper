import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { Menu } from 'lucide-react'
import { NAVIGATION_ITEMS } from '@/config/routes'

interface MobileBottomNavProps {
  onMenuClick: () => void
}

export function MobileBottomNav({ onMenuClick }: MobileBottomNavProps) {
  const { t } = useTranslation()
  const navItems = NAVIGATION_ITEMS.filter((item) => item.mobileBottom)

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden"
      aria-label={t('nav.primaryMobileNavigation')}
    >
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg transition-colors min-w-[56px]',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              )
            }
          >
            <item.icon aria-hidden="true" className="h-5 w-5" />
            <span className="text-[10px] font-medium">{t(item.labelKey)}</span>
          </NavLink>
        ))}
        <button
          type="button"
          onClick={onMenuClick}
          aria-label={t('nav.more')}
          className="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg text-muted-foreground hover:text-foreground transition-colors min-w-[56px]"
        >
          <Menu aria-hidden="true" className="h-5 w-5" />
          <span className="text-[10px] font-medium">{t('nav.more')}</span>
        </button>
      </div>
    </nav>
  )
}
