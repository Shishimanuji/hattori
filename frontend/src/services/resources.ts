import { apiClient } from './api'
import { Resource, ResourceListResponse, PaginationParams } from '../types'

export const resourceService = {
  getResources: async (params?: PaginationParams): Promise<ResourceListResponse> => {
    const response = await apiClient.get<ResourceListResponse>('/resources', { params })
    return response.data
  },

  getResource: async (id: string): Promise<Resource> => {
    const response = await apiClient.get<Resource>(`/resources/${id}`)
    return response.data
  },

  createResource: async (data: Partial<Resource>): Promise<Resource> => {
    const response = await apiClient.post<Resource>('/resources', data)
    return response.data
  },

  updateResource: async (id: string, data: Partial<Resource>): Promise<Resource> => {
    const response = await apiClient.put<Resource>(`/resources/${id}`, data)
    return response.data
  },

  deleteResource: async (id: string): Promise<void> => {
    await apiClient.delete(`/resources/${id}`)
  },

  getResourceHistory: async (id: string) => {
    const response = await apiClient.get(`/resources/${id}/history`)
    return response.data
  },
}
