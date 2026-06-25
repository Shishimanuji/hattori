import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, AlertCircle, Loader2 } from 'lucide-react'
import { projectService } from '../services/projects'
import { Project } from '../types'

interface FormErrors {
  [key: string]: string
}

interface FormData {
  name: string
  description: string
  status: 'Active' | 'Pending' | 'Completed' | 'On Hold'
  budget: string
  start_date: string
  end_date: string
}

const ProjectForm: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const isEditMode = !!id

  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    status: 'Active',
    budget: '',
    start_date: '',
    end_date: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})

  // Fetch project if editing
  const { data: project, isLoading } = useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectService.getProject(id!),
    enabled: isEditMode && !!id,
  })

  // Populate form on mount or when project data loads
  useEffect(() => {
    if (isEditMode && project) {
      setFormData({
        name: project.name,
        description: project.description || '',
        status: project.status as FormData['status'],
        budget: project.budget.toString(),
        start_date: project.start_date ? project.start_date.split('T')[0] : '',
        end_date: project.end_date ? project.end_date.split('T')[0] : '',
      })
    } else if (location.state?.project) {
      // Populate from location state if available
      const stateProject = location.state.project as Project
      setFormData({
        name: stateProject.name,
        description: stateProject.description || '',
        status: stateProject.status as FormData['status'],
        budget: stateProject.budget.toString(),
        start_date: stateProject.start_date ? stateProject.start_date.split('T')[0] : '',
        end_date: stateProject.end_date ? stateProject.end_date.split('T')[0] : '',
      })
    }
  }, [isEditMode, project, location.state?.project])

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async (data: Partial<Project>) => {
      if (isEditMode && id) {
        return projectService.updateProject(id, data)
      } else {
        return projectService.createProject(data)
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate(`/projects/${result.id}`, { replace: true })
    },
  })

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required'
    } else if (formData.name.length > 255) {
      newErrors.name = 'Project name must be 255 characters or less'
    }

    const budget = parseFloat(formData.budget)
    if (!formData.budget) {
      newErrors.budget = 'Budget is required'
    } else if (isNaN(budget) || budget < 0) {
      newErrors.budget = 'Budget must be a positive number'
    }

    if (formData.start_date && formData.end_date) {
      const startDate = new Date(formData.start_date)
      const endDate = new Date(formData.end_date)
      if (endDate < startDate) {
        newErrors.end_date = 'End date must be after start date'
      }
    }

    if (formData.description && formData.description.length > 1000) {
      newErrors.description = 'Description must be 1000 characters or less'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }))
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    const submitData: Partial<Project> = {
      name: formData.name.trim(),
      description: formData.description.trim(),
      status: formData.status,
      budget: parseFloat(formData.budget),
      ...(formData.start_date && { start_date: formData.start_date }),
      ...(formData.end_date && { end_date: formData.end_date }),
    }

    mutation.mutate(submitData)
  }

  if (isEditMode && isLoading) {
    return (
      <div className="flex justify-center items-center p-12">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/projects')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {isEditMode ? 'Edit Project' : 'Create Project'}
        </h1>
      </div>

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6 max-w-2xl">
        {/* API Error Alert */}
        {mutation.isError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertCircle className="text-red-600" size={20} />
            <p className="text-red-700">
              {mutation.error instanceof Error ? mutation.error.message : 'Failed to save project'}
            </p>
          </div>
        )}

        <div className="space-y-6">
          {/* Project Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-900 mb-2">
              Project Name <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter project name"
              maxLength={255}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                errors.name
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-300'
                  : 'border-gray-300 focus:ring-blue-500 focus:border-blue-300'
              }`}
            />
            {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-900 mb-2">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Enter project description (optional)"
              maxLength={1000}
              rows={4}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors resize-vertical ${
                errors.description
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-300'
                  : 'border-gray-300 focus:ring-blue-500 focus:border-blue-300'
              }`}
            />
            <p className="text-gray-500 text-sm mt-1">
              {formData.description.length}/1000 characters
            </p>
            {errors.description && <p className="text-red-600 text-sm mt-1">{errors.description}</p>}
          </div>

          {/* Status */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-900 mb-2">
              Status <span className="text-red-600">*</span>
            </label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-300"
            >
              <option value="Active">Active</option>
              <option value="Pending">Pending</option>
              <option value="Completed">Completed</option>
              <option value="On Hold">On Hold</option>
            </select>
          </div>

          {/* Budget */}
          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-gray-900 mb-2">
              Budget <span className="text-red-600">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-gray-600">$</span>
              <input
                type="number"
                id="budget"
                name="budget"
                value={formData.budget}
                onChange={handleChange}
                placeholder="0.00"
                min="0"
                step="0.01"
                className={`w-full pl-8 pr-3 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                  errors.budget
                    ? 'border-red-300 focus:ring-red-500 focus:border-red-300'
                    : 'border-gray-300 focus:ring-blue-500 focus:border-blue-300'
                }`}
              />
            </div>
            {errors.budget && <p className="text-red-600 text-sm mt-1">{errors.budget}</p>}
          </div>

          {/* Start Date */}
          <div>
            <label htmlFor="start_date" className="block text-sm font-medium text-gray-900 mb-2">
              Start Date
            </label>
            <input
              type="date"
              id="start_date"
              name="start_date"
              value={formData.start_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-300"
            />
          </div>

          {/* End Date */}
          <div>
            <label htmlFor="end_date" className="block text-sm font-medium text-gray-900 mb-2">
              End Date
            </label>
            <input
              type="date"
              id="end_date"
              name="end_date"
              value={formData.end_date}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                errors.end_date
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-300'
                  : 'border-gray-300 focus:ring-blue-500 focus:border-blue-300'
              }`}
            />
            {errors.end_date && <p className="text-red-600 text-sm mt-1">{errors.end_date}</p>}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => navigate('/projects')}
              className="px-6 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium flex items-center gap-2"
            >
              {mutation.isPending && <Loader2 size={18} className="animate-spin" />}
              {mutation.isPending ? 'Saving...' : isEditMode ? 'Update Project' : 'Create Project'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}

export default ProjectForm
