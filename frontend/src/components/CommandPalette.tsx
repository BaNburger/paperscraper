import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Command } from 'cmdk'
import {
  FileText,
  FolderKanban,
  Keyboard,
  Plus,
  Search,
  Upload,
  UsersRound,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useCommandPaletteData } from '@/hooks/useCommandPaletteData'
import { COMMAND_PALETTE_ITEMS } from '@/config/routes'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/Dialog'
import type { Group, Paper, Project } from '@/types'
import '@/styles/cmdk.css'

export interface CommandPaletteProps {
  onShowKeyboardShortcuts?: () => void
}

interface RecentItem {
  type: 'paper' | 'project' | 'group'
  id: string
  title: string
  timestamp: number
}

const RECENT_ITEMS_KEY = 'paper_scraper_recent_items'
const MAX_RECENT_ITEMS = 5
const OPEN_EVENT = 'paper-scraper:open-command-palette'

function getRecentItems(): RecentItem[] {
  try {
    const stored = localStorage.getItem(RECENT_ITEMS_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function addRecentItem(item: Omit<RecentItem, 'timestamp'>): void {
  try {
    const items = getRecentItems().filter(
      (existing) => !(existing.type === item.type && existing.id === item.id)
    )
    items.unshift({ ...item, timestamp: Date.now() })
    localStorage.setItem(RECENT_ITEMS_KEY, JSON.stringify(items.slice(0, MAX_RECENT_ITEMS)))
  } catch {
    // Ignore storage errors
  }
}

export function CommandPalette({ onShowKeyboardShortcuts }: CommandPaletteProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()
  const { t } = useTranslation()

  const { papers, projects, groups } = useCommandPaletteData({
    open,
    query: search,
    isAuthenticated,
  })

  const recentItems = useMemo(() => (open ? getRecentItems() : []), [open])
  const visibleNavigationItems = useMemo(
    () =>
      COMMAND_PALETTE_ITEMS.filter((item) => {
        if (item.adminOnly && user?.role !== 'admin') return false
        return true
      }),
    [user?.role]
  )

  // Toggle the menu when ⌘K/Ctrl+K is pressed
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prevOpen) => !prevOpen)
      }
    }

    const openPalette = () => setOpen(true)

    document.addEventListener('keydown', down)
    document.addEventListener(OPEN_EVENT, openPalette)
    return () => {
      document.removeEventListener('keydown', down)
      document.removeEventListener(OPEN_EVENT, openPalette)
    }
  }, [])

  const runCommand = useCallback((command: () => void) => {
    setOpen(false)
    setSearch('')
    command()
  }, [])

  const handleNavigate = useCallback(
    (path: string) => {
      runCommand(() => navigate(path))
    },
    [navigate, runCommand]
  )

  const handlePaperSelect = useCallback(
    (paper: Paper) => {
      addRecentItem({ type: 'paper', id: paper.id, title: paper.title })
      runCommand(() => navigate(`/papers/${paper.id}`))
    },
    [navigate, runCommand]
  )

  const handleProjectSelect = useCallback(
    (project: Project) => {
      addRecentItem({ type: 'project', id: project.id, title: project.name })
      runCommand(() => navigate(`/projects/${project.id}`))
    },
    [navigate, runCommand]
  )

  const handleGroupSelect = useCallback(
    (group: Group) => {
      addRecentItem({ type: 'group', id: group.id, title: group.name })
      runCommand(() => navigate(`/groups?selected=${encodeURIComponent(group.id)}`))
    },
    [navigate, runCommand]
  )

  const navigationItems = visibleNavigationItems.filter((item) => !item.path.startsWith('/settings'))
  const settingsItems = visibleNavigationItems.filter((item) => item.path.startsWith('/settings'))

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="cmdk-dialog p-0 gap-0" aria-describedby="command-palette-description">
        <DialogTitle className="sr-only">{t('nav.globalCommandMenu')}</DialogTitle>
        <DialogDescription id="command-palette-description" className="sr-only">
          {t('nav.commandMenuDescription')}
        </DialogDescription>
        <Command label={t('nav.globalCommandMenu')}>
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder={t('nav.commandMenuPlaceholder')}
            className="cmdk-input"
          />
          <Command.List className="cmdk-list">
            <Command.Empty className="cmdk-empty">{t('common.noResults')}</Command.Empty>

            {recentItems.length > 0 && !search && (
              <Command.Group heading={t('nav.recent')} className="cmdk-group">
                {recentItems.map((item) => (
                  <Command.Item
                    key={`${item.type}-${item.id}`}
                    value={`recent-${item.title}`}
                    onSelect={() => {
                      if (item.type === 'paper') {
                        handleNavigate(`/papers/${encodeURIComponent(item.id)}`)
                      } else if (item.type === 'project') {
                        handleNavigate(`/projects/${encodeURIComponent(item.id)}`)
                      } else {
                        handleNavigate(`/groups?selected=${encodeURIComponent(item.id)}`)
                      }
                    }}
                    className="cmdk-item"
                  >
                    {item.type === 'paper' && <FileText className="cmdk-icon" />}
                    {item.type === 'project' && <FolderKanban className="cmdk-icon" />}
                    {item.type === 'group' && <UsersRound className="cmdk-icon" />}
                    <span className="cmdk-item-text">{item.title}</span>
                    <span className="cmdk-badge">{item.type}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            <Command.Group heading={t('dashboard.quickActions')} className="cmdk-group">
              <Command.Item
                value="new-paper-import"
                onSelect={() => handleNavigate('/papers?import=true')}
                className="cmdk-item"
              >
                <Upload className="cmdk-icon" />
                <span className="cmdk-item-text">{t('dashboard.importPapers')}</span>
                <kbd className="cmdk-shortcut">n p</kbd>
              </Command.Item>
              <Command.Item
                value="new-project"
                onSelect={() => handleNavigate('/projects?new=true')}
                className="cmdk-item"
              >
                <Plus className="cmdk-icon" />
                <span className="cmdk-item-text">{t('projects.newProject')}</span>
                <kbd className="cmdk-shortcut">n j</kbd>
              </Command.Item>
              <Command.Item
                value="search-papers"
                onSelect={() => handleNavigate('/search')}
                className="cmdk-item"
              >
                <Search className="cmdk-icon" />
                <span className="cmdk-item-text">{t('dashboard.searchLibrary')}</span>
                <kbd className="cmdk-shortcut">/</kbd>
              </Command.Item>
            </Command.Group>

            <Command.Group heading={t('nav.navigation')} className="cmdk-group">
              {navigationItems.map((item) => (
                <Command.Item
                  key={item.path}
                  value={`go-${item.path}`}
                  onSelect={() => handleNavigate(item.path)}
                  className="cmdk-item"
                >
                  <item.icon className="cmdk-icon" />
                  <span className="cmdk-item-text">{t(item.labelKey)}</span>
                  {item.shortcut && <kbd className="cmdk-shortcut">{item.shortcut}</kbd>}
                </Command.Item>
              ))}
            </Command.Group>

            <Command.Group heading={t('nav.settings')} className="cmdk-group">
              {settingsItems.map((item) => (
                <Command.Item
                  key={item.path}
                  value={`go-${item.path}`}
                  onSelect={() => handleNavigate(item.path)}
                  className="cmdk-item"
                >
                  <item.icon className="cmdk-icon" />
                  <span className="cmdk-item-text">{t(item.labelKey)}</span>
                </Command.Item>
              ))}
              <Command.Item
                value="show-keyboard-shortcuts"
                onSelect={() => {
                  setOpen(false)
                  onShowKeyboardShortcuts?.()
                }}
                className="cmdk-item"
              >
                <Keyboard className="cmdk-icon" />
                <span className="cmdk-item-text">{t('nav.keyboardShortcuts')}</span>
                <kbd className="cmdk-shortcut">?</kbd>
              </Command.Item>
            </Command.Group>

            {search && papers.length > 0 && (
              <Command.Group heading={t('nav.papers')} className="cmdk-group">
                {papers.slice(0, 5).map((paper) => (
                  <Command.Item
                    key={paper.id}
                    value={`paper-${paper.title}`}
                    onSelect={() => handlePaperSelect(paper)}
                    className="cmdk-item"
                  >
                    <FileText className="cmdk-icon" />
                    <span className="cmdk-item-text">{paper.title}</span>
                    <span className="cmdk-badge">{paper.source}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {search && projects.length > 0 && (
              <Command.Group heading={t('nav.projects')} className="cmdk-group">
                {projects.slice(0, 5).map((project) => (
                  <Command.Item
                    key={project.id}
                    value={`project-${project.name}`}
                    onSelect={() => handleProjectSelect(project)}
                    className="cmdk-item"
                  >
                    <FolderKanban className="cmdk-icon" />
                    <span className="cmdk-item-text">{project.name}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {search && groups.length > 0 && (
              <Command.Group heading={t('nav.groups')} className="cmdk-group">
                {groups.slice(0, 5).map((group) => (
                  <Command.Item
                    key={group.id}
                    value={`group-${group.name}`}
                    onSelect={() => handleGroupSelect(group)}
                    className="cmdk-item"
                  >
                    <UsersRound className="cmdk-icon" />
                    <span className="cmdk-item-text">{group.name}</span>
                    <span className="cmdk-badge">
                      {t('groups.memberCount', { count: group.member_count })}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  )
}
