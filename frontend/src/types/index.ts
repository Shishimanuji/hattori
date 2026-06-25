// Auth Types
export interface User {
  id: string
  username: string
  email: string
  role: 'Admin' | 'Manager' | 'Analyst' | 'Viewer'
  is_active: boolean
  last_login?: string
  created_at: string
  updated_at: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface AuthContextType {
  state: AuthState
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: User) => void
  setToken: (token: string) => void
  clearAuth: () => void
  refreshToken: () => Promise<void>
}

// Project Types
export interface Project {
  id: string
  name: string
  description: string
  status: 'Active' | 'Pending' | 'Completed' | 'On Hold'
  budget: number
  allocated_budget: number
  remaining_budget?: number
  utilization_percentage: number
  start_date: string
  end_date?: string
  owner_id: string
  resource_count: number
  resources_by_type?: Record<string, number>
  created_at: string
  updated_at: string
  deleted_at?: string | null
}

export interface ProjectListResponse {
  data: Project[]
  total: number
  page: number
  limit: number
}

// Resource Types
export interface Resource {
  id: string
  project_id: string
  asset_type_id: string
  name: string
  cost: number
  allocation_date: string
  status: 'Active' | 'Inactive'
  custom_fields?: Record<string, any>
  allocation_history?: AllocationHistoryEntry[]
  created_by: string
  created_at: string
  updated_at: string
  deleted_at?: string | null
}

export interface AllocationHistoryEntry {
  allocation_date: string
  deallocation_date?: string | null
  cost_at_allocation: number
  created_by: string
}

export interface ResourceListResponse {
  data: Resource[]
  total: number
  page: number
  limit: number
}

// Asset Type Types
export interface CustomField {
  id: string
  asset_type_id: string
  name: string
  field_type: 'text' | 'number' | 'date' | 'dropdown' | 'boolean'
  is_required: boolean
  options?: string[] | Record<string, any> // For dropdown types
  validation_rules?: Record<string, any>
  display_order: number
  created_at: string
  updated_at: string
}

export interface CustomFieldCreate {
  name: string
  field_type: 'text' | 'number' | 'date' | 'dropdown' | 'boolean'
  is_required?: boolean
  options?: string[] | Record<string, any>
  validation_rules?: Record<string, any>
  display_order?: number
}

export interface CustomFieldUpdate {
  name?: string
  field_type?: 'text' | 'number' | 'date' | 'dropdown' | 'boolean'
  is_required?: boolean
  options?: string[] | Record<string, any>
  validation_rules?: Record<string, any>
  display_order?: number
}

export interface AssetType {
  id: string
  name: string
  description?: string
  is_active: boolean
  field_count?: number
  standard_fields?: Array<{
    name: string
    type: string
    required: boolean
  }>
  custom_fields: CustomField[]
  created_at: string
  updated_at: string
}

export interface AssetTypeCreate {
  name: string
  description?: string
  custom_fields?: CustomFieldCreate[]
}

export interface AssetTypeUpdate {
  name?: string
  description?: string | null
  is_active?: boolean
}

export interface AssetTypeListItem {
  id: string
  name: string
  description?: string
  is_active: boolean
  field_count: number
  created_at: string
  updated_at: string
}

export interface AssetTypeListResponse {
  data: AssetTypeListItem[]
  items?: AssetTypeListItem[]
  total: number
  page: number
  limit: number
  page_size?: number
  hasMore?: boolean
}

export interface AssetTypeDetailResponse {
  id: string
  name: string
  description?: string
  is_active: boolean
  field_count: number
  custom_fields: CustomField[]
  created_at: string
  updated_at: string
}

// Dashboard Types
export interface DashboardMetrics {
  total_projects: number
  total_resources: number
  total_budget: number
  allocated_budget: number
  projects: Project[]
  resource_distribution: Record<string, number>
  utilization_trend: UtilizationTrendPoint[]
  budget_status: BudgetStatus
}

export interface UtilizationTrendPoint {
  date: string
  [key: string]: string | number // resource type counts
}

export interface BudgetStatus {
  total_budget: number
  allocated_budget: number
  remaining_budget: number
  utilization_percentage: number
  at_80_percent: boolean
  at_100_percent: boolean
}

export interface ProjectOverviewCardProps {
  project: Project
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
}

export interface ChartDataPoint {
  name: string
  value: number
}

// API Error Types
export interface ApiError {
  error: string
  code: string
  details?: string
  timestamp: string
}

// Pagination Types
export interface PaginationParams {
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface ListResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

// Import Types
export interface ImportPreviewResponse {
  rows: Array<Record<string, any>>
  total_rows: number
  error_count: number
  errors?: Array<{
    row_number: number
    field: string
    error: string
  }>
}

export interface ImportExecuteRequest {
  file_path: string
  project_id: string
  asset_type_id: string
}

export interface ImportStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress_percent: number
  imported_count: number
  error_count: number
  total_records: number
  errors?: Array<{
    row_number: number
    error: string
  }>
}

// Notification Types
export interface Notification {
  id: string
  type: string
  title: string
  message: string
  is_read: boolean
  priority: 'low' | 'normal' | 'high' | 'urgent'
  action_url?: string
  created_at: string
  read_at?: string | null
}

// Form validation types
export interface FormError {
  field: string
  message: string
}

export interface FormState<T> {
  values: T
  errors: FormError[]
  isSubmitting: boolean
}
