import { apiClient } from './api'

export interface InfrastructureMetrics {
  timestamp: string
  total_assets: {
    total: number
    active: number
    inactive: number
  }
  asset_distribution: Record<string, number>
  warranty_analysis: {
    expired: number
    expiring_30_days: number
    expiring_90_days: number
    healthy: number
    at_risk: number
  }
  av_compliance: {
    protected: number
    expired: number
    unknown: number
    compliance_percentage: number
  }
  asset_age_analysis: {
    less_than_1_year: number
    '1_to_3_years': number
    '3_to_5_years': number
    over_5_years: number
  }
  room_distribution: Record<string, number>
  health_score: number
  capacity_summary: {
    total_cores: number
    total_ram_gb: number
    total_ram_tb: number
    total_storage_tb: number
    gpu_servers: number
  }
  compliance_status: {
    compliant: number
    non_compliant: number
    compliance_percentage: number
  }
  critical_alerts: Array<{
    type: string
    severity: string
    count: number
    message: string
  }>
}

export interface DashboardMetrics {
  timestamp: string
  user: {
    id: string
    username: string
    role: string
  }
  projects: {
    total_projects: number
    by_status: {
      active: number
      pending: number
      completed: number
      on_hold: number
    }
    budget: {
      total: number
      allocated: number
      remaining: number
      avg_utilization: number
    }
  }
  resources: {
    by_type: Record<string, number>
    by_status: Record<string, number>
    total_resources: number
  }
  trends: {
    days: number
    trends: Record<string, Record<string, number>>
    period_start: string
    period_end: string
  }
  budget_status: {
    projects: Array<{
      project_id: string
      project_name: string
      total_budget: number
      allocated: number
      remaining: number
      utilization_percentage: number
    }>
    warnings: Array<{
      project_id: string
      project_name: string
      total_budget: number
      allocated: number
      remaining: number
      utilization_percentage: number
    }>
    critical: Array<{
      project_id: string
      project_name: string
      total_budget: number
      allocated: number
      remaining: number
      utilization_percentage: number
    }>
    total_budget: number
    total_allocated: number
    total_remaining: number
  }
}

export interface InfrastructureKPIs {
  timestamp: string
  total_assets: {
    total: number
    active: number
    inactive: number
  }
  asset_distribution: Record<string, number>
  warranty_analysis: {
    expired: number
    expiring_30_days: number
    expiring_90_days: number
    healthy: number
    at_risk: number
  }
  av_compliance: {
    protected: number
    expired: number
    unknown: number
    compliance_percentage: number
  }
  asset_age_analysis: {
    less_than_1_year: number
    '1_to_3_years': number
    '3_to_5_years': number
    over_5_years: number
  }
  room_distribution: Record<string, number>
  health_score: number
  capacity_summary: {
    total_cores: number
    total_ram_gb: number
    total_ram_tb: number
    total_storage_tb: number
    gpu_servers: number
  }
  compliance_status: {
    compliant: number
    non_compliant: number
    compliance_percentage: number
  }
  critical_alerts: Array<{
    type: string
    severity: string
    count: number
    message: string
  }>
}

class DashboardService {
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await apiClient.get<DashboardMetrics>('/dashboard/metrics')
    return response.data
  }

  async getProjectOverview() {
    const response = await apiClient.get('/dashboard/projects')
    return response.data
  }

  async getResourceDistribution() {
    const response = await apiClient.get('/dashboard/resources')
    return response.data
  }

  async getUtilizationTrends(days: number = 30) {
    const response = await apiClient.get('/dashboard/trends', { params: { days } })
    return response.data
  }

  async getBudgetStatus() {
    const response = await apiClient.get('/dashboard/budget-status')
    return response.data
  }

  async clearCache() {
    const response = await apiClient.post('/dashboard/cache/clear')
    return response.data
  }

  async getInfrastructureMetrics(): Promise<InfrastructureMetrics> {
    const response = await apiClient.get<InfrastructureMetrics>('/dashboard/infrastructure/kpis')
    return response.data
  }

  async getInfrastructureKPIs(): Promise<InfrastructureKPIs> {
    const response = await apiClient.get<InfrastructureKPIs>('/dashboard/infrastructure/kpis')
    return response.data
  }
}

export const dashboardService = new DashboardService()
