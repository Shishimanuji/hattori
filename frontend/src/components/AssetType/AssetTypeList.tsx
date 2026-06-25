import React, { useState } from 'react'
import { useAssetTypes, useDeactivateAssetType } from '../../hooks/useAssetTypes'
import { AssetTypeListItem } from '../../types'
import { Edit, Trash2, AlertCircle, Loader } from 'lucide-react'

interface AssetTypeListProps {
  onEdit: (assetType: AssetTypeListItem) => void
  onDeactivate?: (assetTypeId: string) => void
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

export const AssetTypeList: React.FC<AssetTypeListProps> = ({ onEdit, onDeactivate }) => {
  const [page, setPage] = useState(0)
  const [showInactive, setShowInactive] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  // Fetch asset types
  const { data, isLoading, error } = useAssetTypes({
    page,
    limit: 10,
  })

  // Deactivate mutation
  const { mutate: deactivate, isPending: isDeactivating } = useDeactivateAssetType('')

  const assetTypes = data?.data || data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / 10)

  // Filter asset types by search term
  const filteredAssetTypes = assetTypes.filter((at) =>
    at.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (at.description && at.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const handleDeactivate = (id: string) => {
    deactivate(undefined, {
      onSuccess: () => {
        setConfirmDeleteId(null)
        onDeactivate?.(id)
      },
    })
  }

  if (isLoading) {
    return <AssetTypeListSkeleton />
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Failed to load asset types</h3>
            <p className="text-red-700 text-sm mt-1">
              {error instanceof Error ? error.message : 'An error occurred while loading asset types'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search and filter controls */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            type="text"
            placeholder="Search by name or description..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value)
              setPage(0)
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => {
              setShowInactive(e.target.checked)
              setPage(0)
            }}
            className="rounded"
          />
          <span className="text-sm text-gray-700">Show inactive</span>
        </label>
      </div>

      {/* Empty state */}
      {filteredAssetTypes.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600">
            {searchTerm ? 'No asset types match your search' : 'No asset types available'}
          </p>
        </div>
      ) : (
        <>
          {/* Asset types table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                    Description
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                    Fields
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                    Created
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
                {filteredAssetTypes.map((assetType) => (
                  <tr
                    key={assetType.id}
                    className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{assetType.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {assetType.description ? (
                        <span className="max-w-xs truncate block" title={assetType.description}>
                          {assetType.description}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-center text-gray-900">
                      <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {assetType.field_count || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {formatDate(assetType.created_at)}
                    </td>
                    <td className="px-6 py-4 text-center text-sm">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          assetType.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {assetType.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => onEdit(assetType)}
                          className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          aria-label={`Edit ${assetType.name}`}
                          title="Edit"
                        >
                          <Edit size={18} />
                        </button>
                        {assetType.is_active && (
                          <button
                            onClick={() => setConfirmDeleteId(assetType.id)}
                            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            aria-label={`Deactivate ${assetType.name}`}
                            title="Deactivate"
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

      {/* Deactivation confirmation dialog */}
      {confirmDeleteId && (
        <ConfirmDeactivateDialog
          assetTypeName={
            filteredAssetTypes.find((at) => at.id === confirmDeleteId)?.name || ''
          }
          onConfirm={() => handleDeactivate(confirmDeleteId)}
          onCancel={() => setConfirmDeleteId(null)}
          isLoading={isDeactivating}
        />
      )}
    </div>
  )
}

/**
 * Loading skeleton for asset type list
 */
function AssetTypeListSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Description</th>
            <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">Fields</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Created</th>
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
                <div className="h-4 bg-gray-200 rounded w-48 animate-pulse" />
              </td>
              <td className="px-6 py-4 text-center">
                <div className="h-4 bg-gray-200 rounded w-12 mx-auto animate-pulse" />
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
 * Confirmation dialog for deactivating an asset type
 */
interface ConfirmDeactivateDialogProps {
  assetTypeName: string
  onConfirm: () => void
  onCancel: () => void
  isLoading: boolean
}

function ConfirmDeactivateDialog({
  assetTypeName,
  onConfirm,
  onCancel,
  isLoading,
}: ConfirmDeactivateDialogProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm mx-4 shadow-lg">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Deactivate Asset Type?</h2>
        <p className="text-gray-600 text-sm mb-6">
          Are you sure you want to deactivate <strong>{assetTypeName}</strong>? This will prevent
          new resources from being created with this type, but existing resources will remain
          accessible.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {isLoading && <Loader size={16} className="animate-spin" />}
            Deactivate
          </button>
        </div>
      </div>
    </div>
  )
}
