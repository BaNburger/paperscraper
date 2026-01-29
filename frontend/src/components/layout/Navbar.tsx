import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/Button'
import { FileText, LogOut, User } from 'lucide-react'

export function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <FileText className="h-6 w-6 text-primary" />
          <span>Paper Scraper</span>
        </Link>

        <div className="ml-auto flex items-center gap-4">
          {user && (
            <>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span>{user.full_name}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
                <span className="sr-only">Logout</span>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
