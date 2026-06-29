import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Project {
  id: string
  name: string
  project_code: string
  status: string
  budget: number
  allocated_budget: number
  remaining_budget: number
  utilization_percentage: number
  client: string
  vendor: string
  location: string
  created_at: string
}

interface ProjectsResponse {
  total: number
  limit: number
  offset: number
  projects: Project[]
}

const ProjectsTab: React.FC = () => {
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-projects', offset, statusFilter, searchTerm],
    queryFn: async () => {
      const params: Record<string, any> = { limit, offset }
      if (statusFilter) params.status = statusFilter
      if (searchTerm) params.search = searchTerm

      const response = await axios.get<ProjectsResponse>('/api/dashboard/tab/projects', { params })
      return response.data
    },
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading projects...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading projects</div>
  }

  const statusColors: Record<string, string> = {
    Active: 'bg-green-100 text-green-800',
    Pending: 'bg-yellow-100 text-yellow-800',
    Completed: 'bg-blue-100 text-blue-800',
    'On Hold': 'bg-red-100 text-red-800',
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <input
          type="text"
          placeholder="Search by name or code..."
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
          <option value="Pending">Pending</option>
          <option value="Completed">Completed</option>
          <option value="On Hold">On Hold</option>
        </select>
      </div>

      {/* Projects Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Budget</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Utilization</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Client</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.projects && data.projects.length > 0 ? (
              data.projects.map((project) => (
                <tr key={project.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{project.project_code}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{project.name}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[project.status] || 'bg-gray-100'}`}>
                      {project.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">${project.budget.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            project.utilization_percentage >= 100
                              ? 'bg-red-600'
                              : project.utilization_percentage >= 80
                                ? 'bg-yellow-600'
                                : 'bg-green-600'
                          }`}
                          style={{ width: `${Math.min(project.utilization_percentage, 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600">{project.utilization_percentage.toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{project.client || '-'}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No projects found
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

export default ProjectsTab
