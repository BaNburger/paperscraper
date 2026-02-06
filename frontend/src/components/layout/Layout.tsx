import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
import { MobileBottomNav } from './MobileBottomNav'
import { MobileMenu } from './MobileMenu'

export function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pb-20 md:pb-0">
          <div className="container mx-auto p-4 md:p-6">
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
