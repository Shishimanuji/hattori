import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface AdminData {
  users: {
    total: number
    active: number
    inactive: number
  }
  projects: {
    total: number
    active: number
  }
  assets: {
    total: number
    by_status: Record<string, number>
  }
  audit_activity: {
    period_days: number
    operations: Record<string, number>
  }
  recent_audit_logs: Array<{
    id: string
    user_id: string | null
    operation: string
    entity_type: string
    status: string
    created_at: string
  }>
}

const AdministrationTab: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-administration'],
    queryFn: async () => {
      const response = await axios.get<AdminData>('/api/dashboard/tab/administration')
      return response.data
    },
    staleTime: 60000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading administration data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading administration data</div>
  }

  return (
    <div className="space-y-6">
      {/* System Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Users */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-2">Total Users</h3>
          <p className="text-3xl font-bold text-gray-900">{data?.users.total || 0}</p>
          <div className="mt-4 space-y-1 text-sm">
            <p className="text-green-600">
              <span className="font-semibold">{data?.users.active || 0}</span> active
            </p>
            <p className="text-gray-600">
              <span className="font-semibold">{data?.users.inactive || 0}</span> inactive
            </p>
          </div>
        </div>

        {/* Projects */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-2">Total Projects</h3>
          <p className="text-3xl font-bold text-gray-900">{data?.projects.total || 0}</p>
          <div className="mt-4 text-sm">
            <p className="text-blue-600">
              <span className="font-semibold">{data?.projects.active || 0}</span> active
            </p>
          </div>
        </div>

        {/* Assets */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-2">Total Assets</h3>
          <p className="text-3xl font-bold text-gray-900">{data?.assets.total || 0}</p>
        </div>

        {/* Audit Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium mb-2">Audit Activity</h3>
          <p className="text-3xl font-bold text-gray-900">
            {data?.audit_activity.operations ? Object.values(data.audit_activity.operations).reduce((a, b) => a + b, 0) : 0}
          </p>
          <p className="text-xs text-gray-500 mt-2">{data?.audit_activity.period_days || 30} days</p>
        </div>
      </div>

      {/* Asset Status Distribution */}
      {data?.assets.by_status && Object.keys(data.assets.by_status).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Distribution by Status</h3>
          <div className="space-y-3">
            {Object.entries(data.assets.by_status).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="text-gray-700">{status}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-600"
                      style={{
                        width: `${(count / (data.assets.total || 1)) * 100}%`,
                      }}
                    ></div>
                  </div>
                  <span className="text-gray-900 font-semibold min-w-12 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Operations */}
      {data?.audit_activity.operations && Object.keys(data.audit_activity.operations).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Audit Operations (Last {data.audit_activity.period_days} days)</h3>
          <div className="space-y-3">
            {Object.entries(data.audit_activity.operations).map(([operation, count]) => (
              <div key={operation} className="flex items-center justify-between">
                <span className="text-gray-700">{operation}</span>
                <span className="bg-gray-100 text-gray-900 px-3 py-1 rounded-full text-sm font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Audit Logs */}
      {data?.recent_audit_logs && data.recent_audit_logs.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Audit Logs</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Operation</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Entity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.recent_audit_logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{log.operation}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{log.entity_type}</td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          log.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdministrationTab
