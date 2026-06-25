import React from 'react'
import { AlertCircle, AlertTriangle, Loader } from 'lucide-react'

interface BudgetProject {
  project_id: string
  project_name: string
  total_budget: number
  allocated: number
  remaining: number
  utilization_percentage: number
}

interface BudgetVisualizationData {
  projects: BudgetProject[]
  warnings: BudgetProject[]
  critical: BudgetProject[]
  total_budget: number
  total_allocated: number
  total_remaining: number
}

interface BudgetVisualizationProps {
  data?: BudgetVisualizationData
  isLoading?: boolean
  error?: Error | null
}

const formatCurrency = (amount: number) => {
  return `$${amount.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`
}

const getUtilizationColor = (percentage: number) => {
  if (percentage >= 100) return 'bg-red-500'
  if (percentage >= 80) return 'bg-yellow-500'
  return 'bg-green-500'
}

const getUtilizationBadgeColor = (percentage: number) => {
  if (percentage >= 100) return 'bg-red-100 text-red-800'
  if (percentage >= 80) return 'bg-yellow-100 text-yellow-800'
  return 'bg-green-100 text-green-800'
}

export const BudgetVisualization: React.FC<BudgetVisualizationProps> = ({
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
          <span className="text-sm">Failed to load budget visualization</span>
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
      <div className="mb-4">
        <h2 className="text-base font-semibold text-gray-900">Budget Status</h2>
        <p className="text-xs text-gray-600 mt-1">Organization-wide budget allocation</p>
      </div>

      {/* Overall Budget Summary */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div>
            <p className="text-[10px] text-gray-600 mb-0.5">Total Budget</p>
            <p className="text-xl font-bold text-gray-900">
              {formatCurrency(data.total_budget)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-gray-600 mb-0.5">Allocated</p>
            <p className="text-xl font-bold text-blue-600">
              {formatCurrency(data.total_allocated)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-gray-600 mb-0.5">Remaining</p>
            <p className="text-xl font-bold text-green-600">
              {formatCurrency(data.total_remaining)}
            </p>
          </div>
        </div>

        {/* Overall allocation bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-600">Overall Allocation</span>
            <span className="font-medium text-gray-900">
              {data.total_budget > 0
                ? ((data.total_allocated / data.total_budget) * 100).toFixed(1)
                : 0}
              %
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all ${getUtilizationColor(
                data.total_budget > 0
                  ? (data.total_allocated / data.total_budget) * 100
                  : 0
              )}`}
              style={{
                width: `${Math.min(
                  (data.total_allocated / (data.total_budget || 1)) * 100,
                  100
                )}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Critical Projects */}
      {data.critical.length > 0 && (
        <div className="mb-4 pb-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={16} className="text-red-600" />
            <h3 className="text-xs font-semibold text-red-900">
              Critical ({data.critical.length})
            </h3>
          </div>
          <div className="space-y-2">
            {data.critical.map(project => (
              <div key={project.project_id} className="bg-red-50 rounded-lg p-2">
                <div className="flex justify-between items-start mb-1">
                  <p className="text-xs font-medium text-gray-900">{project.project_name}</p>
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${getUtilizationBadgeColor(project.utilization_percentage)}`}>
                    {project.utilization_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-1.5 rounded-full bg-red-500"
                    style={{
                      width: `${Math.min((project.allocated / project.total_budget) * 100, 100)}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-gray-600 mt-0.5">
                  <span>{formatCurrency(project.allocated)} allocated</span>
                  <span>{formatCurrency(project.total_budget)} budget</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warning Projects */}
      {data.warnings.length > 0 && (
        <div className="mb-4 pb-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-yellow-600" />
            <h3 className="text-xs font-semibold text-yellow-900">
              Warnings ({data.warnings.length})
            </h3>
          </div>
          <div className="space-y-2">
            {data.warnings.map(project => (
              <div key={project.project_id} className="bg-yellow-50 rounded-lg p-2">
                <div className="flex justify-between items-start mb-1">
                  <p className="text-xs font-medium text-gray-900">{project.project_name}</p>
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${getUtilizationBadgeColor(project.utilization_percentage)}`}>
                    {project.utilization_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-1.5 rounded-full bg-yellow-500"
                    style={{
                      width: `${(project.allocated / project.total_budget) * 100}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-gray-600 mt-0.5">
                  <span>{formatCurrency(project.allocated)} allocated</span>
                  <span>{formatCurrency(project.total_budget)} budget</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Healthy Projects Summary */}
      {data.projects.length > data.critical.length + data.warnings.length && (
        <div>
          <h3 className="text-xs font-semibold text-green-900 mb-1">
            Healthy Projects (
            {data.projects.length - data.critical.length - data.warnings.length})
          </h3>
          <p className="text-[10px] text-gray-600">
            {data.projects.length - data.critical.length - data.warnings.length} project
            {data.projects.length - data.critical.length - data.warnings.length !== 1 ? 's' : ''}{' '}
            with &lt;80% budget utilization
          </p>
        </div>
      )}
    </div>
  )
}
