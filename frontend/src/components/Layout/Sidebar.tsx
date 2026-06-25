import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Database,
  Network,
  Monitor,
  Package,
  Users,
  BarChart3,
  FileText,
  AlertTriangle,
  Settings,
  Menu,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import './Sidebar.css'

interface SidebarProps {
  isOpen: boolean
  toggleSidebar: () => void
}

interface SubmenuItem {
  id: string
  label: string
  path: string
  icon: React.ReactNode
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, toggleSidebar }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['infrastructure']))

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const handleNavigate = (path: string) => {
    navigate(path)
  }

  const isActive = (path: string) => location.pathname === path

  const infrastructureItems: SubmenuItem[] = [
    { id: 'dashboard', label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'infrastructure', label: 'Infrastructure', path: '/infrastructure', icon: <Network size={18} /> },
  ]

  const serversItems: SubmenuItem[] = [
    { id: 'servers', label: 'Servers', path: '/servers', icon: <Server size={18} /> },
    { id: 'storage', label: 'Storage', path: '/storage', icon: <Database size={18} /> },
    { id: 'network', label: 'Network Devices', path: '/network', icon: <Network size={18} /> },
    { id: 'workstations', label: 'Workstations', path: '/workstations', icon: <Monitor size={18} /> },
  ]

  const assetsItems: SubmenuItem[] = [
    { id: 'assets', label: 'Assets', path: '/assets', icon: <Package size={18} /> },
    { id: 'resources', label: 'Resources', path: '/resources', icon: <Users size={18} /> },
  ]

  const analyticsItems: SubmenuItem[] = [
    { id: 'analytics', label: 'Analytics', path: '/analytics', icon: <BarChart3 size={18} /> },
    { id: 'reports', label: 'Reports', path: '/reports', icon: <FileText size={18} /> },
  ]

  const alertsItems: SubmenuItem[] = [
    { id: 'alerts', label: 'Alerts', path: '/alerts', icon: <AlertTriangle size={18} /> },
  ]

  const adminItems: SubmenuItem[] = [
    { id: 'administration', label: 'Administration', path: '/administration', icon: <Settings size={18} /> },
  ]

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={toggleSidebar} />
      )}

      <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        {/* Header */}
        <div className="sidebar-header">
          <div className="logo">
            <h1>PRMS</h1>
          </div>
          <button className="toggle-btn" onClick={toggleSidebar} aria-label="Toggle sidebar">
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Navigation Menu */}
        <nav className="sidebar-menu">
          {/* Infrastructure Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('infrastructure')}
            >
              <span className="section-title">Infrastructure</span>
              {expandedSections.has('infrastructure') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('infrastructure') && (
              <div className="sidebar-submenu">
                {infrastructureItems.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-menu-item ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => handleNavigate(item.path)}
                  >
                    {item.icon}
                    <span className="menu-text">{item.label}</span>
                    {isActive(item.path) && <div className="menu-dot" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Servers Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('servers')}
            >
              <span className="section-title">Servers</span>
              {expandedSections.has('servers') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('servers') && (
              <div className="sidebar-submenu">
                {serversItems.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-menu-item ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => handleNavigate(item.path)}
                  >
                    {item.icon}
                    <span className="menu-text">{item.label}</span>
                    {isActive(item.path) && <div className="menu-dot" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Assets Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('assets')}
            >
              <span className="section-title">Assets</span>
              {expandedSections.has('assets') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('assets') && (
              <div className="sidebar-submenu">
                {assetsItems.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-menu-item ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => handleNavigate(item.path)}
                  >
                    {item.icon}
                    <span className="menu-text">{item.label}</span>
                    {isActive(item.path) && <div className="menu-dot" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Analytics Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('analytics')}
            >
              <span className="section-title">Analytics</span>
              {expandedSections.has('analytics') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('analytics') && (
              <div className="sidebar-submenu">
                {analyticsItems.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-menu-item ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => handleNavigate(item.path)}
                  >
                    {item.icon}
                    <span className="menu-text">{item.label}</span>
                    {isActive(item.path) && <div className="menu-dot" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Alerts Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('alerts')}
            >
              <span className="section-title">Alerts</span>
              {expandedSections.has('alerts') ? (
                <ChevronUp size={12} />
              ) : (
                <ChevronDown size={12} />
              )}
            </button>
            {expandedSections.has('alerts') && (
              <div className="sidebar-submenu">
                {alertsItems.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-menu-item ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => handleNavigate(item.path)}
                  >
                    {item.icon}
                    <span className="menu-text">{item.label}</span>
                    {isActive(item.path) && <div className="menu-dot" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Admin Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('admin')}
            >
              <span className="section-title">Administration</span>
              {expandedSections.has('admin') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('admin') && (
              <div className="sidebar-submenu">
                {adminItems.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-menu-item ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => handleNavigate(item.path)}
                  >
                    {item.icon}
                    <span className="menu-text">{item.label}</span>
                    {isActive(item.path) && <div className="menu-dot" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </nav>
      </div>
    </>
  )
}

export default Sidebar
