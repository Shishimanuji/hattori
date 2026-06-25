import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: 'Admin' | 'Manager' | 'Analyst' | 'Viewer'
}

/**
 * ProtectedRoute component restricts access to authenticated users only.
 * Optionally checks for specific role requirements.
 * If user is not authenticated or lacks required role, redirects to /login.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { isAuthenticated, user, isLoading } = useAuth()
  const location = useLocation()

  // Show loading state while auth is initializing
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Avoid redirect loop by only redirecting if we're not already on login page
    if (location.pathname !== '/login') {
      return <Navigate to="/login" replace />
    }
    return <>{children}</>
  }

  // Check role if required role is specified
  if (requiredRole && user?.role !== requiredRole) {
    // For now, redirect to login. In future, could show unauthorized page
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
