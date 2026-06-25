import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { ResourceDetail as ResourceDetailComponent } from '../components/Resource/ResourceDetail'

const ResourceDetailPage: React.FC = () => {
  const navigate = useNavigate()
  const { resourceId } = useParams<{ resourceId: string }>()

  if (!resourceId) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">Error: Resource ID is required</p>
      </div>
    )
  }

  const handleEdit = (id: string) => {
    navigate(`/resources/${id}/edit`)
  }

  const handleDelete = () => {
    navigate('/resources', { replace: true })
  }

  const handleClose = () => {
    navigate(-1)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleClose}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ChevronLeft size={24} />
          <span>Back</span>
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Resource Details</h1>
      </div>

      {/* Detail Container */}
      <div className="max-w-4xl">
        <ResourceDetailComponent
          resourceId={resourceId}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onClose={handleClose}
        />
      </div>
    </div>
  )
}

export default ResourceDetailPage
