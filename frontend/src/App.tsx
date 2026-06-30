import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './store/authContext'
import { queryClient } from './store/queryClient'
import Dashboard from './pages/Dashboard'
import InfrastructureDashboard from './pages/InfrastructureDashboard'
import Login from './pages/Login'
import ProjectList from './pages/ProjectList'
import ProjectForm from './pages/ProjectForm'
import AssetList from './pages/AssetList'
import ProtectedRoute from './components/Common/ProtectedRoute'
import Navbar from './components/Layout/Navbar'
import Sidebar from './components/Layout/Sidebar'
import { useState } from 'react'
import './styles/globals.css'

// Layout component for protected pages
const ProtectedLayout = ({ children }: { children: React.ReactNode }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  return (
    <ProtectedRoute>
      <div className={`app-layout ${isSidebarOpen ? 'has-open-sidebar' : ''}`}>
        <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
        <div className="main-content">
          <Navbar onMenuToggle={toggleSidebar} />
          <main className="content-inner">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public route - Login */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected routes - require authentication */}
            <Route
              path="/dashboard/:tab?"
              element={
                <ProtectedLayout>
                  <Dashboard />
                </ProtectedLayout>
              }
            />
            
            <Route
              path="/infrastructure"
              element={
                <ProtectedLayout>
                  <InfrastructureDashboard />
                </ProtectedLayout>
              }
            />
            
            {/* Projects routes */}
            <Route
              path="/projects"
              element={
                <ProtectedLayout>
                  <ProjectList />
                </ProtectedLayout>
              }
            />
            
            <Route
              path="/projects/add"
              element={
                <ProtectedLayout>
                  <ProjectForm />
                </ProtectedLayout>
              }
            />
            
            <Route
              path="/assets"
              element={
                <ProtectedLayout>
                  <AssetList />
                </ProtectedLayout>
              }
            />
            
            {/* Catch all - redirect to login */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App