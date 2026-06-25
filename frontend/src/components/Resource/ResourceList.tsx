import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { resourceService } from '../../services/resources'
import { Resource, AssetTypeListItem } from '../../types'
import { Edit, Trash2, AlertCircle, Loader, Eye, ChevronRight } from 'lucide-react'
import { useAssetTypes } from '../../hooks/useAssetTypes'

interface ResourceListProps {
  projectId?: string
  onEdit: (resourceId: string) => void
  onDelete?: (resourceId: string) => void
  onView?: (resourceId: string) => void
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

export const ResourceList: React.FC<ResourceListProps> = ({
  projectId,
  onEdit,
  onDelete,
  onView,
}) => {
  const [page, setPage] = useState(0)
  const [limit] = useState(10)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterAssetType, setFilterAssetType] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  // Fetch resources
  const { data, isLoading, error } = useQuery({
    queryKey: ['resources', { page, limit, projectId, searchTerm }],
    queryFn: async () => {
      const params: any = {
        page: page + 1,
        limit,
      }
      if (projectId) params.project_id = projectId
      if (searchTerm) params.search = searchTerm
      if (filterAssetType) params.asset_type_id = filterAssetType
      if (filterStatus) params.status = filterStatus

      return resourceService.getResources(params)
    },
    retry: 1,
  })

  // Fetch asset types for filter dropdown
  const { data: assetTypesData } = useQuery({
    queryKey: ['assetTypes', { limit: 100 }],
    queryFn: () => resourceService.getResources({ limit: 100 }),
    select: (data) => {
      // Extract unique asset types from resources
      const assetTypes = new Map<string, string>()
      data.data?.forEach((resource: Resource) => {
        if (resource.asset_type_id && !assetTypes.has(resource.asset_type_id)) {
          assetTypes.set(resource.asset_type_id, resource.asset_type_id)
        }
      })
      return Array.from(assetTypes.entries()).map(([id]) => ({
        id,
        name: id.substring(0, 20),
      }))
    },
  })

  const resources = data?.data || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / limit)

  // Filter resources by search term
  const filteredResources = resources.filter(
    (r) =>
      r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = (id: string) => {
    if (onDelete) {
      onDelete(id)
      setConfirmDeleteId(null)
    }
  }

  if (isLoading) {
    return <ResourceListSkeleton />
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Failed to load resources</h3>
            <p className="text-red-700 text-sm mt-1">
              {error instanceof Error ? error.message : 'An error occurred while loading resources'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search and filter controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            type="text"
            placeholder="Search by name..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value)
              setPage(0)
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Asset Type</label>
          <select
            value={filterAssetType}
            onChange={(e) => {
              setFilterAssetType(e.target.value)
              setPage(0)
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          >
            <option value="">All Types</option>
            {assetTypesData?.map((at) => (
              <option key={at.id} value={at.id}>
                {at.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value)
              setPage(0)
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          >
            <option value="">All Statuses</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={() => {
              setSearchTerm('')
              setFilterAssetType('')
              setFilterStatus('')
              setPage(0)
            }}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Empty state */}
      {filteredResources.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600">
            {searchTerm || filterAssetType || filterStatus
              ? 'No resources match your filters'
              : 'No resources available'}
          </p>
        </div>
      ) : (
        <>
          {/* Resources table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                    Asset Type
                  </th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                    Allocation Date
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                    Status
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredResources.map((resource) => (
                  <tr
                    key={resource.id}
                    className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{resource.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {resource.asset_type_id.substring(0, 8)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-gray-900 font-medium">
                      {formatCurrency(resource.cost)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {formatDate(resource.allocation_date)}
                    </td>
                    <td className="px-6 py-4 text-center text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(resource.status)}`}>
                        {resource.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {onView && (
                          <button
                            onClick={() => onView(resource.id)}
                            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            aria-label={`View ${resource.name}`}
                            title="View details"
                          >
                            <Eye size={18} />
                          </button>
                        )}
                        <button
                          onClick={() => onEdit(resource.id)}
                          className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          aria-label={`Edit ${resource.name}`}
                          title="Edit"
                        >
                          <Edit size={18} />
                        </button>
                        {onDelete && (
                          <button
                            onClick={() => setConfirmDeleteId(resource.id)}
                            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            aria-label={`Delete ${resource.name}`}
                            title="Delete"
                          >
                            <Trash2 size={18} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Page {page + 1} of {totalPages} ({total} total)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Deletion confirmation dialog */}
      {confirmDeleteId && (
        <ConfirmDeleteDialog
          resourceId={confirmDeleteId}
          resourceName={filteredResources.find((r) => r.id === confirmDeleteId)?.name || ''}
          onConfirm={() => handleDelete(confirmDeleteId)}
          onCancel={() => setConfirmDeleteId(null)}
        />
      )}
    </div>
  )
}

/**
 * Loading skeleton for resource list
 */
function ResourceListSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Asset Type</th>
            <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Cost</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
              Allocation Date
            </th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">Status</th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">Actions</th>
          </tr>
        </thead>
        <tbody>
          {[...Array(5)].map((_, i) => (
            <tr key={i} className="border-b border-gray-200">
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded w-32 animate-pulse" />
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded w-24 animate-pulse" />
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded w-24 mx-auto animate-pulse" />
              </td>
              <td className="px-6 py-4">
                <div className="h-4 bg-gray-200 rounded w-28 animate-pulse" />
              </td>
              <td className="px-6 py-4 text-center">
                <div className="h-4 bg-gray-200 rounded w-16 mx-auto animate-pulse" />
              </td>
              <td className="px-6 py-4 text-center">
                <div className="flex gap-2 justify-center">
                  <div className="h-8 bg-gray-200 rounded w-8 animate-pulse" />
                  <div className="h-8 bg-gray-200 rounded w-8 animate-pulse" />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * Confirmation dialog for deleting a resource
 */
interface ConfirmDeleteDialogProps {
  resourceId: string
  resourceName: string
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmDeleteDialog({
  resourceName,
  onConfirm,
  onCancel,
}: ConfirmDeleteDialogProps) {
  const [isDeleting, setIsDeleting] = React.useState(false)

  const handleConfirm = async () => {
    setIsDeleting(true)
    try {
      onConfirm()
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-lg">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Delete Resource?</h2>
        <p className="text-gray-600 text-sm mb-6">
          Are you sure you want to delete <strong>{resourceName}</strong>? This action will soft delete
          the resource and prevent it from being used in new allocations.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {isDeleting && <Loader size={16} className="animate-spin" />}
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
