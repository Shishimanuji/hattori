import React, { useMemo } from 'react'
import * as echarts from 'echarts'
import { AlertCircle, Loader } from 'lucide-react'

interface ResourceDistributionData {
  by_type: Record<string, number>
  by_status: Record<string, number>
  total_resources: number
}

interface ResourceDistributionChartProps {
  data?: ResourceDistributionData
  isLoading?: boolean
  error?: Error | null
}

export const ResourceDistributionChart: React.FC<ResourceDistributionChartProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null)

  const chartData = useMemo(() => {
    if (!data || !data.by_type) return []

    return Object.entries(data.by_type).map(([type, count]) => ({
      value: count,
      name: type,
    }))
  }, [data])

  React.useEffect(() => {
    if (!containerRef.current || !data || chartData.length === 0) return

    const chart = echarts.init(containerRef.current)

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.componentSubType === 'pie') {
            const percentage = ((params.value / (data.total_resources || 1)) * 100).toFixed(1)
            return `${params.name}<br/>Count: ${params.value}<br/>Percentage: ${percentage}%`
          }
          return params.name
        },
      },
      series: [
        {
          name: 'Resources',
          type: 'pie',
          radius: ['30%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: chartData,
          colors: [
            '#3B82F6', // blue
            '#10B981', // green
            '#F59E0B', // amber
            '#EF4444', // red
            '#8B5CF6', // purple
            '#EC4899', // pink
            '#06B6D4', // cyan
            '#6366F1', // indigo
          ],
        },
      ],
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
        <div className="flex items-center justify-center h-64">
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
          <span className="text-sm">Failed to load resource distribution</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Resource Distribution by Type</h2>
        <p className="text-sm text-gray-600 mt-1">Total Resources: {data?.total_resources || 0}</p>
      </div>

      {/* Chart */}
      {chartData.length > 0 ? (
        <div ref={containerRef} style={{ width: '100%', height: '300px' }} />
      ) : (
        <div className="flex items-center justify-center h-64 bg-gray-50 rounded">
          <p className="text-gray-600">No resource data available</p>
        </div>
      )}

      {/* Legend */}
      {chartData.length > 0 && (
        <div className="mt-6 grid grid-cols-2 gap-3">
          {chartData.map((item, index) => (
            <div key={item.name} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor: [
                    '#3B82F6',
                    '#10B981',
                    '#F59E0B',
                    '#EF4444',
                    '#8B5CF6',
                    '#EC4899',
                    '#06B6D4',
                    '#6366F1',
                  ][index % 8],
                }}
              />
              <div className="flex-1 text-sm">
                <p className="text-gray-700">{item.name}</p>
                <p className="text-gray-600">{item.value} resources</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
