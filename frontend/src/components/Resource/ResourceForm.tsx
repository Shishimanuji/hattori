import React, { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { resourceService } from '../../services/resources'
import { assetTypeService } from '../../services/assetTypes'
import { Resource, CustomField, AssetType } from '../../types'
import { AlertCircle, Loader } from 'lucide-react'
import { CustomFieldInput } from '../Forms/CustomFieldInput'

interface ResourceFormProps {
  projectId: string
  resourceId?: string
  onSuccess: () => void
  onCancel: () => void
}

interface FormErrors {
  [key: string]: string
}

export const ResourceForm: React.FC<ResourceFormProps> = ({
  projectId,
  resourceId,
  onSuccess,
  onCancel,
}) => {
  const [formData, setFormData] = useState<Partial<Resource>>({
    project_id: projectId,
    name: '',
    cost: 0,
    allocation_date: new Date().toISOString().split('T')[0],
    status: 'Active',
    custom_fields: {},
  })

  const [selectedAssetType, setSelectedAssetType] = useState<string>('')
  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Fetch asset types
  const { data: assetTypesData, isLoading: assetTypesLoading } = useQuery({
    queryKey: ['assetTypes'],
    queryFn: () => assetTypeService.getAssetTypes({ limit: 100 }),
  })

  // Fetch selected asset type schema
  const { data: assetTypeSchema, isLoading: schemaLoading } = useQuery({
    queryKey: ['assetType', selectedAssetType],
    queryFn: () => assetTypeService.getAssetType(selectedAssetType),
    enabled: !!selectedAssetType,
  })

  // Fetch existing resource if in edit mode
  const { data: existingResource, isLoading: resourceLoading } = useQuery({
    queryKey: ['resource', resourceId],
    queryFn: () => resourceService.getResource(resourceId!),
    enabled: !!resourceId,
  })

  // Initialize form with existing resource data
  useEffect(() => {
    if (existingResource) {
      setFormData(existingResource)
      setSelectedAssetType(existingResource.asset_type_id)
    }
  }, [existingResource])

  // Create/update mutation
  const mutation = useMutation({
    mutationFn: async (data: Partial<Resource>) => {
      if (resourceId) {
        return resourceService.updateResource(resourceId, data)
      } else {
        return resourceService.createResource(data)
      }
    },
    onSuccess: () => {
      onSuccess()
    },
  })

  // Validate form
  const validateForm = (): boolean => {
    const errors: FormErrors = {}

    if (!formData.name?.trim()) {
      errors.name = 'Name is required'
    }

    if (!selectedAssetType) {
      errors.asset_type_id = 'Asset type is required'
    }

    if (!formData.cost || formData.cost <= 0) {
      errors.cost = 'Cost must be greater than 0'
    }

    if (!formData.allocation_date) {
      errors.allocation_date = 'Allocation date is required'
    }

    // Validate custom fields
    if (assetTypeSchema) {
      assetTypeSchema.custom_fields?.forEach((field: CustomField) => {
        const value = formData.custom_fields?.[field.name]
        if (field.is_required && !value) {
          errors[`custom_${field.name}`] = `${field.name} is required`
        }
      })
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    try {
      const submitData: Partial<Resource> = {
        ...formData,
        asset_type_id: selectedAssetType,
        project_id: projectId,
      }
      await mutation.mutateAsync(submitData)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle field change
  const handleFieldChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
    // Clear error for this field
    if (formErrors[field]) {
      const newErrors = { ...formErrors }
      delete newErrors[field]
      setFormErrors(newErrors)
    }
  }

  // Handle custom field change
  const handleCustomFieldChange = (fieldName: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      custom_fields: {
        ...prev.custom_fields,
        [fieldName]: value,
      },
    }))
    // Clear error for this field
    const errorKey = `custom_${fieldName}`
    if (formErrors[errorKey]) {
      const newErrors = { ...formErrors }
      delete newErrors[errorKey]
      setFormErrors(newErrors)
    }
  }

  const assetTypes = assetTypesData?.data || []
  const isLoading = assetTypesLoading || resourceLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader size={32} className="animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Summary */}
      {Object.keys(formErrors).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-red-900">Please fix the following errors:</h3>
              <ul className="mt-2 space-y-1 text-sm text-red-700">
                {Object.entries(formErrors).map(([key, error]) => (
                  <li key={key}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* API Error */}
      {mutation.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-red-900">Failed to save resource</h3>
              <p className="text-red-700 text-sm mt-1">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : 'An error occurred while saving'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Standard Fields */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Resource Information</h3>

        {/* Name Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Resource Name *
          </label>
          <input
            type="text"
            value={formData.name || ''}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
              formErrors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter resource name"
            disabled={isSubmitting}
          />
          {formErrors.name && <p className="text-red-600 text-sm mt-1">{formErrors.name}</p>}
        </div>

        {/* Asset Type Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Asset Type *
          </label>
          <select
            value={selectedAssetType}
            onChange={(e) => {
              setSelectedAssetType(e.target.value)
              handleFieldChange('asset_type_id', e.target.value)
            }}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
              formErrors.asset_type_id ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isSubmitting || !!resourceId}
          >
            <option value="">Select an asset type</option>
            {assetTypes.map((at: any) => (
              <option key={at.id} value={at.id}>
                {at.name}
              </option>
            ))}
          </select>
          {formErrors.asset_type_id && (
            <p className="text-red-600 text-sm mt-1">{formErrors.asset_type_id}</p>
          )}
        </div>

        {/* Cost Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cost ($) *</label>
          <input
            type="number"
            value={formData.cost || ''}
            onChange={(e) => handleFieldChange('cost', parseFloat(e.target.value) || 0)}
            step="0.01"
            min="0"
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
              formErrors.cost ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="0.00"
            disabled={isSubmitting}
          />
          {formErrors.cost && <p className="text-red-600 text-sm mt-1">{formErrors.cost}</p>}
        </div>

        {/* Allocation Date Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Allocation Date *
          </label>
          <input
            type="date"
            value={formData.allocation_date || ''}
            onChange={(e) => handleFieldChange('allocation_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
              formErrors.allocation_date ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isSubmitting}
          />
          {formErrors.allocation_date && (
            <p className="text-red-600 text-sm mt-1">{formErrors.allocation_date}</p>
          )}
        </div>

        {/* Status Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={formData.status || 'Active'}
            onChange={(e) => handleFieldChange('status', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            disabled={isSubmitting}
          >
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Custom Fields */}
      {assetTypeSchema && assetTypeSchema.custom_fields && assetTypeSchema.custom_fields.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Custom Fields</h3>

          {assetTypeSchema.custom_fields.map((field: CustomField) => (
            <div key={field.id}>
              <CustomFieldInput
                field={field}
                value={formData.custom_fields?.[field.name] || ''}
                onChange={(value) => handleCustomFieldChange(field.name, value)}
                disabled={isSubmitting}
                error={formErrors[`custom_${field.name}`]}
              />
            </div>
          ))}
        </div>
      )}

      {/* Form Actions */}
      <div className="flex gap-3 justify-end">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-6 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
        >
          {isSubmitting && <Loader size={16} className="animate-spin" />}
          {resourceId ? 'Update Resource' : 'Create Resource'}
        </button>
      </div>
    </form>
  )
}
