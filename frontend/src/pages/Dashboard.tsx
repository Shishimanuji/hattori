import React, { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { ProjectOverviewCard } from '../components/Dashboard/ProjectOverviewCard'
import { ResourceDistributionChart } from '../components/Dashboard/ResourceDistributionChart'
import { UtilizationTrendChart } from '../components/Dashboard/UtilizationTrendChart'
import { BudgetVisualization } from '../components/Dashboard/BudgetVisualization'
import { MetricsCard } from '../components/Dashboard/MetricsCard'
import {
  useDashboardMetrics,
  useClearDashboardCache,
} from '../hooks/useDashboard'
import DashboardTabContent from '../components/Dashboard/DashboardTabContent'

type TabType = 'dashboard' | 'projects' | 'assets' | 'resources' | 'documents' | 'reports' | 'alerts' | 'administration'

const tabs: { id: TabType; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'projects', label: 'Projects', icon: '📁' },
  { id: 'assets', label: 'Assets', icon: '🖥️' },
  { id: 'resources', label: 'Resources', icon: '⚙️' },
  { id: 'documents', label: 'Documents', icon: '📄' },
  { id: 'reports', label: 'Reports', icon: '📈' },
  { id: 'alerts', label: 'Alerts', icon: '🔔' },
  { id: 'administration', label: 'Administration', icon: '⚡' },
]

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard')
  const { data: metrics, isLoading, error } = useDashboardMetrics()
  const { mutate: clearCache, isPending: isClearing } = useClearDashboardCache()

  React.useEffect(() => {
    console.log('Dashboard mounted')
    console.log('Metrics loading:', isLoading)
    console.log('Metrics data:', metrics)
    console.log('Metrics error:', error)
  }, [metrics, isLoading, error])

  const handleRefresh = () => {
    clearCache()
  }

  // Show loading state
  if (isLoading && !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error && !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-lg text-red-600 mb-2">Error loading dashboard</p>
          <p className="text-sm text-gray-600 mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-gray-900">Dashboard</h2>
              <p className="text-gray-600 text-sm mt-1">
                {metrics ? `Last updated: ${new Date(metrics.timestamp).toLocaleTimeString()}` : 'Loading...'}
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isClearing}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
              title="Refresh dashboard data"
            >
              <RefreshCw size={16} className={isClearing ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 font-medium text-sm whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Key Metrics Cards - Top Row */}
            {metrics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <MetricsCard
                  title="Total Projects"
                  value={metrics.projects.total_projects}
                  subtitle="Active projects"
                  className="p-3"
                />
                <MetricsCard
                  title="Total Resources"
                  value={metrics.resources.total_resources}
                  subtitle="Allocated resources"
                  className="p-3"
                />
                <MetricsCard
                  title="Budget Utilization"
                  value={`${metrics.projects.budget.avg_utilization.toFixed(1)}%`}
                  subtitle="Average utilization"
                  className="p-3"
                  trend={
                    metrics.projects.budget.avg_utilization >= 80 ? 'down' : 'up'
                  }
                  trendValue={
                    metrics.projects.budget.avg_utilization >= 80
                      ? 'Approaching limit'
                      : 'Within limits'
                  }
                />
                <MetricsCard
                  title="Active Status"
                  value={metrics.projects.by_status.active}
                  subtitle={`of ${metrics.projects.total_projects} projects`}
                  className="p-3"
                />
              </div>
            )}

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="space-y-4">
                <ProjectOverviewCard
                  data={metrics?.projects}
                  isLoading={isLoading}
                  error={error}
                />
                <ResourceDistributionChart
                  data={metrics?.resources}
                  isLoading={isLoading}
                  error={error}
                />
              </div>
              <div className="space-y-4">
                <BudgetVisualization
                  data={metrics?.budget_status}
                  isLoading={isLoading}
                  error={error}
                />
              </div>
            </div>

            {/* Utilization Trends */}
            <UtilizationTrendChart
              data={metrics?.trends}
              isLoading={isLoading}
              error={error}
            />
          </div>
        )}

        {activeTab !== 'dashboard' && (
          <DashboardTabContent
            tab={activeTab}
            isLoading={isLoading}
            error={error}
          />
        )}
      </div>
    </div>
  )
}

export default Dashboard
