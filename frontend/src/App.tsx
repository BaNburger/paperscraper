import '@/locales/i18n'
import {
  lazy,
  Suspense,
  useEffect,
  useMemo,
  useState,
  type ComponentType,
} from 'react'
import type { LazyExoticComponent } from 'react'
import { BrowserRouter, Routes, Route, useLocation, matchPath } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { SidebarProvider } from '@/contexts/SidebarContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Layout } from '@/components/layout'
import { ToastProvider } from '@/components/ui/Toast'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { CelebrationProvider } from '@/components/CelebrationOverlay'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { useAuth } from '@/contexts/AuthContext'
import { APP_ROUTE_META } from '@/config/routes'

type ExtractLazyComponent<T> = T extends ComponentType<infer TProps>
  ? ComponentType<TProps>
  : ComponentType<object>

function lazyNamedImport<TModule, TKey extends keyof TModule>(
  importer: () => Promise<TModule>,
  key: TKey
): LazyExoticComponent<ExtractLazyComponent<TModule[TKey]>> {
  return lazy(async () => {
    const module = await importer()
    return {
      default: module[key] as ExtractLazyComponent<TModule[TKey]>,
    }
  })
}

const CommandPalette = lazyNamedImport(
  () => import('@/components/CommandPalette'),
  'CommandPalette'
)
const KeyboardShortcutsDialog = lazyNamedImport(
  () => import('@/components/KeyboardShortcutsDialog'),
  'KeyboardShortcutsDialog'
)

const LoginPage = lazyNamedImport(() => import('@/pages/LoginPage'), 'LoginPage')
const RegisterPage = lazyNamedImport(() => import('@/pages/RegisterPage'), 'RegisterPage')
const DashboardPage = lazyNamedImport(() => import('@/pages/DashboardPage'), 'DashboardPage')
const GroupsPage = lazyNamedImport(() => import('@/pages/GroupsPage'), 'GroupsPage')
const KnowledgePage = lazyNamedImport(() => import('@/pages/KnowledgePage'), 'KnowledgePage')
const PapersPage = lazyNamedImport(() => import('@/pages/PapersPage'), 'PapersPage')
const PaperDetailPage = lazyNamedImport(() => import('@/pages/PaperDetailPage'), 'PaperDetailPage')
const ProjectsPage = lazyNamedImport(() => import('@/pages/ProjectsPage'), 'ProjectsPage')
const ProjectKanbanPage = lazyNamedImport(
  () => import('@/pages/ProjectKanbanPage'),
  'ProjectKanbanPage'
)
const SearchPage = lazyNamedImport(() => import('@/pages/SearchPage'), 'SearchPage')
const SubmissionsPage = lazyNamedImport(() => import('@/pages/SubmissionsPage'), 'SubmissionsPage')
const ForgotPasswordPage = lazyNamedImport(
  () => import('@/pages/ForgotPasswordPage'),
  'ForgotPasswordPage'
)
const ResetPasswordPage = lazyNamedImport(() => import('@/pages/ResetPasswordPage'), 'ResetPasswordPage')
const TransferPage = lazyNamedImport(() => import('@/pages/TransferPage'), 'TransferPage')
const TransferDetailPage = lazyNamedImport(
  () => import('@/pages/TransferDetailPage'),
  'TransferDetailPage'
)
const VerifyEmailPage = lazyNamedImport(() => import('@/pages/VerifyEmailPage'), 'VerifyEmailPage')
const AcceptInvitePage = lazyNamedImport(
  () => import('@/pages/AcceptInvitePage'),
  'AcceptInvitePage'
)
const TeamMembersPage = lazyNamedImport(() => import('@/pages/TeamMembersPage'), 'TeamMembersPage')
const UserSettingsPage = lazyNamedImport(() => import('@/pages/UserSettingsPage'), 'UserSettingsPage')
const OrganizationSettingsPage = lazyNamedImport(
  () => import('@/pages/OrganizationSettingsPage'),
  'OrganizationSettingsPage'
)
const ModelSettingsPage = lazyNamedImport(() => import('@/pages/ModelSettingsPage'), 'ModelSettingsPage')
const DeveloperSettingsPage = lazyNamedImport(
  () => import('@/pages/DeveloperSettingsPage'),
  'DeveloperSettingsPage'
)
const AlertsPage = lazyNamedImport(() => import('@/pages/AlertsPage'), 'AlertsPage')
const NotificationsPage = lazyNamedImport(() => import('@/pages/NotificationsPage'), 'NotificationsPage')
const BadgesPage = lazyNamedImport(() => import('@/pages/BadgesPage'), 'BadgesPage')
const CompliancePage = lazyNamedImport(() => import('@/pages/CompliancePage'), 'CompliancePage')
const AnalyticsPage = lazyNamedImport(() => import('@/pages/AnalyticsPage'), 'AnalyticsPage')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
})

function AppContent() {
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false)
  const location = useLocation()
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()

  // Enable keyboard shortcuts
  useKeyboardShortcuts(() => setShowKeyboardShortcuts(true))

  const pageTitle = useMemo(() => {
    const route = APP_ROUTE_META.find((entry) => {
      if (entry.path === location.pathname) return true
      if (entry.path.includes(':')) {
        return !!matchPath({ path: entry.path, end: true }, location.pathname)
      }
      return false
    })

    if (!route) return 'Paper Scraper'
    return `${t(route.titleKey)} | Paper Scraper`
  }, [location.pathname, t])

  useEffect(() => {
    document.title = pageTitle
  }, [pageTitle])

  return (
    <>
      {isAuthenticated && (
        <Suspense fallback={null}>
          <CommandPalette onShowKeyboardShortcuts={() => setShowKeyboardShortcuts(true)} />
          <KeyboardShortcutsDialog
            open={showKeyboardShortcuts}
            onOpenChange={setShowKeyboardShortcuts}
          />
        </Suspense>
      )}
      <Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-r-transparent" />
          </div>
        }
      >
        <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/accept-invite" element={<AcceptInvitePage />} />

        {/* Protected routes */}
        <Route
          element={
            <ProtectedRoute>
              <SidebarProvider>
                <Layout />
              </SidebarProvider>
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/papers" element={<PapersPage />} />
          <Route path="/papers/:id" element={<PaperDetailPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:id" element={<ProjectKanbanPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/groups" element={<GroupsPage />} />
          <Route path="/transfer" element={<TransferPage />} />
          <Route path="/transfer/:id" element={<TransferDetailPage />} />
          <Route path="/submissions" element={<SubmissionsPage />} />
          <Route path="/badges" element={<BadgesPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/team" element={<TeamMembersPage />} />
          <Route path="/settings" element={<UserSettingsPage />} />
          <Route path="/settings/organization" element={<OrganizationSettingsPage />} />
          <Route path="/settings/models" element={<ModelSettingsPage />} />
          <Route path="/settings/developer" element={<DeveloperSettingsPage />} />
          <Route path="/compliance" element={<CompliancePage />} />
        </Route>
        </Routes>
      </Suspense>
    </>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <ToastProvider>
                <CelebrationProvider>
                  <AppContent />
                </CelebrationProvider>
              </ToastProvider>
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
