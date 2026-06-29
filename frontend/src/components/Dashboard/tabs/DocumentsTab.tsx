import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

interface Document {
  id: string
  file_name: string
  document_type: string
  file_size: number
  mime_type: string
  uploaded_at: string
  description: string
  project_id: string | null
  asset_id: string | null
}

interface DocumentsResponse {
  total: number
  limit: number
  offset: number
  documents: Document[]
}

const DocumentsTab: React.FC = () => {
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [docTypeFilter, setDocTypeFilter] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-documents', offset, docTypeFilter],
    queryFn: async () => {
      const params: Record<string, any> = { limit, offset }
      if (docTypeFilter) params.doc_type = docTypeFilter

      const response = await axios.get<DocumentsResponse>('/api/dashboard/tab/documents', { params })
      return response.data
    },
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading documents...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading documents</div>
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <select
          value={docTypeFilter || ''}
          onChange={(e) => {
            setDocTypeFilter(e.target.value || null)
            setOffset(0)
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Types</option>
          <option value="Invoice">Invoice</option>
          <option value="Warranty">Warranty</option>
          <option value="Configuration">Configuration</option>
          <option value="Drawing">Drawing</option>
          <option value="Manual">Manual</option>
          <option value="Certificate">Certificate</option>
          <option value="Other">Other</option>
        </select>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">File Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Size</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Uploaded</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.documents && data.documents.length > 0 ? (
              data.documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{doc.file_name}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      {doc.document_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{formatFileSize(doc.file_size)}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 truncate">{doc.description || '-'}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No documents found
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

export default DocumentsTab
