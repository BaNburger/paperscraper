import '@/locales/i18n'
import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { SidebarProvider } from '@/contexts/SidebarContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Layout } from '@/components/layout'
import { ToastProvider } from '@/components/ui/Toast'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { CommandPalette } from '@/components/CommandPalette'
import { KeyboardShortcutsDialog } from '@/components/KeyboardShortcutsDialog'
import { CelebrationProvider } from '@/components/CelebrationOverlay'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import {
  AnalyticsPage,
  BadgesPage,
  LoginPage,
  RegisterPage,
  DashboardPage,
  GroupsPage,
  KnowledgePage,
  PapersPage,
  PaperDetailPage,
  ProjectsPage,
  ProjectKanbanPage,
  SearchPage,
  SubmissionsPage,
  ForgotPasswordPage,
  ResetPasswordPage,
  TransferPage,
  TransferDetailPage,
  VerifyEmailPage,
  AcceptInvitePage,
  TeamMembersPage,
  UserSettingsPage,
  OrganizationSettingsPage,
  ModelSettingsPage,
  DeveloperSettingsPage,
  AlertsPage,
  NotificationsPage,
  CompliancePage,
} from '@/pages'

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

  // Enable keyboard shortcuts
  useKeyboardShortcuts(() => setShowKeyboardShortcuts(true))

  return (
    <>
      <CommandPalette onShowKeyboardShortcuts={() => setShowKeyboardShortcuts(true)} />
      <KeyboardShortcutsDialog
        open={showKeyboardShortcuts}
        onOpenChange={setShowKeyboardShortcuts}
      />
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
