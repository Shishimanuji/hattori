import React from 'react'
import { AlertTriangle, AlertCircle } from 'lucide-react'

interface ProjectAllocationSummaryProps {
  totalBudget: number
  allocatedBudget: number
  remainingBudget?: number
  utilizationPercentage: number
  currency?: string
}

const ProjectAllocationSummary: React.FC<ProjectAllocationSummaryProps> = ({
  totalBudget,
  allocatedBudget,
  remainingBudget = totalBudget - allocatedBudget,
  utilizationPercentage,
  currency = 'USD',
}) => {
  const isWarning = utilizationPercentage >= 80 && utilizationPercentage < 100
  const isError = utilizationPercentage >= 100
  const isHealthy = utilizationPercentage < 80

  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const getBarColor = () => {
    if (isError) return 'bg-red-500'
    if (isWarning) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getStatusColor = () => {
    if (isError) return 'bg-red-50 border-red-200'
    if (isWarning) return 'bg-yellow-50 border-yellow-200'
    return 'bg-green-50 border-green-200'
  }

  const getTextColor = () => {
    if (isError) return 'text-red-800'
    if (isWarning) return 'text-yellow-800'
    return 'text-green-800'
  }

  return (
    <div className={`rounded-lg border p-6 ${getStatusColor()}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Budget Allocation</h3>
          <p className="text-sm text-gray-600 mt-1">Allocated vs Remaining budget overview</p>
        </div>
        {isError && (
          <div className="flex items-center gap-1 bg-red-100 px-3 py-1 rounded-full">
            <AlertCircle className="text-red-600" size={18} />
            <span className="text-sm font-medium text-red-800">Over Budget</span>
          </div>
        )}
        {isWarning && (
          <div className="flex items-center gap-1 bg-yellow-100 px-3 py-1 rounded-full">
            <AlertTriangle className="text-yellow-600" size={18} />
            <span className="text-sm font-medium text-yellow-800">Warning</span>
          </div>
        )}
      </div>

      {/* Budget Breakdown */}
      <div className="space-y-4 mb-6">
        {/* Allocated Budget Row */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <div>
              <p className="text-sm text-gray-700 font-medium">Allocated</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(allocatedBudget)}</p>
            </div>
            <p className="text-right">
              <p className="text-sm text-gray-600">of {formatCurrency(totalBudget)}</p>
              <p className={`text-lg font-semibold ${getTextColor()}`}>
                {((allocatedBudget / totalBudget) * 100).toFixed(1)}%
              </p>
            </p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-3 rounded-full transition-all ${getBarColor()}`}
              style={{
                width: `${Math.min((allocatedBudget / totalBudget) * 100, 100)}%`,
              }}
            />
          </div>
        </div>

        {/* Remaining Budget Row */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <div>
              <p className="text-sm text-gray-700 font-medium">Remaining</p>
              <p className={`text-2xl font-bold ${remainingBudget < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                {formatCurrency(Math.max(remainingBudget, 0))}
              </p>
            </div>
            <p className="text-right">
              <p className="text-sm text-gray-600">Available</p>
              <p className={`text-lg font-semibold ${remainingBudget < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {Math.max(((remainingBudget / totalBudget) * 100), 0).toFixed(1)}%
              </p>
            </p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="h-3 rounded-full bg-green-500 transition-all"
              style={{
                width: `${Math.max((remainingBudget / totalBudget) * 100, 0)}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="grid grid-cols-3 gap-4">
        {/* Total Budget */}
        <div className="bg-white bg-opacity-50 rounded p-3 text-center">
          <p className="text-xs text-gray-600 mb-1">Total Budget</p>
          <p className="text-lg font-semibold text-gray-900">{formatCurrency(totalBudget)}</p>
        </div>

        {/* Utilization */}
        <div className="bg-white bg-opacity-50 rounded p-3 text-center">
          <p className="text-xs text-gray-600 mb-1">Utilization</p>
          <p className={`text-lg font-semibold ${getTextColor()}`}>
            {utilizationPercentage.toFixed(1)}%
          </p>
        </div>

        {/* Currency */}
        <div className="bg-white bg-opacity-50 rounded p-3 text-center">
          <p className="text-xs text-gray-600 mb-1">Currency</p>
          <p className="text-lg font-semibold text-gray-900">{currency}</p>
        </div>
      </div>

      {/* Warning/Error Messages */}
      {isError && (
        <div className="mt-6 p-4 bg-red-100 border border-red-300 rounded-lg">
          <p className="text-sm font-medium text-red-800">
            🚨 <strong>Over Budget:</strong> The allocated budget exceeds the project budget. Please review and deallocate resources or increase the project budget.
          </p>
        </div>
      )}

      {isWarning && (
        <div className="mt-6 p-4 bg-yellow-100 border border-yellow-300 rounded-lg">
          <p className="text-sm font-medium text-yellow-800">
            ⚠️ <strong>Budget Warning:</strong> Budget utilization is at {utilizationPercentage.toFixed(1)}%. Consider reviewing resource allocations to avoid exceeding budget.
          </p>
        </div>
      )}
    </div>
  )
}

export default ProjectAllocationSummary
