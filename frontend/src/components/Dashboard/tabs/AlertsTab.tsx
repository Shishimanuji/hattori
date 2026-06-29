import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Alert {
  id: string
  title: string
  message: string
  alert_type: string
  severity: string
  status: string
  due_date: string | null
  created_at: string
  project_id: string | null
  asset_id: string | null
}

interface AlertsResponse {
  total: number
  limit: number
  offset: number
  severity_summary: Record<string, number>
  alerts: Alert[]
}

const AlertsTab: React.FC = () => {
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [severityFilter, setSeverityFilter] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-alerts', offset, severityFilter, statusFilter],
    queryFn: async () => {
      const params: Record<string, any> = { limit, offset }
      if (severityFilter) params.severity = severityFilter
      if (statusFilter) params.status = statusFilter

      const response = await axios.get<AlertsResponse>('/api/dashboard/tab/alerts', { params })
      return response.data
    },
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading alerts...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading alerts</div>
  }

  const severityColors: Record<string, string> = {
    Low: 'bg-blue-100 text-blue-800',
    Medium: 'bg-yellow-100 text-yellow-800',
    High: 'bg-orange-100 text-orange-800',
    Critical: 'bg-red-100 text-red-800',
  }

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      {data?.severity_summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-600 font-medium">Low</p>
            <p className="text-2xl font-bold text-blue-900">{data.severity_summary.low || 0}</p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-600 font-medium">Medium</p>
            <p className="text-2xl font-bold text-yellow-900">{data.severity_summary.medium || 0}</p>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <p className="text-sm text-orange-600 font-medium">High</p>
            <p className="text-2xl font-bold text-orange-900">{data.severity_summary.high || 0}</p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600 font-medium">Critical</p>
            <p className="text-2xl font-bold text-red-900">{data.severity_summary.critical || 0}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <select
          value={severityFilter || ''}
          onChange={(e) => {
            setSeverityFilter(e.target.value || null)
            setOffset(0)
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Severities</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
          <option value="Critical">Critical</option>
        </select>

        <select
          value={statusFilter || ''}
          onChange={(e) => {
            setStatusFilter(e.target.value || null)
            setOffset(0)
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Status</option>
          <option value="Active">Active</option>
          <option value="Acknowledged">Acknowledged</option>
          <option value="Resolved">Resolved</option>
          <option value="Dismissed">Dismissed</option>
        </select>
      </div>

      {/* Alerts Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Title</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Severity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Due Date</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.alerts && data.alerts.length > 0 ? (
              data.alerts.map((alert) => (
                <tr key={alert.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{alert.title}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{alert.alert_type}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${severityColors[alert.severity] || 'bg-gray-100'}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        alert.status === 'Active'
                          ? 'bg-red-100 text-red-800'
                          : alert.status === 'Acknowledged'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {alert.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {alert.due_date ? new Date(alert.due_date).toLocaleDateString() : '-'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No alerts found
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

export default AlertsTab
