import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { Bell, Search, User, Settings } from 'lucide-react'
import './Navbar.css'

export const Navbar: React.FC<{ onMenuToggle: () => void }> = ({ onMenuToggle }) => {
  const navigate = useNavigate()
  const { state, logout } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const toggleUserMenu = () => {
    setShowUserMenu(!showUserMenu)
  }

  const handleLogout = async () => {
    if (!window.confirm('Are you sure you want to logout?')) {
      return
    }

    setIsLoggingOut(true)

    try {
      await logout()
      // Navigate to login page
      navigate('/login')
    } catch (error: any) {
      console.error('Logout error:', error)
      // Still navigate even on error
      navigate('/login')
    } finally {
      setIsLoggingOut(false)
      setShowUserMenu(false)
    }
  }

  // Only show navbar when authenticated
  if (!state.isAuthenticated) {
    return null
  }

  return (
    <nav className="top-bar">
      <div className="top-bar-left">
        {/* Mobile Menu Toggle */}
        <button
          className="menu-toggle"
          onClick={onMenuToggle}
          aria-label="Toggle sidebar"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        {/* Search Box */}
        <div className="search-box">
          <Search size={12} className="search-icon" />
          <input
            type="text"
            placeholder="Search..."
            className="search-input"
          />
        </div>
      </div>

      <div className="top-bar-right">
        {/* User Info */}
        <div className="user-info">
          <span className="user-role">{state.user?.role || 'User'}</span>
        </div>

        {/* Notifications */}
        <button className="notification-btn" aria-label="Notifications">
          <Bell size={20} />
          <span className="notification-badge">3</span>
        </button>

        {/* User Menu */}
        <div className="user-menu-container">
          <button
            className="user-menu-trigger"
            onClick={toggleUserMenu}
            aria-expanded={showUserMenu}
            aria-label="User menu"
          >
            <User size={20} />
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <div className="user-dropdown-menu">
              <div className="menu-header">
                <div className="user-info">
                  <p className="username">{state.user?.username}</p>
                  <p className="user-role">{state.user?.role}</p>
                </div>
              </div>

              <div className="menu-divider"></div>

              <div className="menu-items">
                <button
                  className="menu-item"
                  onClick={() => {
                    setShowUserMenu(false)
                    // Future: navigate to profile page
                  }}
                >
                  <User size={16} />
                  <span>View Profile</span>
                </button>

                <button
                  className="menu-item"
                  onClick={() => {
                    setShowUserMenu(false)
                    // Future: navigate to settings
                  }}
                >
                  <Settings size={16} />
                  <span>Settings</span>
                </button>
              </div>

              <div className="menu-divider"></div>

              <div className="menu-items">
                <button
                  className="menu-item logout-item"
                  onClick={handleLogout}
                  disabled={isLoggingOut}
                >
                  <span className="menu-icon">🚪</span>
                  <span>{isLoggingOut ? 'Logging out...' : 'Logout'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
