import React from 'react'
import ProjectsTab from './tabs/ProjectsTab'
import AssetsTab from './tabs/AssetsTab'
import ResourcesTab from './tabs/ResourcesTab'
import DocumentsTab from './tabs/DocumentsTab'
import ReportsTab from './tabs/ReportsTab'
import AlertsTab from './tabs/AlertsTab'
import AdministrationTab from './tabs/AdministrationTab'

type TabType = 'projects' | 'assets' | 'resources' | 'documents' | 'reports' | 'alerts' | 'administration'

interface DashboardTabContentProps {
  tab: TabType
  isLoading: boolean
  error: Error | null
}

const DashboardTabContent: React.FC<DashboardTabContentProps> = ({ tab, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">Error loading tab: {error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    )
  }

  switch (tab) {
    case 'projects':
      return <ProjectsTab />
    case 'assets':
      return <AssetsTab />
    case 'resources':
      return <ResourcesTab />
    case 'documents':
      return <DocumentsTab />
    case 'reports':
      return <ReportsTab />
    case 'alerts':
      return <AlertsTab />
    case 'administration':
      return <AdministrationTab />
    default:
      return <div>Unknown tab</div>
  }
}

export default DashboardTabContent
