import React, { useMemo } from 'react'
import * as echarts from 'echarts'
import { AlertCircle, Loader } from 'lucide-react'

interface UtilizationTrendData {
  days: number
  trends: Record<string, Record<string, number>>
  period_start: string
  period_end: string
}

interface UtilizationTrendChartProps {
  data?: UtilizationTrendData
  isLoading?: boolean
  error?: Error | null
}

export const UtilizationTrendChart: React.FC<UtilizationTrendChartProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null)

  const chartData = useMemo(() => {
    if (!data || !data.trends) return { dates: [], series: [] }

    const dates = Object.keys(data.trends).sort()
    const typeMap: Record<string, number[]> = {}

    // Aggregate data by asset type
    dates.forEach(date => {
      const dayData = data.trends[date]
      Object.entries(dayData).forEach(([assetTypeId, count]) => {
        if (!typeMap[assetTypeId]) {
          typeMap[assetTypeId] = new Array(dates.length).fill(0)
        }
        const index = dates.indexOf(date)
        typeMap[assetTypeId][index] = count
      })
    })

    const series = Object.entries(typeMap).map(([typeId, values], index) => ({
      name: `Type ${typeId.substring(0, 8)}...`,
      type: 'line',
      data: values,
      smooth: true,
      color: [
        '#3B82F6',
        '#10B981',
        '#F59E0B',
        '#EF4444',
        '#8B5CF6',
        '#EC4899',
        '#06B6D4',
        '#6366F1',
      ][index % 8],
    }))

    return { dates, series }
  }, [data])

  React.useEffect(() => {
    if (!containerRef.current || !data || chartData.dates.length === 0) return

    const chart = echarts.init(containerRef.current)

    const option = {
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        data: chartData.series.map(s => s.name),
        top: 0,
      },
      grid: {
        left: '3%',
        right: '3%',
        bottom: '3%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: chartData.dates,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
      },
      series: chartData.series,
    }

    chart.setOption(option)

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
    }
  }, [chartData, data])

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center h-80">
          <Loader className="animate-spin text-gray-400" size={24} />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-3 text-red-600">
          <AlertCircle size={20} />
          <span className="text-sm">Failed to load utilization trends</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Utilization Trends (30 Days)</h2>
        <p className="text-sm text-gray-600 mt-1">Resource allocation over time by type</p>
      </div>

      {/* Chart */}
      {chartData.dates.length > 0 ? (
        <div ref={containerRef} style={{ width: '100%', height: '350px' }} />
      ) : (
        <div className="flex items-center justify-center h-80 bg-gray-50 rounded">
          <p className="text-gray-600">No trend data available</p>
        </div>
      )}
    </div>
  )
}
