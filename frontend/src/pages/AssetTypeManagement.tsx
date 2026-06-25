import React, { useState } from 'react'
import { Plus, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AssetTypeList } from '../components/AssetType/AssetTypeList'
import { AssetTypeListItem } from '../types'

const AssetTypeManagement: React.FC = () => {
  const navigate = useNavigate()
  const [editingAssetType, setEditingAssetType] = useState<AssetTypeListItem | null>(null)

  const handleEdit = (assetType: AssetTypeListItem) => {
    setEditingAssetType(assetType)
    // TODO: Open edit modal or navigate to edit page
    console.log('Edit asset type:', assetType)
  }

  const handleCreate = () => {
    setEditingAssetType(null)
    // TODO: Open create modal or navigate to create page
    console.log('Create new asset type')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Go back"
            >
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
            <h1 className="text-3xl font-bold text-gray-900">Asset Types</h1>
          </div>
          <p className="text-gray-600">Manage asset type definitions and custom fields</p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus size={20} />
          New Asset Type
        </button>
      </div>

      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-sm text-gray-600">
        <button
          onClick={() => navigate('/')}
          className="hover:text-gray-900 transition-colors"
        >
          Home
        </button>
        <span>/</span>
        <span className="text-gray-900 font-medium">Asset Types</span>
      </nav>

      {/* Asset Types List */}
      <AssetTypeList
        onEdit={handleEdit}
        onDeactivate={(id) => {
          // Reset editing state when an asset type is deactivated
          if (editingAssetType?.id === id) {
            setEditingAssetType(null)
          }
        }}
      />

      {/* TODO: Asset Type Form Modal/Page */}
      {editingAssetType && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-900">
            Asset type form for editing <strong>{editingAssetType.name}</strong> will be implemented
            in task 10.2
          </p>
        </div>
      )}
    </div>
  )
}

export default AssetTypeManagement
