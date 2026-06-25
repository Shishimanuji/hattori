import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardService, DashboardMetrics, InfrastructureMetrics, InfrastructureKPIs } from '../services/dashboard'

// Query key factory for dashboard
const dashboardKeys = {
  all: ['dashboard'] as const,
  metrics: () => [...dashboardKeys.all, 'metrics'] as const,
  projects: () => [...dashboardKeys.all, 'projects'] as const,
  resources: () => [...dashboardKeys.all, 'resources'] as const,
  trends: (days: number) => [...dashboardKeys.all, 'trends', days] as const,
  budgetStatus: () => [...dashboardKeys.all, 'budget-status'] as const,
  infrastructureMetrics: () => [...dashboardKeys.all, 'infrastructure-metrics'] as const,
  infrastructureKPIs: () => [...dashboardKeys.all, 'infrastructure-kpis'] as const,
}

/**
 * Hook to fetch all dashboard metrics
 */
export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: dashboardKeys.metrics(),
    queryFn: () => dashboardService.getDashboardMetrics(),
    staleTime: 60 * 1000, // 30 seconds to match backend cache
    gcTime: 10 * 60 * 1000, // 5 minutes (formerly cacheTime)
     // Auto-refresh every 30 seconds
    retry: (failureCount, error: any) => {
      // Don't retry on 401 or 403 errors (auth issues)
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        return false
      }
      // Retry max 2 times for network errors
      return failureCount < 2
    },
  })
}

/**
 * Hook to fetch infrastructure metrics for the infrastructure dashboard
 */
export const useInfrastructureMetrics = () => {
  return useQuery({
    queryKey: dashboardKeys.infrastructureMetrics(),
    queryFn: () => dashboardService.getInfrastructureMetrics(),
    staleTime: 60 * 1000, // 30 seconds to match backend cache
    gcTime: 10 * 60 * 1000, // 5 minutes (formerly cacheTime)
    // Auto-refresh every 30 seconds
  })
}

/**
 * Hook to fetch infrastructure KPIs
 */
export const useInfrastructureKPIs = () => {
  return useQuery({
    queryKey: dashboardKeys.infrastructureKPIs(),
    queryFn: () => dashboardService.getInfrastructureKPIs(),
    staleTime:  60 * 1000, // 30 seconds to match backend cache
    gcTime: 10 * 60 * 1000, // 5 minutes (formerly cacheTime)
    // Auto-refresh every 30 seconds
    retry: (failureCount, error: any) => {
      // Don't retry on 401 or 403 errors (auth issues)
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        return false
      }
      // Retry max 2 times for network errors
      return failureCount < 2
    },
  })
}

/**
 * Hook to fetch project overview
 */
export const useProjectOverview = () => {
  return useQuery({
    queryKey: dashboardKeys.projects(),
    queryFn: () => dashboardService.getProjectOverview(),
    staleTime: 60 * 1000,
    gcTime:  10 * 60 * 1000,
  })
}

/**
 * Hook to fetch resource distribution
 */
export const useResourceDistribution = () => {
  return useQuery({
    queryKey: dashboardKeys.resources(),
    queryFn: () => dashboardService.getResourceDistribution(),
    staleTime:  60 * 1000,
    gcTime:  10 * 60 * 1000,
  })
}

/**
 * Hook to fetch utilization trends
 */
export const useUtilizationTrends = (days: number = 30) => {
  return useQuery({
    queryKey: dashboardKeys.trends(days),
    queryFn: () => dashboardService.getUtilizationTrends(days),
    staleTime:  60 * 1000,
    gcTime:  10 * 60 * 1000,
  })
}

/**
 * Hook to fetch budget status
 */
export const useBudgetStatus = () => {
  return useQuery({
    queryKey: dashboardKeys.budgetStatus(),
    queryFn: () => dashboardService.getBudgetStatus(),
    staleTime:  60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

/**
 * Hook to clear dashboard cache
 */
export const useClearDashboardCache = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => dashboardService.clearCache(),
    onSuccess: () => {
      // Invalidate all dashboard queries
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all })
    },
  })
}
