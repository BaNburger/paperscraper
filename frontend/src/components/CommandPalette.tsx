import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Command } from 'cmdk'
import {
  BarChart3,
  BookOpen,
  FileText,
  FolderKanban,
  Home,
  Inbox,
  Plus,
  Search,
  Settings,
  Trophy,
  Upload,
  Users,
  UsersRound,
  ArrowRightLeft,
  Bot,
  Keyboard,
  Building2,
  Code2,
} from 'lucide-react'
import { usePapers, useProjects, useGroups } from '@/hooks'
import type { Paper, Project, Group } from '@/types'
import '@/styles/cmdk.css'

interface CommandPaletteProps {
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
      (i) => !(i.type === item.type && i.id === item.id)
    )
    items.unshift({ ...item, timestamp: Date.now() })
    localStorage.setItem(
      RECENT_ITEMS_KEY,
      JSON.stringify(items.slice(0, MAX_RECENT_ITEMS))
    )
  } catch {
    // Ignore storage errors
  }
}

export function CommandPalette({ onShowKeyboardShortcuts }: CommandPaletteProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  // Fetch data for search
  const { data: papersData } = usePapers({ page: 1, page_size: 10, search: search || undefined })
  const { data: projectsData } = useProjects()
  const { data: groupsData } = useGroups()

  const [recentItems, setRecentItems] = useState<RecentItem[]>([])

  useEffect(() => {
    setRecentItems(getRecentItems())
  }, [open])

  // Toggle the menu when ⌘K or Ctrl+K is pressed
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const runCommand = useCallback((command: () => void) => {
    setOpen(false)
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

  const papers = papersData?.items ?? []
  const projects = projectsData?.items ?? []
  const groups = groupsData?.items ?? []

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Global Command Menu"
      className="cmdk-dialog"
    >
      <Command.Input
        value={search}
        onValueChange={setSearch}
        placeholder="Type a command or search..."
        className="cmdk-input"
      />
      <Command.List className="cmdk-list">
        <Command.Empty className="cmdk-empty">No results found.</Command.Empty>

        {/* Recent Items */}
        {recentItems.length > 0 && !search && (
          <Command.Group heading="Recent" className="cmdk-group">
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

        {/* Quick Actions */}
        <Command.Group heading="Quick Actions" className="cmdk-group">
          <Command.Item
            value="new-paper-import"
            onSelect={() => handleNavigate('/papers?import=true')}
            className="cmdk-item"
          >
            <Upload className="cmdk-icon" />
            <span className="cmdk-item-text">Import Papers</span>
            <kbd className="cmdk-shortcut">n p</kbd>
          </Command.Item>
          <Command.Item
            value="new-project"
            onSelect={() => handleNavigate('/projects?new=true')}
            className="cmdk-item"
          >
            <Plus className="cmdk-icon" />
            <span className="cmdk-item-text">New Project</span>
            <kbd className="cmdk-shortcut">n j</kbd>
          </Command.Item>
          <Command.Item
            value="search-papers"
            onSelect={() => handleNavigate('/search')}
            className="cmdk-item"
          >
            <Search className="cmdk-icon" />
            <span className="cmdk-item-text">Search Papers</span>
            <kbd className="cmdk-shortcut">/</kbd>
          </Command.Item>
        </Command.Group>

        {/* Navigation */}
        <Command.Group heading="Navigation" className="cmdk-group">
          <Command.Item
            value="go-dashboard"
            onSelect={() => handleNavigate('/')}
            className="cmdk-item"
          >
            <Home className="cmdk-icon" />
            <span className="cmdk-item-text">Dashboard</span>
            <kbd className="cmdk-shortcut">g d</kbd>
          </Command.Item>
          <Command.Item
            value="go-papers"
            onSelect={() => handleNavigate('/papers')}
            className="cmdk-item"
          >
            <FileText className="cmdk-icon" />
            <span className="cmdk-item-text">Papers</span>
            <kbd className="cmdk-shortcut">g p</kbd>
          </Command.Item>
          <Command.Item
            value="go-projects"
            onSelect={() => handleNavigate('/projects')}
            className="cmdk-item"
          >
            <FolderKanban className="cmdk-icon" />
            <span className="cmdk-item-text">Projects</span>
            <kbd className="cmdk-shortcut">g k</kbd>
          </Command.Item>
          <Command.Item
            value="go-search"
            onSelect={() => handleNavigate('/search')}
            className="cmdk-item"
          >
            <Search className="cmdk-icon" />
            <span className="cmdk-item-text">Search</span>
            <kbd className="cmdk-shortcut">g s</kbd>
          </Command.Item>
          <Command.Item
            value="go-groups"
            onSelect={() => handleNavigate('/groups')}
            className="cmdk-item"
          >
            <UsersRound className="cmdk-icon" />
            <span className="cmdk-item-text">Groups</span>
          </Command.Item>
          <Command.Item
            value="go-transfer"
            onSelect={() => handleNavigate('/transfer')}
            className="cmdk-item"
          >
            <ArrowRightLeft className="cmdk-icon" />
            <span className="cmdk-item-text">Transfer</span>
          </Command.Item>
          <Command.Item
            value="go-submissions"
            onSelect={() => handleNavigate('/submissions')}
            className="cmdk-item"
          >
            <Inbox className="cmdk-icon" />
            <span className="cmdk-item-text">Submissions</span>
          </Command.Item>
          <Command.Item
            value="go-analytics"
            onSelect={() => handleNavigate('/analytics')}
            className="cmdk-item"
          >
            <BarChart3 className="cmdk-icon" />
            <span className="cmdk-item-text">Analytics</span>
            <kbd className="cmdk-shortcut">g a</kbd>
          </Command.Item>
          <Command.Item
            value="go-badges"
            onSelect={() => handleNavigate('/badges')}
            className="cmdk-item"
          >
            <Trophy className="cmdk-icon" />
            <span className="cmdk-item-text">Badges</span>
          </Command.Item>
          <Command.Item
            value="go-knowledge"
            onSelect={() => handleNavigate('/knowledge')}
            className="cmdk-item"
          >
            <BookOpen className="cmdk-icon" />
            <span className="cmdk-item-text">Knowledge</span>
          </Command.Item>
          <Command.Item
            value="go-team"
            onSelect={() => handleNavigate('/team')}
            className="cmdk-item"
          >
            <Users className="cmdk-icon" />
            <span className="cmdk-item-text">Team</span>
          </Command.Item>
        </Command.Group>

        {/* Settings */}
        <Command.Group heading="Settings" className="cmdk-group">
          <Command.Item
            value="go-settings"
            onSelect={() => handleNavigate('/settings')}
            className="cmdk-item"
          >
            <Settings className="cmdk-icon" />
            <span className="cmdk-item-text">User Settings</span>
          </Command.Item>
          <Command.Item
            value="go-organization-settings"
            onSelect={() => handleNavigate('/settings/organization')}
            className="cmdk-item"
          >
            <Building2 className="cmdk-icon" />
            <span className="cmdk-item-text">Organization Settings</span>
          </Command.Item>
          <Command.Item
            value="go-model-settings"
            onSelect={() => handleNavigate('/settings/models')}
            className="cmdk-item"
          >
            <Bot className="cmdk-icon" />
            <span className="cmdk-item-text">AI Models</span>
          </Command.Item>
          <Command.Item
            value="go-developer-settings"
            onSelect={() => handleNavigate('/settings/developer')}
            className="cmdk-item"
          >
            <Code2 className="cmdk-icon" />
            <span className="cmdk-item-text">Developer Settings</span>
          </Command.Item>
          <Command.Item
            value="show-keyboard-shortcuts"
            onSelect={() => {
              setOpen(false)
              onShowKeyboardShortcuts?.()
            }}
            className="cmdk-item"
          >
            <Keyboard className="cmdk-icon" />
            <span className="cmdk-item-text">Keyboard Shortcuts</span>
            <kbd className="cmdk-shortcut">?</kbd>
          </Command.Item>
        </Command.Group>

        {/* Search Results - Papers */}
        {search && papers.length > 0 && (
          <Command.Group heading="Papers" className="cmdk-group">
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

        {/* Search Results - Projects */}
        {search && projects.length > 0 && (
          <Command.Group heading="Projects" className="cmdk-group">
            {projects
              .filter((p) =>
                p.name.toLowerCase().includes(search.toLowerCase())
              )
              .slice(0, 5)
              .map((project) => (
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

        {/* Search Results - Groups */}
        {search && groups.length > 0 && (
          <Command.Group heading="Groups" className="cmdk-group">
            {groups
              .filter((g) =>
                g.name.toLowerCase().includes(search.toLowerCase())
              )
              .slice(0, 5)
              .map((group) => (
                <Command.Item
                  key={group.id}
                  value={`group-${group.name}`}
                  onSelect={() => handleGroupSelect(group)}
                  className="cmdk-item"
                >
                  <UsersRound className="cmdk-icon" />
                  <span className="cmdk-item-text">{group.name}</span>
                  <span className="cmdk-badge">{group.member_count} members</span>
                </Command.Item>
              ))}
          </Command.Group>
        )}
      </Command.List>
    </Command.Dialog>
  )
}
