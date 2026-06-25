import React from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { ResourceForm as ResourceFormComponent } from '../components/Resource/ResourceForm'

interface LocationState {
  projectId?: string
}

const ResourceFormPage: React.FC = () => {
  const navigate = useNavigate()
  const { resourceId } = useParams<{ resourceId?: string }>()
  const location = useLocation()
  const state = location.state as LocationState | undefined
  const projectId = state?.projectId || ''

  const handleSuccess = () => {
    navigate('/resources', { replace: true })
  }

  const handleCancel = () => {
    navigate(-1)
  }

  if (!projectId && !resourceId) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">Error: Project ID is required for creating resources</p>
        <button
          onClick={() => navigate('/projects')}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Go Back to Projects
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleCancel}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ChevronLeft size={24} />
          <span>Back</span>
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {resourceId ? 'Edit Resource' : 'Create Resource'}
          </h1>
          <p className="text-gray-600 text-sm mt-1">
            {projectId && `Project: ${projectId.substring(0, 12)}...`}
          </p>
        </div>
      </div>

      {/* Form Container */}
      <div className="max-w-2xl">
        <ResourceFormComponent
          projectId={projectId}
          resourceId={resourceId}
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>
    </div>
  )
}

export default ResourceFormPage
