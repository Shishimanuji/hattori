import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { assetTypeService } from '../services/assetTypes'
import { AssetTypeListResponse, AssetType, PaginationParams, CustomField } from '../types'

// Query key factory for asset types
const assetTypeKeys = {
  all: ['assetTypes'] as const,
  lists: () => [...assetTypeKeys.all, 'list'] as const,
  list: (params: PaginationParams) => [...assetTypeKeys.lists(), params] as const,
  details: () => [...assetTypeKeys.all, 'detail'] as const,
  detail: (id: string) => [...assetTypeKeys.details(), id] as const,
}

/**
 * Hook to fetch all asset types with pagination
 */
export const useAssetTypes = (params?: PaginationParams) => {
  return useQuery({
    queryKey: assetTypeKeys.list(params || {}),
    queryFn: () => assetTypeService.getAssetTypes(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  })
}

/**
 * Hook to fetch a single asset type with all its custom fields
 */
export const useAssetType = (id: string) => {
  return useQuery({
    queryKey: assetTypeKeys.detail(id),
    queryFn: () => assetTypeService.getAssetType(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

/**
 * Hook to create a new asset type
 */
export const useCreateAssetType = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<AssetType>) => assetTypeService.createAssetType(data),
    onSuccess: (newAssetType) => {
      // Invalidate the list to refetch with new asset type
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.lists() })
      // Add to cache
      queryClient.setQueryData(assetTypeKeys.detail(newAssetType.id), newAssetType)
    },
  })
}

/**
 * Hook to update an existing asset type
 */
export const useUpdateAssetType = (id: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<AssetType>) => assetTypeService.updateAssetType(id, data),
    onSuccess: (updatedAssetType) => {
      // Update the detail cache
      queryClient.setQueryData(assetTypeKeys.detail(id), updatedAssetType)
      // Invalidate the list to refetch
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.lists() })
    },
  })
}

/**
 * Hook to deactivate (soft delete) an asset type
 */
export const useDeactivateAssetType = (id: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => assetTypeService.deactivateAssetType(id),
    onSuccess: () => {
      // Invalidate all asset type queries
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.all })
    },
  })
}

/**
 * Hook to add a custom field to an asset type
 */
export const useAddCustomField = (assetTypeId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (field: Partial<CustomField>) =>
      assetTypeService.addCustomField(assetTypeId, field),
    onSuccess: () => {
      // Invalidate the asset type detail to refetch with new field
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.detail(assetTypeId) })
      // Invalidate list to update field count
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.lists() })
    },
  })
}

/**
 * Hook to update a custom field
 */
export const useUpdateCustomField = (assetTypeId: string, fieldId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<CustomField>) =>
      assetTypeService.updateCustomField(assetTypeId, fieldId, data),
    onSuccess: () => {
      // Invalidate the asset type detail
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.detail(assetTypeId) })
    },
  })
}

/**
 * Hook to delete a custom field
 */
export const useDeleteCustomField = (assetTypeId: string, fieldId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => assetTypeService.deleteCustomField(assetTypeId, fieldId),
    onSuccess: () => {
      // Invalidate the asset type detail to refetch without the deleted field
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.detail(assetTypeId) })
      // Invalidate list to update field count
      queryClient.invalidateQueries({ queryKey: assetTypeKeys.lists() })
    },
  })
}
