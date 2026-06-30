import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface MetricsCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon?: React.ReactNode
  className?: string
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  className = '',
}) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp size={16} className="text-green-600" />
      case 'down':
        return <TrendingDown size={16} className="text-red-600" />
      default:
        return null
    }
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm p-3 ${className}`}>
      {/* Header with icon and title */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-gray-600">{title}</h3>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>

      {/* Main value */}
      <div className="mb-1">
        <p className="text-lg font-bold text-gray-900">{value}</p>
      </div>

      {/* Subtitle and trend */}
      <div className="flex items-center justify-between">
        {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        {trend && trendValue && (
          <div className={`flex items-center gap-0.5 ${getTrendColor()} text-xs font-medium`}>
            {getTrendIcon()}
            <span>{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  )
}
