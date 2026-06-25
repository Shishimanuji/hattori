import React from 'react'
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

const Dashboard: React.FC = () => {
  const { data: metrics, isLoading, error } = useDashboardMetrics()
  const { mutate: clearCache, isPending: isClearing } = useClearDashboardCache()

  // Debug logging
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
  if (isLoading) {
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
  if (error) {
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="space-y-6">
        {/* Header */}
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

        {/* Main Dashboard Grid - Responsive Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left Column */}
          <div className="space-y-4">
            {/* Project Overview Card */}
            <ProjectOverviewCard
              data={metrics?.projects}
              isLoading={isLoading}
              error={error}
            />

            {/* Resource Distribution Chart */}
            <ResourceDistributionChart
              data={metrics?.resources}
              isLoading={isLoading}
              error={error}
            />
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            {/* Budget Visualization */}
            <BudgetVisualization
              data={metrics?.budget_status}
              isLoading={isLoading}
              error={error}
            />
          </div>
        </div>

        {/* Utilization Trends - Full Width */}
        <UtilizationTrendChart
          data={metrics?.trends}
          isLoading={isLoading}
          error={error}
        />

        {/* Info Card */}
        {!metrics && !isLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">
              Welcome to PRMS Dashboard
            </h2>
            <p className="text-blue-800 mb-4">
              Here you can view comprehensive insights into your projects, resources, and budgets
              at a glance.
            </p>
            <ul className="space-y-2 text-sm text-blue-800">
              <li>✓ Monitor project status and budget utilization</li>
              <li>✓ Track resource allocation across all projects</li>
              <li>✓ Identify budget warnings and critical alerts</li>
              <li>✓ Analyze 30-day resource trends</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
