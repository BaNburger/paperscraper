import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  Home,
  FileText,
  FolderKanban,
  Search,
  Menu,
} from 'lucide-react'

interface MobileBottomNavProps {
  onMenuClick: () => void
}

const navItems = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/papers', icon: FileText, label: 'Papers' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/search', icon: Search, label: 'Search' },
]

export function MobileBottomNav({ onMenuClick }: MobileBottomNavProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden">
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg transition-colors min-w-[56px]',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span className="text-[10px] font-medium">{item.label}</span>
          </NavLink>
        ))}
        <button
          onClick={onMenuClick}
          className="flex flex-col items-center justify-center gap-1 py-2 px-3 rounded-lg text-muted-foreground hover:text-foreground transition-colors min-w-[56px]"
        >
          <Menu className="h-5 w-5" />
          <span className="text-[10px] font-medium">More</span>
        </button>
      </div>
    </nav>
  )
}
