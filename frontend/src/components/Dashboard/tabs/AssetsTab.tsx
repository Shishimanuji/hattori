import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Asset {
  id: string
  asset_code: string
  asset_name: string
  manufacturer: string
  model: string
  serial_number: string
  status: string
  audit_status: string
  cost: number
  warranty_end: string | null
  location: string
  created_at: string
}

interface AssetsResponse {
  total: number
  limit: number
  offset: number
  assets: Asset[]
}

const AssetsTab: React.FC = () => {
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-assets', offset, statusFilter, searchTerm],
    queryFn: async () => {
      const params: Record<string, any> = { limit, offset }
      if (statusFilter) params.status = statusFilter
      if (searchTerm) params.search = searchTerm

      const response = await axios.get<AssetsResponse>('/api/dashboard/tab/assets', { params })
      return response.data
    },
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading assets...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading assets</div>
  }

  const statusColors: Record<string, string> = {
    Active: 'bg-green-100 text-green-800',
    Inactive: 'bg-gray-100 text-gray-800',
    Disposed: 'bg-red-100 text-red-800',
    'Under Repair': 'bg-yellow-100 text-yellow-800',
    Reserved: 'bg-blue-100 text-blue-800',
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <input
          type="text"
          placeholder="Search by name, serial, or code..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value)
            setOffset(0)
          }}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={statusFilter || ''}
          onChange={(e) => {
            setStatusFilter(e.target.value || null)
            setOffset(0)
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="Active">Active</option>
          <option value="Inactive">Inactive</option>
          <option value="Disposed">Disposed</option>
          <option value="Under Repair">Under Repair</option>
          <option value="Reserved">Reserved</option>
        </select>
      </div>

      {/* Assets Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Manufacturer</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Serial</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Warranty End</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.assets && data.assets.length > 0 ? (
              data.assets.map((asset) => (
                <tr key={asset.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{asset.asset_code || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{asset.asset_name}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{asset.manufacturer || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{asset.serial_number || '-'}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[asset.status] || 'bg-gray-100'}`}>
                      {asset.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {asset.warranty_end ? new Date(asset.warranty_end).toLocaleDateString() : '-'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No assets found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">Showing {offset + 1} to {Math.min(offset + limit, data.total)} of {data.total}</p>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= data.total}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AssetsTab
