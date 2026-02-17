import type { ComponentType } from 'react'
import type { LucideIcon } from 'lucide-react'
import {
  ArrowRightLeft,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  ClipboardCheck,
  Code2,
  Compass,
  FileText,
  Home,
  Inbox,
  LayoutDashboard,
  Search,
  Settings,
  Shield,
  Telescope,
  TrendingUp,
  Trophy,
  Users,
  UsersRound,
} from 'lucide-react'

export type NavGroup = 'main' | 'secondary' | 'mobile-settings'
export type SidebarGroup = 'discover' | 'evaluate' | 'transfer' | 'workspace' | 'settings'
export type RouteLoader = () => Promise<{ default: ComponentType<object> }>

export interface SidebarGroupDefinition {
  key: SidebarGroup
  labelKey: string
  icon: LucideIcon
}

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
  sidebarGroup?: SidebarGroup
  mobileBottom?: boolean
  mobileMenuGroup?: 'menu' | 'settings'
  adminOnly?: boolean
  commandPalette?: boolean
  shortcut?: string
  shortcutLabelKey?: string
  hidden?: boolean
}

export interface RouteDefinition {
  path: string
  titleKey: string
  requiresAuth: boolean
  loader: RouteLoader
  navigation?: Omit<NavigationItem, 'path'>
}

export interface NavigationShortcut {
  keys: string
  path: string
  labelKey: string
}

type RouteWithNavigation = RouteDefinition & { navigation: Omit<NavigationItem, 'path'> }

function hasVisibleNavigation(route: RouteDefinition): route is RouteWithNavigation {
  return !!route.navigation && !route.navigation.hidden
}

function hasShortcut(route: RouteDefinition): route is RouteWithNavigation {
  return !!route.navigation?.shortcut
}

const loadLoginPage: RouteLoader = () =>
  import('@/pages/LoginPage').then((mod) => ({ default: mod.LoginPage }))
const loadRegisterPage: RouteLoader = () =>
  import('@/pages/RegisterPage').then((mod) => ({ default: mod.RegisterPage }))
const loadForgotPasswordPage: RouteLoader = () =>
  import('@/pages/ForgotPasswordPage').then((mod) => ({ default: mod.ForgotPasswordPage }))
const loadResetPasswordPage: RouteLoader = () =>
  import('@/pages/ResetPasswordPage').then((mod) => ({ default: mod.ResetPasswordPage }))
const loadVerifyEmailPage: RouteLoader = () =>
  import('@/pages/VerifyEmailPage').then((mod) => ({ default: mod.VerifyEmailPage }))
const loadAcceptInvitePage: RouteLoader = () =>
  import('@/pages/AcceptInvitePage').then((mod) => ({ default: mod.AcceptInvitePage }))
const loadDashboardPage: RouteLoader = () =>
  import('@/pages/DashboardPage').then((mod) => ({ default: mod.DashboardPage }))
const loadAnalyticsPage: RouteLoader = () =>
  import('@/pages/AnalyticsPage').then((mod) => ({ default: mod.AnalyticsPage }))
const loadPapersPage: RouteLoader = () =>
  import('@/pages/PapersPage').then((mod) => ({ default: mod.PapersPage }))
const loadPaperDetailPage: RouteLoader = () =>
  import('@/pages/PaperDetailPage').then((mod) => ({ default: mod.PaperDetailPage }))
const loadProjectsPage: RouteLoader = () =>
  import('@/pages/ProjectsPage').then((mod) => ({ default: mod.ProjectsPage }))
const loadProjectKanbanPage: RouteLoader = () =>
  import('@/pages/ProjectKanbanPage').then((mod) => ({ default: mod.ProjectKanbanPage }))
const loadSearchPage: RouteLoader = () =>
  import('@/pages/SearchPage').then((mod) => ({ default: mod.SearchPage }))
const loadSavedSearchesPage: RouteLoader = () =>
  import('@/pages/SavedSearchesPage').then((mod) => ({ default: mod.SavedSearchesPage }))
const loadGroupsPage: RouteLoader = () =>
  import('@/pages/GroupsPage').then((mod) => ({ default: mod.GroupsPage }))
const loadTransferPage: RouteLoader = () =>
  import('@/pages/TransferPage').then((mod) => ({ default: mod.TransferPage }))
const loadTransferDetailPage: RouteLoader = () =>
  import('@/pages/TransferDetailPage').then((mod) => ({ default: mod.TransferDetailPage }))
const loadSubmissionsPage: RouteLoader = () =>
  import('@/pages/SubmissionsPage').then((mod) => ({ default: mod.SubmissionsPage }))
const loadBadgesPage: RouteLoader = () =>
  import('@/pages/BadgesPage').then((mod) => ({ default: mod.BadgesPage }))
const loadKnowledgePage: RouteLoader = () =>
  import('@/pages/KnowledgePage').then((mod) => ({ default: mod.KnowledgePage }))
const loadTrendsPage: RouteLoader = () =>
  import('@/pages/TrendsPage').then((mod) => ({ default: mod.TrendsPage }))
const loadTrendDetailPage: RouteLoader = () =>
  import('@/pages/TrendDetailPage').then((mod) => ({ default: mod.TrendDetailPage }))
const loadDiscoveryPage: RouteLoader = () =>
  import('@/pages/DiscoveryPage').then((mod) => ({ default: mod.DiscoveryPage }))
const loadAlertsPage: RouteLoader = () =>
  import('@/pages/AlertsPage').then((mod) => ({ default: mod.AlertsPage }))
const loadNotificationsPage: RouteLoader = () =>
  import('@/pages/NotificationsPage').then((mod) => ({ default: mod.NotificationsPage }))
const loadTeamMembersPage: RouteLoader = () =>
  import('@/pages/TeamMembersPage').then((mod) => ({ default: mod.TeamMembersPage }))
const loadUserSettingsPage: RouteLoader = () =>
  import('@/pages/UserSettingsPage').then((mod) => ({ default: mod.UserSettingsPage }))
const loadOrganizationSettingsPage: RouteLoader = () =>
  import('@/pages/OrganizationSettingsPage').then((mod) => ({ default: mod.OrganizationSettingsPage }))
const loadModelSettingsPage: RouteLoader = () =>
  import('@/pages/ModelSettingsPage').then((mod) => ({ default: mod.ModelSettingsPage }))
const loadDeveloperSettingsPage: RouteLoader = () =>
  import('@/pages/DeveloperSettingsPage').then((mod) => ({ default: mod.DeveloperSettingsPage }))
const loadCompliancePage: RouteLoader = () =>
  import('@/pages/CompliancePage').then((mod) => ({ default: mod.CompliancePage }))

export const SIDEBAR_GROUPS: SidebarGroupDefinition[] = [
  { key: 'discover', labelKey: 'nav.sidebarGroups.discover', icon: Telescope },
  { key: 'evaluate', labelKey: 'nav.sidebarGroups.evaluate', icon: ClipboardCheck },
  { key: 'transfer', labelKey: 'nav.sidebarGroups.transfer', icon: ArrowRightLeft },
  { key: 'workspace', labelKey: 'nav.sidebarGroups.workspace', icon: LayoutDashboard },
]

export const APP_ROUTES: RouteDefinition[] = [
  { path: '/login', titleKey: 'auth.signIn', requiresAuth: false, loader: loadLoginPage },
  { path: '/register', titleKey: 'auth.createAccount', requiresAuth: false, loader: loadRegisterPage },
  {
    path: '/forgot-password',
    titleKey: 'auth.forgotPassword',
    requiresAuth: false,
    loader: loadForgotPasswordPage,
  },
  {
    path: '/reset-password',
    titleKey: 'auth.resetPassword',
    requiresAuth: false,
    loader: loadResetPasswordPage,
  },
  {
    path: '/verify-email',
    titleKey: 'auth.verifyingEmail',
    requiresAuth: false,
    loader: loadVerifyEmailPage,
  },
  {
    path: '/accept-invite',
    titleKey: 'auth.acceptAndCreateAccount',
    requiresAuth: false,
    loader: loadAcceptInvitePage,
  },
  {
    path: '/',
    titleKey: 'nav.dashboard',
    requiresAuth: true,
    loader: loadDashboardPage,
    navigation: {
      labelKey: 'nav.dashboard',
      icon: Home,
      desktopGroup: 'main',
      sidebarGroup: 'workspace',
      mobileBottom: true,
      commandPalette: true,
      shortcut: 'g d',
      shortcutLabelKey: 'shortcuts.goToDashboard',
    },
  },
  {
    path: '/dashboard',
    titleKey: 'nav.dashboard',
    requiresAuth: true,
    loader: loadDashboardPage,
  },
  {
    path: '/analytics',
    titleKey: 'nav.analytics',
    requiresAuth: true,
    loader: loadAnalyticsPage,
    navigation: {
      labelKey: 'nav.analytics',
      icon: BarChart3,
      desktopGroup: 'main',
      sidebarGroup: 'evaluate',
      mobileMenuGroup: 'menu',
      commandPalette: true,
      shortcut: 'g a',
      shortcutLabelKey: 'shortcuts.goToAnalytics',
    },
  },
  {
    path: '/papers',
    titleKey: 'nav.papers',
    requiresAuth: true,
    loader: loadPapersPage,
    navigation: {
      labelKey: 'nav.papers',
      icon: FileText,
      desktopGroup: 'main',
      sidebarGroup: 'evaluate',
      mobileBottom: true,
      commandPalette: true,
      shortcut: 'g p',
      shortcutLabelKey: 'shortcuts.goToPapers',
    },
  },
  {
    path: '/papers/:id',
    titleKey: 'papers.title',
    requiresAuth: true,
    loader: loadPaperDetailPage,
  },
  {
    path: '/projects',
    titleKey: 'nav.projects',
    requiresAuth: true,
    loader: loadProjectsPage,
    navigation: {
      labelKey: 'nav.projects',
      icon: Users,
      desktopGroup: 'main',
      sidebarGroup: 'evaluate',
      mobileBottom: true,
      commandPalette: true,
      shortcut: 'g k',
      shortcutLabelKey: 'shortcuts.goToProjects',
    },
  },
  {
    path: '/projects/:id',
    titleKey: 'projects.title',
    requiresAuth: true,
    loader: loadProjectKanbanPage,
  },
  {
    path: '/search',
    titleKey: 'nav.search',
    requiresAuth: true,
    loader: loadSearchPage,
    navigation: {
      labelKey: 'nav.search',
      icon: Search,
      desktopGroup: 'main',
      sidebarGroup: 'discover',
      mobileBottom: true,
      commandPalette: true,
      shortcut: 'g s',
      shortcutLabelKey: 'shortcuts.goToSearch',
    },
  },
  {
    path: '/saved-searches',
    titleKey: 'savedSearches.title',
    requiresAuth: true,
    loader: loadSavedSearchesPage,
  },
  {
    path: '/groups',
    titleKey: 'nav.groups',
    requiresAuth: true,
    loader: loadGroupsPage,
    navigation: {
      labelKey: 'nav.groups',
      icon: UsersRound,
      desktopGroup: 'main',
      sidebarGroup: 'evaluate',
      mobileMenuGroup: 'menu',
      commandPalette: true,
      shortcut: 'g g',
      shortcutLabelKey: 'shortcuts.goToGroups',
    },
  },
  {
    path: '/transfer',
    titleKey: 'nav.transfer',
    requiresAuth: true,
    loader: loadTransferPage,
    navigation: {
      labelKey: 'nav.transfer',
      icon: ArrowRightLeft,
      desktopGroup: 'main',
      sidebarGroup: 'transfer',
      mobileMenuGroup: 'menu',
      commandPalette: true,
      shortcut: 'g t',
      shortcutLabelKey: 'shortcuts.goToTransfer',
    },
  },
  {
    path: '/transfer/:id',
    titleKey: 'transfer.title',
    requiresAuth: true,
    loader: loadTransferDetailPage,
  },
  {
    path: '/submissions',
    titleKey: 'nav.submissions',
    requiresAuth: true,
    loader: loadSubmissionsPage,
    navigation: {
      labelKey: 'nav.submissions',
      icon: Inbox,
      desktopGroup: 'main',
      sidebarGroup: 'transfer',
      mobileMenuGroup: 'menu',
      commandPalette: true,
    },
  },
  {
    path: '/badges',
    titleKey: 'nav.badges',
    requiresAuth: true,
    loader: loadBadgesPage,
    navigation: {
      labelKey: 'nav.badges',
      icon: Trophy,
      desktopGroup: 'secondary',
      sidebarGroup: 'workspace',
      mobileMenuGroup: 'menu',
      commandPalette: true,
      shortcut: 'g b',
      shortcutLabelKey: 'shortcuts.goToBadges',
    },
  },
  {
    path: '/knowledge',
    titleKey: 'nav.knowledge',
    requiresAuth: true,
    loader: loadKnowledgePage,
    navigation: {
      labelKey: 'nav.knowledge',
      icon: BookOpen,
      desktopGroup: 'secondary',
      sidebarGroup: 'workspace',
      mobileMenuGroup: 'menu',
      commandPalette: true,
    },
  },
  {
    path: '/trends',
    titleKey: 'nav.trends',
    requiresAuth: true,
    loader: loadTrendsPage,
    navigation: {
      labelKey: 'nav.trends',
      icon: TrendingUp,
      desktopGroup: 'main',
      sidebarGroup: 'discover',
      mobileMenuGroup: 'menu',
      commandPalette: true,
      shortcut: 'g r',
      shortcutLabelKey: 'shortcuts.goToTrends',
    },
  },
  {
    path: '/trends/:id',
    titleKey: 'trends.title',
    requiresAuth: true,
    loader: loadTrendDetailPage,
  },
  {
    path: '/discovery',
    titleKey: 'discovery.title',
    requiresAuth: true,
    loader: loadDiscoveryPage,
    navigation: {
      labelKey: 'nav.discovery',
      icon: Compass,
      desktopGroup: 'main',
      sidebarGroup: 'discover',
      mobileMenuGroup: 'menu',
      commandPalette: true,
    },
  },
  {
    path: '/alerts',
    titleKey: 'nav.alerts',
    requiresAuth: true,
    loader: loadAlertsPage,
    navigation: {
      labelKey: 'nav.alerts',
      icon: Bell,
      desktopGroup: 'main',
      sidebarGroup: 'discover',
      mobileMenuGroup: 'menu',
    },
  },
  {
    path: '/notifications',
    titleKey: 'notifications.title',
    requiresAuth: true,
    loader: loadNotificationsPage,
    navigation: {
      labelKey: 'notifications.title',
      icon: Bell,
      hidden: true,
      shortcut: 'g n',
      shortcutLabelKey: 'shortcuts.goToNotifications',
    },
  },
  {
    path: '/team',
    titleKey: 'nav.team',
    requiresAuth: true,
    loader: loadTeamMembersPage,
    navigation: {
      labelKey: 'nav.team',
      icon: Users,
      desktopGroup: 'secondary',
      sidebarGroup: 'workspace',
      mobileMenuGroup: 'menu',
      commandPalette: true,
    },
  },
  {
    path: '/settings',
    titleKey: 'nav.settings',
    requiresAuth: true,
    loader: loadUserSettingsPage,
    navigation: {
      labelKey: 'nav.settings',
      icon: Settings,
      desktopGroup: 'secondary',
      sidebarGroup: 'settings',
      mobileMenuGroup: 'settings',
      commandPalette: true,
    },
  },
  {
    path: '/settings/organization',
    titleKey: 'orgSettings.title',
    requiresAuth: true,
    loader: loadOrganizationSettingsPage,
    navigation: {
      labelKey: 'orgSettings.title',
      icon: Shield,
      sidebarGroup: 'settings',
      mobileMenuGroup: 'settings',
      adminOnly: true,
      commandPalette: true,
    },
  },
  {
    path: '/settings/models',
    titleKey: 'nav.aiModels',
    requiresAuth: true,
    loader: loadModelSettingsPage,
    navigation: {
      labelKey: 'nav.aiModels',
      icon: Bot,
      desktopGroup: 'secondary',
      sidebarGroup: 'settings',
      mobileMenuGroup: 'settings',
      commandPalette: true,
    },
  },
  {
    path: '/settings/developer',
    titleKey: 'devSettings.title',
    requiresAuth: true,
    loader: loadDeveloperSettingsPage,
    navigation: {
      labelKey: 'devSettings.title',
      icon: Code2,
      sidebarGroup: 'settings',
      mobileMenuGroup: 'settings',
      commandPalette: true,
    },
  },
  {
    path: '/compliance',
    titleKey: 'nav.compliance',
    requiresAuth: true,
    loader: loadCompliancePage,
    navigation: {
      labelKey: 'nav.compliance',
      icon: Shield,
      desktopGroup: 'secondary',
      sidebarGroup: 'workspace',
      mobileMenuGroup: 'menu',
    },
  },
]

const routeMap = new Map(APP_ROUTES.map((route) => [route.path, route]))

export function getRouteLoader(path: string): RouteLoader | undefined {
  return routeMap.get(path)?.loader
}

export const APP_ROUTE_META: AppRouteMeta[] = APP_ROUTES.map((route) => ({
  path: route.path,
  titleKey: route.titleKey,
  requiresAuth: route.requiresAuth,
  navGroup: route.navigation?.desktopGroup,
  navLabelKey: route.navigation?.labelKey,
  keyboardShortcut: route.navigation?.shortcut,
  showInCommandPalette: route.navigation?.commandPalette,
}))

export const NAVIGATION_ITEMS: NavigationItem[] = APP_ROUTES
  .filter(hasVisibleNavigation)
  .map((route) => ({
    path: route.path,
    ...route.navigation,
  }))

export const COMMAND_PALETTE_ITEMS = NAVIGATION_ITEMS.filter((item) => item.commandPalette)

export const NAVIGATION_SHORTCUTS: NavigationShortcut[] = APP_ROUTES
  .filter(hasShortcut)
  .map((route) => ({
    keys: route.navigation.shortcut ?? '',
    path: route.path,
    labelKey: route.navigation.shortcutLabelKey ?? route.navigation.labelKey ?? route.titleKey,
  }))
