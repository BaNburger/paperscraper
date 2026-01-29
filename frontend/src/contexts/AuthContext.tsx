import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { authApi, getStoredToken, setStoredToken, removeStoredToken } from '@/lib/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const queryClient = useQueryClient()

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getStoredToken()
      if (token) {
        try {
          const userData = await authApi.getMe()
          setUser(userData)
        } catch {
          removeStoredToken()
        }
      }
      setIsLoading(false)
    }
    checkAuth()
  }, [])

  const login = async (data: LoginRequest) => {
    const tokens = await authApi.login(data)
    setStoredToken(tokens.access_token)
    const userData = await authApi.getMe()
    setUser(userData)
  }

  const register = async (data: RegisterRequest) => {
    // Register returns tokens directly - no need for separate login
    const tokens = await authApi.register(data)
    setStoredToken(tokens.access_token)
    const userData = await authApi.getMe()
    setUser(userData)
  }

  const logout = () => {
    removeStoredToken()
    setUser(null)
    queryClient.clear()
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
