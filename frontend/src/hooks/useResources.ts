import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { resourceService } from '../services/resources'
import { Resource, PaginationParams } from '../types'

/**
 * Hook to fetch resources with pagination
 */
export const useResources = (params?: PaginationParams) => {
  return useQuery({
    queryKey: ['resources', params],
    queryFn: () => resourceService.getResources(params),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  })
}

/**
 * Hook to fetch a single resource
 */
export const useResource = (id: string) => {
  return useQuery({
    queryKey: ['resource', id],
    queryFn: () => resourceService.getResource(id),
    enabled: !!id,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to fetch resource allocation history
 */
export const useResourceHistory = (id: string) => {
  return useQuery({
    queryKey: ['resourceHistory', id],
    queryFn: () => resourceService.getResourceHistory(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 60 seconds
    gcTime: 5 * 60 * 1000,
  })
}

/**
 * Hook to create a resource
 */
export const useCreateResource = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<Resource>) => resourceService.createResource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] })
    },
  })
}

/**
 * Hook to update a resource
 */
export const useUpdateResource = (resourceId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<Resource>) => resourceService.updateResource(resourceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource', resourceId] })
      queryClient.invalidateQueries({ queryKey: ['resources'] })
    },
  })
}

/**
 * Hook to delete a resource
 */
export const useDeleteResource = (resourceId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => resourceService.deleteResource(resourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource', resourceId] })
      queryClient.invalidateQueries({ queryKey: ['resources'] })
    },
  })
}
