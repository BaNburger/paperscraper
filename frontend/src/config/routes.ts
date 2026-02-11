import type { LucideIcon } from 'lucide-react'
import {
  ArrowRightLeft,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Code2,
  FileText,
  FolderKanban,
  Home,
  Inbox,
  Search,
  Settings,
  Shield,
  Trophy,
  Users,
  UsersRound,
} from 'lucide-react'

export type NavGroup = 'main' | 'secondary' | 'mobile-settings'

export interface AppRouteMeta {
  path: string
  titleKey: string
  requiresAuth: boolean
  navGroup?: NavGroup
  navLabelKey?: string
  keyboardShortcut?: string
  showInCommandPalette?: boolean
}

export interface NavigationItem {
  path: string
  labelKey: string
  icon: LucideIcon
  desktopGroup?: 'main' | 'secondary'
  mobileBottom?: boolean
  mobileMenuGroup?: 'menu' | 'settings'
  adminOnly?: boolean
  commandPalette?: boolean
  shortcut?: string
}

export const APP_ROUTE_META: AppRouteMeta[] = [
  { path: '/login', titleKey: 'auth.signIn', requiresAuth: false },
  { path: '/register', titleKey: 'auth.createAccount', requiresAuth: false },
  { path: '/forgot-password', titleKey: 'auth.forgotPassword', requiresAuth: false },
  { path: '/reset-password', titleKey: 'auth.resetPassword', requiresAuth: false },
  { path: '/verify-email', titleKey: 'auth.verifyingEmail', requiresAuth: false },
  { path: '/accept-invite', titleKey: 'auth.acceptAndCreateAccount', requiresAuth: false },
  {
    path: '/',
    titleKey: 'nav.dashboard',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.dashboard',
    keyboardShortcut: 'g d',
    showInCommandPalette: true,
  },
  {
    path: '/dashboard',
    titleKey: 'nav.dashboard',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.dashboard',
    keyboardShortcut: 'g d',
    showInCommandPalette: true,
  },
  {
    path: '/papers',
    titleKey: 'nav.papers',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.papers',
    keyboardShortcut: 'g p',
    showInCommandPalette: true,
  },
  {
    path: '/projects',
    titleKey: 'nav.projects',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.projects',
    keyboardShortcut: 'g k',
    showInCommandPalette: true,
  },
  {
    path: '/search',
    titleKey: 'nav.search',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.search',
    keyboardShortcut: 'g s',
    showInCommandPalette: true,
  },
  {
    path: '/groups',
    titleKey: 'nav.groups',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.groups',
    keyboardShortcut: 'g g',
    showInCommandPalette: true,
  },
  {
    path: '/transfer',
    titleKey: 'nav.transfer',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.transfer',
    keyboardShortcut: 'g t',
    showInCommandPalette: true,
  },
  {
    path: '/submissions',
    titleKey: 'nav.submissions',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.submissions',
    showInCommandPalette: true,
  },
  {
    path: '/analytics',
    titleKey: 'nav.analytics',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.analytics',
    keyboardShortcut: 'g a',
    showInCommandPalette: true,
  },
  {
    path: '/alerts',
    titleKey: 'nav.alerts',
    requiresAuth: true,
    navGroup: 'main',
    navLabelKey: 'nav.alerts',
  },
  {
    path: '/badges',
    titleKey: 'nav.badges',
    requiresAuth: true,
    navGroup: 'secondary',
    navLabelKey: 'nav.badges',
    keyboardShortcut: 'g b',
    showInCommandPalette: true,
  },
  {
    path: '/team',
    titleKey: 'nav.team',
    requiresAuth: true,
    navGroup: 'secondary',
    navLabelKey: 'nav.team',
    showInCommandPalette: true,
  },
  {
    path: '/knowledge',
    titleKey: 'nav.knowledge',
    requiresAuth: true,
    navGroup: 'secondary',
    navLabelKey: 'nav.knowledge',
    showInCommandPalette: true,
  },
  {
    path: '/compliance',
    titleKey: 'nav.compliance',
    requiresAuth: true,
    navGroup: 'secondary',
    navLabelKey: 'nav.compliance',
  },
  {
    path: '/settings',
    titleKey: 'nav.settings',
    requiresAuth: true,
    navGroup: 'secondary',
    navLabelKey: 'nav.settings',
    showInCommandPalette: true,
  },
  {
    path: '/settings/organization',
    titleKey: 'orgSettings.title',
    requiresAuth: true,
    navGroup: 'mobile-settings',
    navLabelKey: 'orgSettings.title',
    showInCommandPalette: true,
  },
  {
    path: '/settings/models',
    titleKey: 'nav.aiModels',
    requiresAuth: true,
    navGroup: 'secondary',
    navLabelKey: 'nav.aiModels',
    showInCommandPalette: true,
  },
  {
    path: '/settings/developer',
    titleKey: 'devSettings.title',
    requiresAuth: true,
    navGroup: 'mobile-settings',
    navLabelKey: 'devSettings.title',
    showInCommandPalette: true,
  },
  { path: '/projects/:id', titleKey: 'projects.title', requiresAuth: true },
  { path: '/papers/:id', titleKey: 'papers.title', requiresAuth: true },
  { path: '/transfer/:id', titleKey: 'transfer.title', requiresAuth: true },
  { path: '/notifications', titleKey: 'notifications.title', requiresAuth: true },
]

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    path: '/',
    labelKey: 'nav.dashboard',
    icon: Home,
    desktopGroup: 'main',
    mobileBottom: true,
    commandPalette: true,
    shortcut: 'g d',
  },
  {
    path: '/papers',
    labelKey: 'nav.papers',
    icon: FileText,
    desktopGroup: 'main',
    mobileBottom: true,
    commandPalette: true,
    shortcut: 'g p',
  },
  {
    path: '/projects',
    labelKey: 'nav.projects',
    icon: FolderKanban,
    desktopGroup: 'main',
    mobileBottom: true,
    commandPalette: true,
    shortcut: 'g k',
  },
  {
    path: '/search',
    labelKey: 'nav.search',
    icon: Search,
    desktopGroup: 'main',
    mobileBottom: true,
    commandPalette: true,
    shortcut: 'g s',
  },
  {
    path: '/groups',
    labelKey: 'nav.groups',
    icon: UsersRound,
    desktopGroup: 'main',
    mobileMenuGroup: 'menu',
    commandPalette: true,
    shortcut: 'g g',
  },
  {
    path: '/transfer',
    labelKey: 'nav.transfer',
    icon: ArrowRightLeft,
    desktopGroup: 'main',
    mobileMenuGroup: 'menu',
    commandPalette: true,
    shortcut: 'g t',
  },
  {
    path: '/submissions',
    labelKey: 'nav.submissions',
    icon: Inbox,
    desktopGroup: 'main',
    mobileMenuGroup: 'menu',
    commandPalette: true,
  },
  {
    path: '/analytics',
    labelKey: 'nav.analytics',
    icon: BarChart3,
    desktopGroup: 'main',
    mobileMenuGroup: 'menu',
    commandPalette: true,
    shortcut: 'g a',
  },
  {
    path: '/alerts',
    labelKey: 'nav.alerts',
    icon: Bell,
    desktopGroup: 'main',
    mobileMenuGroup: 'menu',
  },
  {
    path: '/badges',
    labelKey: 'nav.badges',
    icon: Trophy,
    desktopGroup: 'secondary',
    mobileMenuGroup: 'menu',
    commandPalette: true,
    shortcut: 'g b',
  },
  {
    path: '/team',
    labelKey: 'nav.team',
    icon: Users,
    desktopGroup: 'secondary',
    mobileMenuGroup: 'menu',
    commandPalette: true,
  },
  {
    path: '/knowledge',
    labelKey: 'nav.knowledge',
    icon: BookOpen,
    desktopGroup: 'secondary',
    mobileMenuGroup: 'menu',
    commandPalette: true,
  },
  {
    path: '/compliance',
    labelKey: 'nav.compliance',
    icon: Shield,
    desktopGroup: 'secondary',
    mobileMenuGroup: 'menu',
  },
  {
    path: '/settings',
    labelKey: 'nav.settings',
    icon: Settings,
    desktopGroup: 'secondary',
    mobileMenuGroup: 'settings',
    commandPalette: true,
  },
  {
    path: '/settings/organization',
    labelKey: 'orgSettings.title',
    icon: Shield,
    mobileMenuGroup: 'settings',
    adminOnly: true,
    commandPalette: true,
  },
  {
    path: '/settings/models',
    labelKey: 'nav.aiModels',
    icon: Bot,
    desktopGroup: 'secondary',
    mobileMenuGroup: 'settings',
    commandPalette: true,
  },
  {
    path: '/settings/developer',
    labelKey: 'devSettings.title',
    icon: Code2,
    mobileMenuGroup: 'settings',
    commandPalette: true,
  },
]

export const COMMAND_PALETTE_ITEMS = NAVIGATION_ITEMS.filter((item) => item.commandPalette)
