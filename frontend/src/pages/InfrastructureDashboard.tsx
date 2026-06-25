import React, { useEffect, useRef } from 'react'
import { RefreshCw, AlertCircle, AlertTriangle, Plus, Download, Search, Clock, Loader, RotateCcw } from 'lucide-react'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
     

import { useInfrastructureKPIs, useClearDashboardCache } from '../hooks/useDashboard'

interface KPICardProps {
  label: string
  value: string | number | null
  subtext?: string
  icon?: string
  color?: string
  isLoading?: boolean
}

const KPICard: React.FC<KPICardProps> = ({ label, value, subtext, icon, color = 'bg-blue-50', isLoading }) => (
  <div className={`${color} rounded-lg p-6 border-l-4 border-blue-600 shadow-sm hover:shadow-md transition`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-gray-600 text-sm font-medium">{label}</p>
        <p className="text-3xl font-bold mt-2 text-gray-900">
          {isLoading ? <Loader size={24} className="animate-spin text-gray-400" /> : value ?? 'N/A'}
        </p>
        {subtext && <p className="text-xs text-gray-500 mt-2">{subtext}</p>}
      </div>
      {icon && <span className="text-4xl">{icon}</span>}
    </div>
  </div>
)

const BarChart: React.FC<{ title: string; data: Record<string, number>; containerRef: React.RefObject<HTMLDivElement> }> = ({
  title,
  data,
  containerRef,
}) => {
  useEffect(() => {
    if (!containerRef.current) return

    let chartInstance: echarts.ECharts | null = null
    const resizeHandler = () => {
      if (chartInstance && !chartInstance.isDisposed()) {
        chartInstance.resize()
      }
    }

    try {
      chartInstance = echarts.init(containerRef.current)
      const option = {
        title: { text: title, left: 'center', textStyle: { fontSize: 14, fontWeight: 'bold' } },
        tooltip: { trigger: 'axis' },
        grid: { top: 60, left: 60, right: 40, bottom: 40 },
        xAxis: {
          type: 'category',
          data: Object.keys(data),
          axisLabel: { rotate: 45 },
        },
        yAxis: { type: 'value' },
        series: [
          {
            data: Object.values(data),
            type: 'bar',
            itemStyle: { color: '#3b82f6' },
          },
        ],
      } as EChartsOption
      chartInstance.setOption(option)
      
      window.addEventListener('resize', resizeHandler)
      
      return () => {
        window.removeEventListener('resize', resizeHandler)
        if (chartInstance && !chartInstance.isDisposed()) {
          chartInstance.dispose()
        }
      }
    } catch (error) {
      console.error('Error initializing BarChart:', error)
      return () => {
        if (chartInstance && !chartInstance.isDisposed()) {
          chartInstance.dispose()
        }
      }
    }
  }, [data, title, containerRef])

  return <div ref={containerRef} style={{ width: '100%', height: '400px' }} className="bg-gray-50 rounded" />
}

const DonutChart: React.FC<{ title: string; data: Record<string, number>; containerRef: React.RefObject<HTMLDivElement> }> = ({
  title,
  data,
  containerRef,
}) => {
  useEffect(() => {
    if (!containerRef.current) return

    let chartInstance: echarts.ECharts | null = null
    const resizeHandler = () => {
      if (chartInstance && !chartInstance.isDisposed()) {
        chartInstance.resize()
      }
    }

    try {
      chartInstance = echarts.init(containerRef.current)
      const pieData = Object.entries(data).map(([name, value]) => ({ name, value }))
      const colors = ['#10b981', '#f59e0b', '#ef4444', '#6366f1']

      const option = {
        title: { text: title, left: 'center', textStyle: { fontSize: 14, fontWeight: 'bold' } },
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', left: 'left', top: 'center' },
        series: [
          {
            name: title,
            type: 'pie',
            radius: '60%',
            data: pieData,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: { formatter: '{b}: {c}' },
            color: colors,
          },
        ],
      } as EChartsOption
      chartInstance.setOption(option)
      
      window.addEventListener('resize', resizeHandler)
      
      return () => {
        window.removeEventListener('resize', resizeHandler)
        if (chartInstance && !chartInstance.isDisposed()) {
          chartInstance.dispose()
        }
      }
    } catch (error) {
      console.error('Error initializing DonutChart:', error)
      return () => {
        if (chartInstance && !chartInstance.isDisposed()) {
          chartInstance.dispose()
        }
      }
    }
  }, [data, title, containerRef])

  return <div ref={containerRef} style={{ width: '100%', height: '350px' }} className="bg-gray-50 rounded" />
}

const GaugeChart: React.FC<{ score: number; containerRef: React.RefObject<HTMLDivElement> }> = ({ score, containerRef }) => {
  useEffect(() => {
    if (!containerRef.current) return

    let chartInstance: echarts.ECharts | null = null
    const resizeHandler = () => {
      if (chartInstance && !chartInstance.isDisposed()) {
        chartInstance.resize()
      }
    }

    try {
      chartInstance = echarts.init(containerRef.current)
      const option = {
        series: [
          {
            type: 'gauge',
            startAngle: 225,
            endAngle: -45,
            radius: '80%',
            center: ['50%', '50%'],
            min: 0,
            max: 100,
            data: [{ value: Math.max(0, Math.min(100, score)), name: 'Score' }],
            progress: { show: true, width: 10, itemStyle: { color: score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444' } },
            axisLine: { lineStyle: { width: 10, color: [[1, '#e5e7eb']] } },
            axisTick: { distance: -10, splitNumber: 5 },
            splitLine: { distance: -10, length: 8 },
            axisLabel: { color: 'auto', distance: 16 },
            detail: { valueAnimation: true, formatter: '{value}%', color: score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444', fontSize: 20 },
          },
        ],
      } as EChartsOption
      chartInstance.setOption(option)
      
      window.addEventListener('resize', resizeHandler)
      
      return () => {
        window.removeEventListener('resize', resizeHandler)
        if (chartInstance && !chartInstance.isDisposed()) {
          chartInstance.dispose()
        }
      }
    } catch (error) {
      console.error('Error initializing GaugeChart:', error)
      return () => {
        if (chartInstance && !chartInstance.isDisposed()) {
          chartInstance.dispose()
        }
      }
    }
  }, [score, containerRef])

  return <div ref={containerRef} style={{ width: '100%', height: '300px' }} className="bg-gray-50 rounded" />
}

const HeatmapTable: React.FC<{ data: Record<string, number> }> = ({ data }) => {
  const entries = Object.entries(data)
  const maxValue = Math.max(...entries.map(([, v]) => v))

  const getHeatColor = (value: number) => {
    const ratio = value / maxValue
    if (ratio > 0.7) return 'bg-red-100 text-red-900'
    if (ratio > 0.5) return 'bg-yellow-100 text-yellow-900'
    if (ratio > 0.3) return 'bg-blue-100 text-blue-900'
    return 'bg-green-100 text-green-900'
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      {entries.map(([room, count]) => (
        <div key={room} className={`${getHeatColor(count)} p-3 rounded-lg text-center`}>
          <p className="font-semibold text-sm">{room}</p>
          <p className="text-xl font-bold">{count}</p>
        </div>
      ))}
    </div>
  )
}

// Error Boundary Component
interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
              <div>
                <h3 className="font-semibold text-red-800">Error rendering content</h3>
                <p className="text-sm text-red-700 mt-1">{this.state.error?.message || 'Unknown error'}</p>
              </div>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
}

// Loading Skeleton Component
const SkeletonLoader = ({ height = 'h-12' }: { height?: string }) => (
  <div className={`${height} bg-gradient-to-r from-gray-200 to-gray-100 rounded animate-pulse`} />
)

// Error State Component
const ErrorState = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6">
    <div className="flex items-start gap-3">
      <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
      <div className="flex-1">
        <h3 className="font-semibold text-red-800">Failed to load metrics</h3>
        <p className="text-sm text-red-700 mt-1">{message}</p>
        <button
          onClick={onRetry}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm font-medium flex items-center gap-2"
        >
          <RotateCcw size={16} /> Retry
        </button>
      </div>
    </div>
  </div>
)

const InfrastructureDashboard: React.FC = () => {
  const distChartRef = useRef<HTMLDivElement>(null)
  const warrantyChartRef = useRef<HTMLDivElement>(null)
  const ageChartRef = useRef<HTMLDivElement>(null)
  const gaugeChartRef = useRef<HTMLDivElement>(null)

  // Fetch infrastructure KPIs
  const { data: kpis, isLoading, error, refetch } = useInfrastructureKPIs()
  const clearCacheMutation = useClearDashboardCache()

  // Handle refresh button
  const handleRefresh = () => {
    clearCacheMutation.mutate()
    refetch()
  }

  // If loading
  if (isLoading && !kpis) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Infrastructure Dashboard</h1>
              <p className="text-gray-600 mt-1">Real-time asset health and compliance metrics</p>
            </div>
            <button disabled className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg opacity-50 cursor-not-allowed">
              <Loader size={18} className="animate-spin" /> Loading...
            </button>
          </div>

          {/* Loading skeleton for KPI cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg p-6 shadow">
                <SkeletonLoader height="h-6" />
                <div className="mt-4">
                  <SkeletonLoader height="h-12" />
                </div>
              </div>
            ))}
          </div>

          {/* Loading skeleton for charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <SkeletonLoader height="h-96" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // If error
  if (error && !kpis) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Infrastructure Dashboard</h1>
              <p className="text-gray-600 mt-1">Real-time asset health and compliance metrics</p>
            </div>
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <RefreshCw size={18} /> Refresh
            </button>
          </div>

          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load infrastructure metrics'}
            onRetry={() => refetch()}
          />
        </div>
      </div>
    )
  }

  // Default values if KPIs not available
  const data = kpis || {
    total_assets: { total: 0, active: 0, inactive: 0 },
    asset_distribution: {},
    warranty_analysis: { expired: 0, expiring_30_days: 0, expiring_90_days: 0, healthy: 0, at_risk: 0 },
    av_compliance: { protected: 0, expired: 0, unknown: 0, compliance_percentage: 0 },
    asset_age_analysis: { less_than_1_year: 0, '1_to_3_years': 0, '3_to_5_years': 0, over_5_years: 0 },
    room_distribution: {},
    health_score: 0,
    capacity_summary: { total_cores: 0, total_ram_gb: 0, total_ram_tb: 0, total_storage_tb: 0, gpu_servers: 0 },
    compliance_status: { compliant: 0, non_compliant: 0, compliance_percentage: 0 },
    critical_alerts: [],
  }

  // Safely access nested properties with fallbacks
  const totalAssets = data?.total_assets || { total: 0, active: 0, inactive: 0 }
  const warrantyAnalysis = data?.warranty_analysis || { expired: 0, expiring_30_days: 0, expiring_90_days: 0, healthy: 0, at_risk: 0 }
  const avCompliance = data?.av_compliance || { protected: 0, expired: 0, unknown: 0, compliance_percentage: 0 }
  const assetAgeAnalysis = data?.asset_age_analysis || { less_than_1_year: 0, '1_to_3_years': 0, '3_to_5_years': 0, over_5_years: 0 }
  const roomDistribution = data?.room_distribution || {}
  const capacitySummary = data?.capacity_summary || { total_cores: 0, total_ram_gb: 0, total_ram_tb: 0, total_storage_tb: 0, gpu_servers: 0 }
  const complianceStatus = data?.compliance_status || { compliant: 0, non_compliant: 0, compliance_percentage: 0 }
  const assetDistributionData = data?.asset_distribution || {}
  const healthScoreValue = typeof data?.health_score === 'number' ? Math.max(0, Math.min(100, data.health_score)) : 0
  const criticalAlerts = Array.isArray(data?.critical_alerts) ? data.critical_alerts : []

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Infrastructure Dashboard</h1>
            <p className="text-gray-600 mt-1">Real-time asset health and compliance metrics</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={clearCacheMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {clearCacheMutation.isPending ? (
              <>
                <Loader size={18} className="animate-spin" /> Refreshing...
              </>
            ) : (
              <>
                <RefreshCw size={18} /> Refresh
              </>
            )}
          </button>
        </div>


        {/* TOP KPI CARDS - 6 Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <KPICard
            label="Total Assets"
            value={totalAssets.total}
            // icon=""
            color="bg-white"
            isLoading={isLoading}
          />
          <KPICard
            label="Active Assets"
            value={totalAssets.active}
            subtext={totalAssets.total > 0 ? `${((totalAssets.active / totalAssets.total) * 100).toFixed(1)}% of total` : undefined}
            // icon="✅"
            color="bg-white"
            isLoading={isLoading}
          />
          <KPICard
            label="Warranty Expiring"
            value={warrantyAnalysis.expiring_30_days + warrantyAnalysis.expiring_90_days}
            subtext="Next 90 days"
            // icon="⏰"
            color="bg-white"
            isLoading={isLoading}
          />
          <KPICard
            label="Warranty Expired"
            value={warrantyAnalysis.expired}
            subtext="Requires attention"
            // icon="⚠️"
            color="bg-white"
            isLoading={isLoading}
          />
          <KPICard
            label="Total CPU Cores"
            value={capacitySummary.total_cores}
            subtext="Across all assets"
            // icon="⚙️"
            color="bg-white"
            isLoading={isLoading}
          />
          <KPICard
            label="Total RAM"
            value={`${capacitySummary.total_ram_tb} TB`}
            subtext="Across all assets"
            // icon=""
            color="bg-white"
            isLoading={isLoading}
          />
        </div>

        {/* MIDDLE SECTION - 3x2 Grid with Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Asset Distribution by Type */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6">
              {Object.keys(assetDistributionData).length > 0 ? (
                <BarChart title="Asset Distribution by Type" data={assetDistributionData} containerRef={distChartRef} />
              ) : (
                <div className="flex items-center justify-center h-96 bg-gray-50 rounded text-gray-500">
                  No asset distribution data available
                </div>
              )}
            </div>
          </ErrorBoundary>

          {/* Warranty Risk Analysis */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6">
              <DonutChart 
                title="Warranty Risk Analysis" 
                data={{
                  'Healthy': warrantyAnalysis.healthy || 0,
                  'Expiring (30 days)': warrantyAnalysis.expiring_30_days || 0,
                  'Expiring (90 days)': warrantyAnalysis.expiring_90_days || 0,
                  'Expired': warrantyAnalysis.expired || 0,
                }} 
                containerRef={warrantyChartRef} 
              />
            </div>
          </ErrorBoundary>

          {/* Asset Age Analysis */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6">
              <DonutChart 
                title="Asset Age Analysis" 
                data={{
                  'New (< 1 yr)': assetAgeAnalysis.less_than_1_year || 0,
                  'Good (1-3 yrs)': assetAgeAnalysis['1_to_3_years'] || 0,
                  'Aging (3-5 yrs)': assetAgeAnalysis['3_to_5_years'] || 0,
                  'Old (> 5 yrs)': assetAgeAnalysis.over_5_years || 0,
                }} 
                containerRef={ageChartRef} 
              />
            </div>
          </ErrorBoundary>

          {/* Room-wise Asset Distribution */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4 text-center">Room-wise Asset Distribution</h3>
              {Object.keys(roomDistribution).length > 0 ? (
                <HeatmapTable data={roomDistribution} />
              ) : (
                <div className="flex items-center justify-center h-40 bg-gray-50 rounded text-gray-500">
                  No room distribution data available
                </div>
              )}
            </div>
          </ErrorBoundary>

          {/* Compliance Status */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Compliance Status</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Compliance Rate</span>
                    <span className="text-sm font-bold">{complianceStatus.compliance_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-green-600 h-3 rounded-full"
                      style={{ width: `${complianceStatus.compliance_percentage}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-green-50 p-3 rounded">
                    <p className="text-gray-600 text-xs">Compliant</p>
                    <p className="text-2xl font-bold text-green-700">{complianceStatus.compliant}</p>
                  </div>
                  <div className="bg-red-50 p-3 rounded">
                    <p className="text-gray-600 text-xs">Non-compliant</p>
                    <p className="text-2xl font-bold text-red-700">{complianceStatus.non_compliant}</p>
                  </div>
                </div>
              </div>
            </div>
          </ErrorBoundary>

          {/* Antivirus Compliance */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Antivirus Compliance</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                  <span className="text-sm">Protected</span>
                  <span className="font-bold text-green-700">{avCompliance.protected}</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                  <span className="text-sm">Expired</span>
                  <span className="font-bold text-red-700">{avCompliance.expired}</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm">Unknown</span>
                  <span className="font-bold text-gray-700">{avCompliance.unknown}</span>
                </div>
                <div className="mt-4 text-center">
                  <p className="text-xs text-gray-600">Coverage Rate</p>
                  <p className="text-2xl font-bold text-blue-700">{avCompliance.compliance_percentage.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          </ErrorBoundary>
        </div>

        {/* BOTTOM SECTION */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Infrastructure Health Score Gauge */}
          <ErrorBoundary>
            <div className="bg-white rounded-lg shadow p-6 lg:col-span-1">
              <GaugeChart score={healthScoreValue} containerRef={gaugeChartRef} />
              <p className="text-center text-sm text-gray-600 mt-2">Health Score: {healthScoreValue}%</p>
            </div>
          </ErrorBoundary>

          {/* Critical Alerts Panel */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-1">
            <h3 className="text-lg font-bold mb-4">Critical Alerts</h3>
            {criticalAlerts && criticalAlerts.length > 0 ? (
              <div className="space-y-2">
                {criticalAlerts.map((alert, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded flex items-start gap-2 ${
                      alert.severity === 'critical' ? 'bg-red-50' : 'bg-yellow-50'
                    }`}
                  >
                    {alert.severity === 'critical' ? (
                      <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
                    ) : (
                      <AlertTriangle className="text-yellow-600 flex-shrink-0 mt-0.5" size={18} />
                    )}
                    <div className="text-xs">
                      <p className={`font-medium ${alert.severity === 'critical' ? 'text-red-800' : 'text-yellow-800'}`}>
                        {alert.message}
                      </p>
                      <p className="text-gray-500">{alert.count} affected</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500">
                <AlertCircle size={24} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">No critical alerts</p>
              </div>
            )}
          </div>

          {/* Quick Search Box */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-1">
            <h3 className="text-lg font-bold mb-4">Quick Search</h3>
            <div className="flex items-center gap-2 bg-gray-100 rounded-lg px-3 py-2">
              <Search size={18} className="text-gray-400" />
              <input
                type="text"
                placeholder="Natural Language Query"
                className="bg-transparent flex-1 text-sm outline-none"
              />
            </div>
            <p className="text-xs text-gray-500 mt-3">e.g., "Show servers with high CPU usage"</p>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-1">
            <h3 className="text-lg font-bold mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-blue-50 hover:bg-blue-100 rounded text-blue-700 text-sm font-medium">
                <Plus size={16} /> Add New Asset
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-green-50 hover:bg-green-100 rounded text-green-700 text-sm font-medium">
                <Plus size={16} /> Add New Project
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-purple-50 hover:bg-purple-100 rounded text-purple-700 text-sm font-medium">
                <Download size={16} /> Import Assets
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-orange-50 hover:bg-orange-100 rounded text-orange-700 text-sm font-medium">
                <Download size={16} /> Generate Report
              </button>
              <button className="w-full flex items-center gap-2 px-3 py-2 bg-red-50 hover:bg-red-100 rounded text-red-700 text-sm font-medium">
                <Clock size={16} /> Create Alert
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfrastructureDashboard
