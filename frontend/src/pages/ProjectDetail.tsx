import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Edit2, Trash2, AlertCircle, Loader2 } from 'lucide-react'
import { projectService } from '../services/projects'
import { Project } from '../types'

const STATUS_COLORS = {
  'Active': 'bg-green-100 text-green-800 border-green-300',
  'Pending': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Completed': 'bg-blue-100 text-blue-800 border-blue-300',
  'On Hold': 'bg-gray-100 text-gray-800 border-gray-300',
} as const

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  if (!id) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-700">Invalid project ID</p>
      </div>
    )
  }

  // Fetch project details
  const { data: project, isLoading, error } = useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectService.getProject(id),
  })

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: () => projectService.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/projects', { replace: true })
    },
  })

  const handleDelete = () => {
    deleteProjectMutation.mutate()
  }

  const handleEdit = () => {
    navigate(`/projects/${id}/edit`, { state: { project } })
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-12">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2">
          <AlertCircle className="text-red-600" />
          <p className="text-red-700">Failed to load project details. Please try again.</p>
        </div>
      </div>
    )
  }

  const startDate = project.start_date
    ? new Date(project.start_date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Not set'

  const endDate = project.end_date
    ? new Date(project.end_date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Not set'

  const createdDate = new Date(project.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/projects')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={20} />
          Back to Projects
        </button>
        <div className="flex gap-2">
          <button
            onClick={handleEdit}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Edit2 size={20} />
            Edit
          </button>
          <button
            onClick={() => setDeleteConfirm(true)}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Trash2 size={20} />
            Delete
          </button>
        </div>
      </div>

      {/* Project Header Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{project.name}</h1>
            <p className="text-gray-600">{project.description || 'No description provided'}</p>
          </div>
          <span
            className={`inline-block px-4 py-2 rounded-full text-sm font-semibold border ${
              STATUS_COLORS[project.status as keyof typeof STATUS_COLORS] || STATUS_COLORS['Pending']
            }`}
          >
            {project.status}
          </span>
        </div>
        <p className="text-sm text-gray-500">Created on {createdDate}</p>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Budget Information */}
        <div className="lg:col-span-2 space-y-6">
          {/* Budget Details */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Budget Information</h2>
            <div className="space-y-4">
              {/* Total Budget */}
              <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                <span className="text-gray-600">Total Budget</span>
                <span className="text-xl font-semibold text-gray-900">
                  ${project.budget.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>

              {/* Allocated Budget */}
              <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                <span className="text-gray-600">Allocated Budget</span>
                <span className="text-xl font-semibold text-gray-900">
                  ${project.allocated_budget.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>

              {/* Remaining Budget */}
              <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                <span className="text-gray-600">Remaining Budget</span>
                <span className="text-xl font-semibold text-green-600">
                  ${(project.budget - project.allocated_budget).toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </div>

              {/* Utilization Percentage */}
              <div className="pt-2">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Budget Utilization</span>
                  <span
                    className={`text-lg font-semibold px-3 py-1 rounded ${
                      project.utilization_percentage >= 100
                        ? 'text-red-600 bg-red-50'
                        : project.utilization_percentage >= 80
                        ? 'text-yellow-600 bg-yellow-50'
                        : 'text-green-600 bg-green-50'
                    }`}
                  >
                    {project.utilization_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      project.utilization_percentage >= 100
                        ? 'bg-red-500'
                        : project.utilization_percentage >= 80
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{
                      width: `${Math.min(project.utilization_percentage, 100)}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Project Dates */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Timeline</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Start Date</label>
                <p className="text-lg font-medium text-gray-900">{startDate}</p>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">End Date</label>
                <p className="text-lg font-medium text-gray-900">{endDate}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right column - Resource Summary */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Resource Summary</h2>
          
          {/* Total Resources */}
          <div className="mb-6">
            <p className="text-sm text-gray-600 mb-1">Total Resources</p>
            <p className="text-3xl font-bold text-gray-900">{project.resource_count}</p>
          </div>

          {/* Resources by Type */}
          {project.resources_by_type && Object.keys(project.resources_by_type).length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-600 mb-3">Breakdown by Type</p>
              {Object.entries(project.resources_by_type).map(([type, count]) => (
                <div key={type} className="flex justify-between items-center pb-2 border-b border-gray-200">
                  <span className="text-gray-600">{type}</span>
                  <span className="font-semibold text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-gray-500 text-sm">No resources allocated yet</p>
              <button
                onClick={() => navigate(`/resources/create?project=${id}`)}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium mt-2"
              >
                Add resource
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Delete Project</h3>
            <p className="text-gray-600">
              Are you sure you want to delete <strong>{project.name}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirm(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteProjectMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {deleteProjectMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectDetail
