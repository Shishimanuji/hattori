import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Report {
  id: string
  report_name: string
  description: string
  is_public: boolean
  created_at: string
  filters: Record<string, any>
  columns: Record<string, any>
}

interface ReportsResponse {
  total: number
  limit: number
  offset: number
  reports: Report[]
}

const ReportsTab: React.FC = () => {
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-reports', offset],
    queryFn: async () => {
      const response = await axios.get<ReportsResponse>('/api/dashboard/tab/reports', {
        params: { limit, offset },
      })
      return response.data
    },
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading reports...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading reports</div>
  }

  return (
    <div className="space-y-4">
      {/* Reports Grid or List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.reports && data.reports.length > 0 ? (
          data.reports.map((report) => (
            <div key={report.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">{report.report_name}</h3>
                {report.is_public && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">Public</span>
                )}
              </div>
              <p className="text-gray-600 text-sm mb-4">{report.description || 'No description'}</p>
              <div className="text-xs text-gray-500 mb-4">
                Created: {report.created_at ? new Date(report.created_at).toLocaleDateString() : '-'}
              </div>
              <button className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium">
                Generate Report
              </button>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center text-gray-500 py-8">No reports available</div>
        )}
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

export default ReportsTab
