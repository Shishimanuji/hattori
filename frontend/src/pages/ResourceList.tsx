import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { ResourceList as ResourceListComponent } from '../components/Resource/ResourceList'
import { resourceService } from '../services/resources'

const ResourceListPage: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const projectId = searchParams.get('projectId')

  // Delete resource mutation
  const deleteResourceMutation = useMutation({
    mutationFn: (id: string) => resourceService.deleteResource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] })
      setDeleteConfirmId(null)
    },
  })

  const handleEdit = (resourceId: string) => {
    navigate(`/resources/${resourceId}/edit`, {
      state: { projectId: projectId || undefined },
    })
  }

  const handleView = (resourceId: string) => {
    navigate(`/resources/${resourceId}`)
  }

  const handleDelete = (resourceId: string) => {
    setDeleteConfirmId(resourceId)
  }

  const confirmDelete = () => {
    if (deleteConfirmId) {
      deleteResourceMutation.mutate(deleteConfirmId)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Resources</h1>
          {projectId && (
            <p className="text-gray-600 text-sm mt-1">Project: {projectId.substring(0, 12)}...</p>
          )}
        </div>
        <button
          onClick={() =>
            navigate('/resources/create', {
              state: { projectId: projectId || undefined },
            })
          }
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={20} />
          Create Resource
        </button>
      </div>

      {/* Resource List Component */}
      <ResourceListComponent
        projectId={projectId || undefined}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onView={handleView}
      />

      {/* Delete Confirmation Dialog */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Delete Resource</h3>
            <p className="text-gray-600">
              Are you sure you want to delete this resource? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteResourceMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {deleteResourceMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResourceListPage
