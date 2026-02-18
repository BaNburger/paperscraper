import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { authApi } from '@/lib/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const queryClient = useQueryClient()

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await authApi.getMe()
        setUser(userData)
      } catch {
        setUser(null)
      }
      setIsLoading(false)
    }
    checkAuth()
  }, [])

  const login = async (data: LoginRequest) => {
    await authApi.login(data)
    const userData = await authApi.getMe()
    setUser(userData)
  }

  const register = async (data: RegisterRequest) => {
    await authApi.register(data)
    const userData = await authApi.getMe()
    setUser(userData)
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore logout API failures and clear client state anyway.
    }
    setUser(null)
    queryClient.clear()
  }

  const refreshUser = async () => {
    const userData = await authApi.getMe()
    setUser(userData)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
