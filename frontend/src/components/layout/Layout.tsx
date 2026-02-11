import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
import { MobileBottomNav } from './MobileBottomNav'
import { MobileMenu } from './MobileMenu'

export function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { t } = useTranslation()

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground focus:outline-none"
      >
        {t('common.skipToContent')}
      </a>
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main id="main-content" className="flex-1 overflow-y-auto pb-20 md:pb-0" tabIndex={-1}>
          <div className="container mx-auto p-4 md:p-6 page-reveal">
            <Outlet />
          </div>
        </main>
      </div>
      {/* Mobile Navigation */}
      <MobileBottomNav onMenuClick={() => setIsMobileMenuOpen(true)} />
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />
    </div>
  )
}
