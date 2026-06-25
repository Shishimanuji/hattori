import React, { createContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { User, AuthContextType, AuthState } from '../types'
import { authService } from '../services/auth'

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUserState] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('user')
    
    if (storedToken && storedUser) {
      try {
        setTokenState(storedToken)
        setUserState(JSON.parse(storedUser))
      } catch (err) {
        console.error('Failed to parse stored user:', err)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
      }
    }
    
    setIsLoading(false)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await authService.login(username, password)

      localStorage.setItem('auth_token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      setTokenState(response.access_token)
      setUserState(response.user)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Login failed'
      setError(errorMsg)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Attempt to call the logout API endpoint
      await authService.logout()
    } catch (err) {
      // Log the error but continue with local cleanup
      console.error('Logout API error:', err)
      // Don't set error - we want to logout anyway
    } finally {
      // Always clear local state and token, regardless of API response
      setTokenState(null)
      setUserState(null)
      setError(null)
      setIsLoading(false)
      // Clear from localStorage through the service
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
    }
  }, [])

  const setUser = useCallback((newUser: User) => {
    setUserState(newUser)
    localStorage.setItem('user', JSON.stringify(newUser))
  }, [])

  const setToken = useCallback((newToken: string) => {
    setTokenState(newToken)
    localStorage.setItem('auth_token', newToken)
  }, [])

  const clearAuth = useCallback(() => {
    setTokenState(null)
    setUserState(null)
    setError(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }, [])

  const refreshToken = useCallback(async () => {
    try {
      const response = await authService.refreshToken()
      setTokenState(response.access_token)
      setUserState(response.user)
    } catch (err: any) {
      console.error('Token refresh failed:', err)
      // Clear auth on refresh failure (session expired)
      clearAuth()
      throw err
    }
  }, [clearAuth])

  const state: AuthState = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    error,
  }

  const value: AuthContextType = {
    state,
    user,
    token,
    isLoading,
    login,
    logout,
    setUser,
    setToken,
    clearAuth,
    refreshToken,
    isAuthenticated: !!token && !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
