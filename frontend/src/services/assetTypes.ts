import { apiClient } from './api'
import {
  AssetType,
  AssetTypeListResponse,
  AssetTypeDetailResponse,
  CustomField,
  PaginationParams,
} from '../types'

export const assetTypeService = {
  /**
   * Fetch all asset types with pagination
   */
  getAssetTypes: async (params?: PaginationParams): Promise<AssetTypeListResponse> => {
    const response = await apiClient.get<AssetTypeListResponse>('/asset-types', { params })
    // Normalize response to ensure 'data' field exists
    const data = response.data
    return {
      data: data.items || data.data || [],
      items: data.items || data.data || [],
      total: data.total || 0,
      page: data.page ?? 0,
      limit: data.limit || data.page_size || 50,
      page_size: data.page_size || data.limit || 50,
      hasMore: (data.page ?? 0) * (data.limit || data.page_size || 50) + (data.items?.length || data.data?.length || 0) < (data.total || 0),
    }
  },

  /**
   * Fetch a single asset type with all custom fields
   */
  getAssetType: async (id: string): Promise<AssetTypeDetailResponse> => {
    const response = await apiClient.get<AssetTypeDetailResponse>(`/asset-types/${id}`)
    return response.data
  },

  /**
   * Create a new asset type
   */
  createAssetType: async (data: Partial<AssetType>): Promise<AssetType> => {
    const response = await apiClient.post<AssetType>('/asset-types', data)
    return response.data
  },

  /**
   * Update an existing asset type
   */
  updateAssetType: async (id: string, data: Partial<AssetType>): Promise<AssetType> => {
    const response = await apiClient.put<AssetType>(`/asset-types/${id}`, data)
    return response.data
  },

  /**
   * Deactivate (soft delete) an asset type
   */
  deactivateAssetType: async (id: string): Promise<void> => {
    await apiClient.delete(`/asset-types/${id}`)
  },

  /**
   * Add a custom field to an asset type
   */
  addCustomField: async (
    assetTypeId: string,
    field: Partial<CustomField>
  ): Promise<CustomField> => {
    const response = await apiClient.post<CustomField>(
      `/asset-types/${assetTypeId}/fields`,
      field
    )
    return response.data
  },

  /**
   * Update a custom field
   */
  updateCustomField: async (
    assetTypeId: string,
    fieldId: string,
    data: Partial<CustomField>
  ): Promise<CustomField> => {
    const response = await apiClient.put<CustomField>(
      `/asset-types/${assetTypeId}/fields/${fieldId}`,
      data
    )
    return response.data
  },

  /**
   * Delete a custom field
   */
  deleteCustomField: async (assetTypeId: string, fieldId: string): Promise<void> => {
    await apiClient.delete(`/asset-types/${assetTypeId}/fields/${fieldId}`)
  },
}
