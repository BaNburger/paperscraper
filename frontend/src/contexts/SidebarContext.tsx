import { createContext, useContext, useState, type ReactNode } from 'react'

interface SidebarContextType {
  isCollapsed: boolean
  toggleSidebar: () => void
  setCollapsed: (collapsed: boolean) => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

const SIDEBAR_COLLAPSED_KEY = 'paper_scraper_sidebar_collapsed'

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
    return stored === 'true'
  })

  const toggleSidebar = () => {
    setIsCollapsed((prev) => {
      const newValue = !prev
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(newValue))
      return newValue
    })
  }

  const setCollapsed = (collapsed: boolean) => {
    setIsCollapsed(collapsed)
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed))
  }

  return (
    <SidebarContext.Provider value={{ isCollapsed, toggleSidebar, setCollapsed }}>
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  const context = useContext(SidebarContext)
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider')
  }
  return context
}
