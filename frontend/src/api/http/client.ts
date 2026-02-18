import axios, { type InternalAxiosRequestConfig } from 'axios'

export const API_BASE_URL = '/api/v1'

export const PUBLIC_PATHS = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
  '/accept-invite',
]

export const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh']

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

export function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some((path) => pathname.startsWith(path))
}

export function isAuthEndpoint(url: string | undefined): boolean {
  return AUTH_ENDPOINTS.some((endpoint) => url?.includes(endpoint))
}

export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const cookie = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
  return cookie ? decodeURIComponent(cookie.split('=')[1]) : null
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const method = config.method?.toUpperCase() ?? 'GET'
  const isMutating = method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE'

  if (isMutating) {
    const csrfToken = getCookie('ps_csrf_token')
    if (csrfToken) {
      config.headers = config.headers ?? {}
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }

  return config
})
