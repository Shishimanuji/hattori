import { apiClient } from './api'
import { AuthResponse, User } from '../types'

export const authService = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', {
      username,
      password,
    })
    
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }
    
    return response.data
  },

  logout: async (): Promise<void> => {
    try {
      // Call the logout API endpoint
      await apiClient.post('/auth/logout')
    } catch (error) {
      // Log the error but don't throw - we still want to clear local state
      console.error('Logout API error:', error)
      // Continue with local cleanup even if API fails
    } finally {
      // Always clear localStorage, regardless of API success/failure
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
    }
  },

  getCurrentUser: (): User | null => {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
  },

  getToken: (): string | null => {
    return localStorage.getItem('auth_token')
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token')
  },

  refreshToken: async (): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/refresh')
    
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }
    
    return response.data
  },
}
