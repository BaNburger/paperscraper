import * as Dialog from '@radix-ui/react-dialog'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import { X, LogOut } from 'lucide-react'
import { NAVIGATION_ITEMS } from '@/config/routes'

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
}

export function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  const { user, logout } = useAuth()
  const { t } = useTranslation()

  const visibleItems = NAVIGATION_ITEMS.filter(
    (item) => !item.adminOnly || user?.role === 'admin'
  )
  const menuItems = visibleItems.filter((item) => item.mobileMenuGroup === 'menu')
  const settingsItems = visibleItems.filter((item) => item.mobileMenuGroup === 'settings')

  const handleLogout = () => {
    logout()
    onClose()
  }

  return (
    <Dialog.Root
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 md:hidden data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className={cn(
            'fixed inset-y-0 right-0 w-[280px] bg-background border-l z-50 md:hidden',
            'data-[state=open]:animate-in data-[state=closed]:animate-out',
            'data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right'
          )}
        >
          <Dialog.Title className="sr-only">{t('nav.navigationMenu')}</Dialog.Title>
          <Dialog.Description className="sr-only">
            {t('nav.mobileMenuDescription')}
          </Dialog.Description>

          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <p className="font-medium">{user?.full_name || t('auth.signIn')}</p>
                <p className="text-sm text-muted-foreground">{user?.email}</p>
              </div>
              <Dialog.Close asChild>
                <button
                  type="button"
                  aria-label={t('common.close')}
                  className="p-2 rounded-lg hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <X aria-hidden="true" className="h-5 w-5" />
                </button>
              </Dialog.Close>
            </div>

            <div className="py-2 overflow-y-auto flex-1">
              <div className="px-2">
                <p className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase">
                  {t('nav.menu')}
                </p>
                {menuItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
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
                    <item.icon aria-hidden="true" className="h-5 w-5" />
                    <span>{t(item.labelKey)}</span>
                  </NavLink>
                ))}
              </div>

              <div className="px-2 mt-4">
                <p className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase">
                  {t('nav.settings')}
                </p>
                {settingsItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
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
                    <item.icon aria-hidden="true" className="h-5 w-5" />
                    <span>{t(item.labelKey)}</span>
                  </NavLink>
                ))}
              </div>
            </div>

            <div className="p-4 border-t bg-background">
              <button
                type="button"
                onClick={handleLogout}
                aria-label={t('auth.logout')}
                className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <LogOut aria-hidden="true" className="h-5 w-5" />
                <span>{t('auth.logout')}</span>
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
