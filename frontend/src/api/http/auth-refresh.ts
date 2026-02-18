import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { navigateToLogin } from '@/lib/navigation'

import { API_BASE_URL, api, isAuthEndpoint, isPublicPath } from './client'

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean
}

type PendingRequest = {
  config: RetryableRequestConfig
  resolve: (value: unknown) => void
  reject: (reason?: unknown) => void
}

let isRefreshing = false
const pendingQueue: PendingRequest[] = []

function flushQueue(error?: unknown): void {
  while (pendingQueue.length > 0) {
    const pending = pendingQueue.shift()
    if (!pending) break

    if (error) {
      pending.reject(error)
      continue
    }

    api(pending.config)
      .then(pending.resolve)
      .catch(pending.reject)
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined

    if (error.response?.status !== 401 || !originalRequest || isAuthEndpoint(originalRequest.url)) {
      return Promise.reject(error)
    }

    if (originalRequest._retry) {
      navigateToLogin()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ config: originalRequest, resolve, reject })
      })
    }

    isRefreshing = true

    try {
      await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true, headers: { 'Content-Type': 'application/json' } },
      )

      flushQueue()
      return api(originalRequest)
    } catch (refreshError) {
      flushQueue(refreshError)
      if (typeof window !== 'undefined' && !isPublicPath(window.location.pathname)) {
        navigateToLogin()
      }
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  },
)
