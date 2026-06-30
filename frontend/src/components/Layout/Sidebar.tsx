import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Database,
  Network,
  Monitor,
  Package,
  BarChart3,
  FileText,
  AlertTriangle,
  Settings,
  Menu,
  X,
  ChevronDown,
  ChevronUp,
  Plus,
  List
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
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['dashboard', 'projects']))

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

  const isActive = (path: string) => {
    // Check exact match or if current path starts with path + '/'
    if (location.pathname === path) return true
    if (location.pathname.startsWith(path + '/')) return true
    return false
  }

  // Check if any project submenu item is active
  const isProjectMenuActive = () => {
    return projectItems.some(item => isActive(item.path))
  }

  const dashboardItems: SubmenuItem[] = [
    { id: 'dashboard', label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'assets', label: 'Assets', path: '/dashboard/assets', icon: <Package size={18} /> },
    { id: 'resources', label: 'Resources', path: '/dashboard/resources', icon: <Database size={18} /> },
    { id: 'documents', label: 'Documents', path: '/dashboard/documents', icon: <FileText size={18} /> },
    { id: 'reports', label: 'Reports', path: '/dashboard/reports', icon: <BarChart3 size={18} /> },
    { id: 'alerts', label: 'Alerts', path: '/dashboard/alerts', icon: <AlertTriangle size={18} /> },
    { id: 'administration', label: 'Administration', path: '/dashboard/administration', icon: <Settings size={18} /> },
  ]

  const infrastructureItems: SubmenuItem[] = [
    { id: 'infrastructure', label: 'Infrastructure', path: '/infrastructure', icon: <Network size={18} /> },
  ]

  const serversItems: SubmenuItem[] = [
    { id: 'servers', label: 'Servers', path: '/servers', icon: <Server size={18} /> },
    { id: 'storage', label: 'Storage', path: '/storage', icon: <Database size={18} /> },
    { id: 'network', label: 'Network Devices', path: '/network', icon: <Network size={18} /> },
    { id: 'workstations', label: 'Workstations', path: '/workstations', icon: <Monitor size={18} /> },
  ]

  // Projects submenu items
  const projectItems: SubmenuItem[] = [
    { id: 'projects-list', label: 'Projects List', path: '/projects', icon: <List size={18} /> },
    { id: 'add-project', label: 'Add New Project', path: '/projects/add', icon: <Plus size={18} /> },
    { id: 'assets-list', label: 'Asset List', path: '/assets', icon: <Package size={18} /> },
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
          {/* Dashboard Section */}
          <div className="sidebar-section">
            <button
              className="sidebar-section-header"
              onClick={() => toggleSection('dashboard')}
            >
              <span className="section-title">Dashboard</span>
              {expandedSections.has('dashboard') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('dashboard') && (
              <div className="sidebar-submenu">
                {dashboardItems.map((item) => (
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

          {/* Projects Section */}
          <div className="sidebar-section">
            <button
              className={`sidebar-section-header ${isProjectMenuActive() ? 'active' : ''}`}
              onClick={() => toggleSection('projects')}
            >
              <span className="section-title">Projects</span>
              {expandedSections.has('projects') ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}
            </button>
            {expandedSections.has('projects') && (
              <div className="sidebar-submenu">
                {projectItems.map((item) => (
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
