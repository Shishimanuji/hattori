import { apiClient } from './api'
import { Project, ProjectListResponse, PaginationParams } from '../types'

export const projectService = {
  getProjects: async (params?: PaginationParams): Promise<ProjectListResponse> => {
    const response = await apiClient.get<ProjectListResponse>('/projects', { params })
    return response.data
  },

  getProject: async (id: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${id}`)
    return response.data
  },

  createProject: async (data: Partial<Project>): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', data)
    return response.data
  },

  updateProject: async (id: string, data: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  deleteProject: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`)
  },

  getProjectResources: async (id: string, params?: PaginationParams) => {
    const response = await apiClient.get(`/projects/${id}/resources`, { params })
    return response.data
  },

  getProjectBudgetStatus: async (id: string) => {
    const response = await apiClient.get(`/projects/${id}/budget-status`)
    return response.data
  },
}
