import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { resourceService } from '../../services/resources'
import { Resource, AllocationHistoryEntry } from '../../types'
import { Edit, Trash2, AlertCircle, Loader, ChevronLeft, X } from 'lucide-react'

interface ResourceDetailProps {
  resourceId: string
  onEdit: (resourceId: string) => void
  onDelete: (resourceId: string) => void
  onClose: () => void
}

/**
 * Format date to readable string
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
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
 * Get status badge color
 */
function getStatusBadgeColor(status: string): string {
  switch (status) {
    case 'Active':
      return 'bg-green-100 text-green-800'
    case 'Inactive':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export const ResourceDetail: React.FC<ResourceDetailProps> = ({
  resourceId,
  onEdit,
  onDelete,
  onClose,
}) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Fetch resource details
  const { data: resource, isLoading, error } = useQuery({
    queryKey: ['resource', resourceId],
    queryFn: () => resourceService.getResource(resourceId),
  })

  // Fetch allocation history
  const { data: historyData } = useQuery({
    queryKey: ['resourceHistory', resourceId],
    queryFn: () => resourceService.getResourceHistory(resourceId),
    enabled: !!resourceId,
  })

  // Delete mutation
  const deleteResource = useMutation({
    mutationFn: () => resourceService.deleteResource(resourceId),
    onSuccess: () => {
      onDelete(resourceId)
      onClose()
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader size={32} className="animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading resource details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Failed to load resource details</h3>
            <p className="text-red-700 text-sm mt-1">
              {error instanceof Error ? error.message : 'An error occurred'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!resource) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-600">Resource not found</p>
      </div>
    )
  }

  const allocationHistory = historyData?.data || resource.allocation_history || []

  return (
    <div className="space-y-6">
      {/* Header with close button */}
      <div className="flex items-center justify-between">
        <button
          onClick={onClose}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ChevronLeft size={20} />
          <span>Back</span>
        </button>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={24} />
        </button>
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 mb-2">Delete this resource?</h3>
              <p className="text-red-700 text-sm mb-4">
                This action will soft delete the resource. It can no longer be used in allocations.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={deleteResource.isPending}
                  className="px-4 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 hover:bg-red-100 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteResource.mutate()}
                  disabled={deleteResource.isPending}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                >
                  {deleteResource.isPending && <Loader size={16} className="animate-spin" />}
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Resource Information */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{resource.name}</h1>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(resource.status)}`}>
                {resource.status}
              </span>
              <span className="text-sm text-gray-600">ID: {resource.id.substring(0, 8)}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onEdit(resourceId)}
              disabled={deleteResource.isPending}
              className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
            >
              <Edit size={18} />
              Edit
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={deleteResource.isPending}
              className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              <Trash2 size={18} />
              Delete
            </button>
          </div>
        </div>

        {/* Main Details Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <label className="text-sm font-medium text-gray-600">Cost</label>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {formatCurrency(resource.cost)}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600">Asset Type ID</label>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {resource.asset_type_id.substring(0, 12)}...
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600">Allocation Date</label>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {formatDate(resource.allocation_date)}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-600">Project ID</label>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {resource.project_id.substring(0, 12)}...
            </p>
          </div>
        </div>

        {/* Created/Updated Info */}
        <div className="border-t border-gray-200 mt-6 pt-6 grid grid-cols-2 gap-6 text-sm text-gray-600">
          <div>
            <span className="font-medium">Created:</span>{' '}
            {formatDate(resource.created_at)}
          </div>
          <div>
            <span className="font-medium">Updated:</span>{' '}
            {formatDate(resource.updated_at)}
          </div>
        </div>
      </div>

      {/* Custom Fields */}
      {resource.custom_fields && Object.keys(resource.custom_fields).length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Custom Fields</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(resource.custom_fields).map(([key, value]) => (
              <div key={key}>
                <label className="text-sm font-medium text-gray-600 capitalize">
                  {key.replace(/_/g, ' ')}
                </label>
                <p className="text-lg text-gray-900 mt-1">
                  {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Allocation History */}
      {allocationHistory && allocationHistory.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Allocation History</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">
                    Allocated Date
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">
                    Deallocated Date
                  </th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-900">
                    Cost
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">
                    Created By
                  </th>
                </tr>
              </thead>
              <tbody>
                {allocationHistory.map((entry: AllocationHistoryEntry, idx: number) => (
                  <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900">
                      {formatDate(entry.allocation_date)}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {entry.deallocation_date
                        ? formatDate(entry.deallocation_date)
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900 font-medium">
                      {formatCurrency(entry.cost_at_allocation)}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {entry.created_by.substring(0, 8)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty allocation history */}
      {(!allocationHistory || allocationHistory.length === 0) && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
          <p className="text-gray-600">No allocation history available</p>
        </div>
      )}
    </div>
  )
}
