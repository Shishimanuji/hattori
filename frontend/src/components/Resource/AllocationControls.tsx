import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { resourceService } from '../../services/resources'
import { AlertCircle, CheckCircle, AlertTriangle, Loader, X } from 'lucide-react'

interface AllocationControlsProps {
  projectId: string
  projectBudget: number
  allocatedBudget: number
  remainingBudget: number
  onAllocationChange?: () => void
  onDeallocate?: (resourceId: string) => void
}

/**
 * Format currency value
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value)
}

/**
 * Calculate utilization percentage
 */
function calculateUtilization(allocated: number, total: number): number {
  if (total === 0) return 0
  return Math.round((allocated / total) * 100)
}

/**
 * Get status indicator based on utilization
 */
function getStatusIndicator(percentage: number): {
  color: string
  bgColor: string
  icon: React.ReactNode
  label: string
  severity: 'none' | 'warning' | 'error'
} {
  if (percentage >= 100) {
    return {
      color: 'text-red-600',
      bgColor: 'bg-red-50 border-red-200',
      icon: <AlertCircle size={20} />,
      label: 'At Budget Limit',
      severity: 'error',
    }
  }
  if (percentage >= 80) {
    return {
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50 border-yellow-200',
      icon: <AlertTriangle size={20} />,
      label: 'Budget Warning (80%+)',
      severity: 'warning',
    }
  }
  return {
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <CheckCircle size={20} />,
    label: 'Budget Available',
    severity: 'none',
  }
}

export const AllocationControls: React.FC<AllocationControlsProps> = ({
  projectId,
  projectBudget,
  allocatedBudget,
  remainingBudget,
  onAllocationChange,
  onDeallocate,
}) => {
  const [showDeallocateForm, setShowDeallocateForm] = useState(false)
  const [deallocateResourceId, setDeallocateResourceId] = useState('')
  const [deallocateAmount, setDeallocateAmount] = useState(0)

  // Deallocate mutation
  const deallocateMutation = useMutation({
    mutationFn: async () => {
      // In a real implementation, this would call an API endpoint
      // For now, we'll simulate the deallocation
      return Promise.resolve({ success: true })
    },
    onSuccess: () => {
      setShowDeallocateForm(false)
      setDeallocateResourceId('')
      setDeallocateAmount(0)
      onDeallocate?.(deallocateResourceId)
      onAllocationChange?.()
    },
  })

  const utilizationPercentage = calculateUtilization(allocatedBudget, projectBudget)
  const status = getStatusIndicator(utilizationPercentage)

  return (
    <div className="space-y-6">
      {/* Budget Overview */}
      <div className={`rounded-lg border p-6 ${status.bgColor}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={status.color}>{status.icon}</div>
            <div>
              <h3 className={`text-lg font-semibold ${status.color}`}>{status.label}</h3>
              <p className="text-sm text-gray-600 mt-1">
                {utilizationPercentage}% of budget allocated
              </p>
            </div>
          </div>
          {utilizationPercentage >= 100 && (
            <span className="px-3 py-1 bg-red-600 text-white text-xs font-semibold rounded-full">
              FULL
            </span>
          )}
        </div>

        {/* Budget Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium text-gray-900">Budget Utilization</span>
            <span className="text-gray-600">
              {formatCurrency(allocatedBudget)} / {formatCurrency(projectBudget)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all ${
                utilizationPercentage >= 100
                  ? 'bg-red-600'
                  : utilizationPercentage >= 80
                    ? 'bg-yellow-500'
                    : 'bg-green-600'
              }`}
              style={{ width: `${Math.min(utilizationPercentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Budget Details Grid */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-300">
          <div>
            <p className="text-xs text-gray-600 uppercase tracking-wide">Allocated</p>
            <p className="text-lg font-bold text-gray-900 mt-1">
              {formatCurrency(allocatedBudget)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 uppercase tracking-wide">Remaining</p>
            <p className={`text-lg font-bold mt-1 ${remainingBudget > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(Math.max(0, remainingBudget))}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 uppercase tracking-wide">Total Budget</p>
            <p className="text-lg font-bold text-gray-900 mt-1">
              {formatCurrency(projectBudget)}
            </p>
          </div>
        </div>
      </div>

      {/* Budget Status Messages */}
      {utilizationPercentage >= 100 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <div>
              <h4 className="font-semibold text-red-900 mb-1">Budget Limit Reached</h4>
              <p className="text-red-700 text-sm">
                This project has reached its budget limit. No new resources can be allocated until
                budget is deallocated.
              </p>
            </div>
          </div>
        </div>
      )}

      {utilizationPercentage >= 80 && utilizationPercentage < 100 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertTriangle className="text-yellow-600 flex-shrink-0" size={20} />
            <div>
              <h4 className="font-semibold text-yellow-900 mb-1">Budget Warning</h4>
              <p className="text-yellow-700 text-sm">
                This project is {utilizationPercentage}% allocated. Consider deallocating unused
                resources or increasing the budget.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Deallocation Form */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Deallocate Resources</h3>

        {showDeallocateForm ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Resource ID to Deallocate *
              </label>
              <input
                type="text"
                value={deallocateResourceId}
                onChange={(e) => setDeallocateResourceId(e.target.value)}
                placeholder="Enter resource ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={deallocateMutation.isPending}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Deallocation Amount ($) *
              </label>
              <input
                type="number"
                value={deallocateAmount}
                onChange={(e) => setDeallocateAmount(parseFloat(e.target.value) || 0)}
                step="0.01"
                min="0"
                max={allocatedBudget}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={deallocateMutation.isPending}
              />
              <p className="text-xs text-gray-600 mt-1">
                Maximum: {formatCurrency(allocatedBudget)}
              </p>
            </div>

            {deallocateMutation.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">
                  {deallocateMutation.error instanceof Error
                    ? deallocateMutation.error.message
                    : 'Failed to deallocate resource'}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => {
                  setShowDeallocateForm(false)
                  setDeallocateResourceId('')
                  setDeallocateAmount(0)
                }}
                disabled={deallocateMutation.isPending}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => deallocateMutation.mutate()}
                disabled={
                  deallocateMutation.isPending ||
                  !deallocateResourceId ||
                  deallocateAmount <= 0
                }
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
              >
                {deallocateMutation.isPending && <Loader size={16} className="animate-spin" />}
                Deallocate
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowDeallocateForm(true)}
            className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            + Deallocate Resource
          </button>
        )}
      </div>

      {/* Deallocation Summary */}
      {allocatedBudget > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">Quick Reference</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Total Budget: {formatCurrency(projectBudget)}</li>
            <li>• Currently Allocated: {formatCurrency(allocatedBudget)}</li>
            <li>• Available for Allocation: {formatCurrency(Math.max(0, remainingBudget))}</li>
            <li>• Utilization: {utilizationPercentage}%</li>
          </ul>
        </div>
      )}
    </div>
  )
}
