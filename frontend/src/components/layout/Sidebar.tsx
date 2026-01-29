import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { FileText, FolderKanban, Home, Search } from 'lucide-react'

const navItems = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/papers', icon: FileText, label: 'Papers' },
  { to: '/projects', icon: FolderKanban, label: 'Projects' },
  { to: '/search', icon: Search, label: 'Search' },
]

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-muted/40 md:block">
      <nav className="flex flex-col gap-2 p-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
