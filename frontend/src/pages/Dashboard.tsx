import React from 'react'
import { useParams } from 'react-router-dom'
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

const Dashboard: React.FC = () => {
  const { tab } = useParams<{ tab?: string }>()
  const [activeTab, setActiveTab] = React.useState<TabType>((tab as TabType) || 'dashboard')
  const { data: metrics, isLoading, error } = useDashboardMetrics()
  const { mutate: clearCache, isPending: isClearing } = useClearDashboardCache()

  // Sync URL parameter with local state
  React.useEffect(() => {
    if (tab && tab !== activeTab) {
      setActiveTab(tab as TabType)
    }
  }, [tab])

  React.useEffect(() => {
    console.log('Dashboard mounted')
    console.log('Metrics loading:', isLoading)
    console.log('Metrics data:', metrics)
    console.log('Metrics error:', error)
  }, [metrics, isLoading, error])

  const handleRefresh = () => {
    clearCache()
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
