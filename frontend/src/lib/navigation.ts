const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
  '/accept-invite',
]

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some((route) => pathname.startsWith(route))
}

export function navigateTo(path: string, options?: { replace?: boolean }): void {
  if (typeof window === 'undefined') return
  const target = path.startsWith('/') ? path : '/'
  if (options?.replace) {
    window.location.replace(target)
    return
  }
  window.location.assign(target)
}

export function navigateToLogin(): void {
  if (typeof window === 'undefined') return
  if (!isPublicRoute(window.location.pathname)) {
    navigateTo('/login')
  }
}
