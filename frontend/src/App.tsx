import '@/locales/i18n'
import { lazy, Suspense, useEffect, useMemo, useState, type ComponentType } from 'react'
import type { LazyExoticComponent } from 'react'
import { BrowserRouter, Routes, Route, useLocation, matchPath } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { SidebarProvider } from '@/contexts/SidebarContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Layout } from '@/components/layout'
import { ToastProvider } from '@/components/ui/Toast'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { CelebrationProvider } from '@/components/CelebrationOverlay'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { APP_ROUTE_META, APP_ROUTES } from '@/config/routes'
import { PageSkeleton } from '@/components/ui/PageSkeleton'

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

const ROUTE_COMPONENTS = Object.fromEntries(
  APP_ROUTES.map((route) => [route.path, lazy(route.loader)])
) as Record<string, LazyExoticComponent<ComponentType<object>>>

const PUBLIC_ROUTES = APP_ROUTES.filter((route) => !route.requiresAuth)
const PROTECTED_ROUTES = APP_ROUTES.filter((route) => route.requiresAuth)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      gcTime: 1000 * 60 * 10,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function AppContent() {
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false)
  const location = useLocation()
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()

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
      <Suspense fallback={<PageSkeleton />}>
        <Routes>
          {PUBLIC_ROUTES.map((route) => {
            const RouteComponent = ROUTE_COMPONENTS[route.path]
            return <Route key={route.path} path={route.path} element={<RouteComponent />} />
          })}

          <Route
            element={
              <ProtectedRoute>
                <SidebarProvider>
                  <Layout />
                </SidebarProvider>
              </ProtectedRoute>
            }
          >
            {PROTECTED_ROUTES.map((route) => {
              const RouteComponent = ROUTE_COMPONENTS[route.path]
              return <Route key={route.path} path={route.path} element={<RouteComponent />} />
            })}
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
