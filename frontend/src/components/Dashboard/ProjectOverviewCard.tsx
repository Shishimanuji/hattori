import React from 'react'
import { Folder, AlertCircle, Loader } from 'lucide-react'

interface ProjectOverviewData {
  total_projects: number
  by_status: {
    active: number
    pending: number
    completed: number
    on_hold: number
  }
  budget: {
    total: number
    allocated: number
    remaining: number
    avg_utilization: number
  }
}

interface ProjectOverviewCardProps {
  data?: ProjectOverviewData
  isLoading?: boolean
  error?: Error | null
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'completed':
      return 'bg-blue-100 text-blue-800'
    case 'on_hold':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatCurrency = (amount: number) => {
  return `$${amount.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`
}

const formatStatus = (status: string) => {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export const ProjectOverviewCard: React.FC<ProjectOverviewCardProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center h-48">
          <Loader className="animate-spin text-gray-400" size={24} />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-3 text-red-600">
          <AlertCircle size={20} />
          <span className="text-sm">Failed to load project overview</span>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-600 text-sm">No data available</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 bg-blue-50 rounded-lg">
          <Folder className="text-blue-600" size={20} />
        </div>
        <div>
          <h2 className="text-base font-semibold text-gray-900">Project Overview</h2>
          <p className="text-xs text-gray-600">Active projects and budget status</p>
        </div>
      </div>

      {/* Total Projects */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-baseline gap-1 mb-1">
          <span className="text-2xl font-bold text-gray-900">{data.total_projects}</span>
          <span className="text-xs text-gray-600">Total Projects</span>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <h3 className="text-xs font-medium text-gray-700 mb-2">Projects by Status</h3>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(data.by_status).map(([status, count]) => (
            <div key={status} className={`rounded-lg p-2 ${getStatusColor(status)}`}>
              <p className="text-[10px] font-medium opacity-75">{formatStatus(status)}</p>
              <p className="text-base font-bold">{count}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Budget Summary */}
      <div>
        <h3 className="text-xs font-medium text-gray-700 mb-2">Budget Summary</h3>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-600">Total Budget:</span>
            <span className="font-medium text-gray-900">{formatCurrency(data.budget.total)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Allocated:</span>
            <span className="font-medium text-gray-900">{formatCurrency(data.budget.allocated)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Remaining:</span>
            <span className="font-medium text-gray-900">{formatCurrency(data.budget.remaining)}</span>
          </div>
          <div className="flex justify-between pt-1 border-t border-gray-200">
            <span className="text-gray-600">Avg Utilization:</span>
            <span className="font-medium text-gray-900">{data.budget.avg_utilization.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
