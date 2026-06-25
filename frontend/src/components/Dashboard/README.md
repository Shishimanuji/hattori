# Dashboard Components

This directory contains all the components used in the Project Resource Management System (PRMS) dashboard. The dashboard provides comprehensive visibility into projects, resources, budgets, and allocation trends.

## Components

### 1. **MetricsCard** (`MetricsCard.tsx`)
A reusable card component for displaying key metrics.

**Props:**
- `title: string` - Card title
- `value: string | number` - Primary metric value
- `subtitle?: string` - Secondary text
- `trend?: 'up' | 'down' | 'neutral'` - Trend indicator
- `trendValue?: string` - Trend text (e.g., "↑ 12%")
- `icon?: React.ReactNode` - Optional icon
- `className?: string` - Additional CSS classes

**Usage:**
```tsx
<MetricsCard
  title="Total Projects"
  value={25}
  subtitle="Active projects"
  trend="up"
  trendValue="↑ 3 new"
/>
```

### 2. **ProjectOverviewCard** (`ProjectOverviewCard.tsx`)
Displays high-level project statistics including count by status and budget summary.

**Props:**
- `data?: ProjectOverviewData` - Project overview data
- `isLoading?: boolean` - Loading state
- `error?: Error | null` - Error state

**Data Structure:**
```typescript
{
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
```

**Features:**
- Total project count
- Projects grouped by status with color coding
- Budget summary with allocation percentages
- Average utilization across all projects

### 3. **ResourceDistributionChart** (`ResourceDistributionChart.tsx`)
ECharts pie/donut chart showing resource distribution by type.

**Props:**
- `data?: ResourceDistributionData` - Resource distribution data
- `isLoading?: boolean` - Loading state
- `error?: Error | null` - Error state

**Data Structure:**
```typescript
{
  by_type: Record<string, number> // Asset type IDs mapped to counts
  by_status: Record<string, number> // Status mapped to counts
  total_resources: number
}
```

**Features:**
- Pie/donut chart with color-coded segments
- Hover tooltips showing count and percentage
- Legend showing asset types and resource counts
- Responsive sizing

### 4. **UtilizationTrendChart** (`UtilizationTrendChart.tsx`)
ECharts line chart showing 30-day resource allocation trends by type.

**Props:**
- `data?: UtilizationTrendData` - Trend data
- `isLoading?: boolean` - Loading state
- `error?: Error | null` - Error state

**Data Structure:**
```typescript
{
  days: number
  trends: Record<string, Record<string, number>> // Date -> Type -> Count
  period_start: string
  period_end: string
}
```

**Features:**
- Multi-line chart with one line per resource type
- Smooth curve interpolation
- Date-based X-axis
- Legend with all asset types
- Responsive sizing and refresh on window resize

### 5. **BudgetVisualization** (`BudgetVisualization.tsx`)
Comprehensive budget status display showing allocation across all projects with alerts.

**Props:**
- `data?: BudgetVisualizationData` - Budget status data
- `isLoading?: boolean` - Loading state
- `error?: Error | null` - Error state

**Data Structure:**
```typescript
{
  projects: BudgetProject[]
  warnings: BudgetProject[] // 80-99% utilization
  critical: BudgetProject[] // 100%+ utilization
  total_budget: number
  total_allocated: number
  total_remaining: number
}
```

**Features:**
- Organization-wide budget summary at the top
- Progress bar showing overall allocation
- Separate sections for critical projects (red), warnings (yellow), and healthy projects
- Per-project allocation progress bars
- Color-coded status indicators

### 6. **ProjectAllocationSummary** (`ProjectAllocationSummary.tsx`)
Detailed budget allocation visualization for a single project.

**Props:**
- `totalBudget: number`
- `allocatedBudget: number`
- `remainingBudget?: number`
- `utilizationPercentage: number`
- `currency?: string` (default: 'USD')

**Features:**
- Allocated vs remaining budget display
- Dual progress bars (allocated and remaining)
- Color-coded status (green < 80%, yellow 80-100%, red > 100%)
- Warning and error messages
- Grid summary of total, utilization, and currency

## Data Flow

### Dashboard Page (`../../pages/Dashboard.tsx`)

1. **Fetch Data**: Uses `useDashboardMetrics()` hook which fetches from `/api/dashboard/metrics`
2. **Display Metrics**: Renders all metrics at once for comprehensive view
3. **Responsive Layout**: 
   - Mobile: Single column
   - Tablet: Two-column layout
   - Desktop: Two-column with 4-card metrics row at top
4. **Auto-refresh**: Metrics refresh every 30 seconds matching backend cache TTL
5. **Manual Refresh**: User can click "Refresh" button to clear cache and get fresh data

### API Integration

The dashboard fetches data from these backend endpoints:

- `GET /api/dashboard/metrics` - All metrics combined (recommended)
- `GET /api/dashboard/projects` - Project overview only
- `GET /api/dashboard/resources` - Resource distribution only
- `GET /api/dashboard/trends` - Utilization trends (configurable days)
- `GET /api/dashboard/budget-status` - Budget status with warnings/critical
- `POST /api/dashboard/cache/clear` - Manually clear backend cache

## Styling

All components use Tailwind CSS with a consistent dark blue theme:

- **Primary Blue**: `#3B82F6` (blue-600)
- **Success Green**: `#10B981` (green-600)
- **Warning Yellow**: `#F59E0B` (amber-500)
- **Error Red**: `#EF4444` (red-500)
- **Purple**: `#8B5CF6`
- **Pink**: `#EC4899`
- **Cyan**: `#06B6D4`
- **Indigo**: `#6366F1`

## Performance Considerations

1. **Caching**: TanStack Query caches dashboard data for 30 seconds
2. **Auto-refresh**: Automatic background refresh every 30 seconds
3. **Stale-while-revalidate**: Backend provides 30-second cache TTL
4. **Chart Optimization**: ECharts handles rendering efficiently
5. **Lazy Loading**: Charts only render when visible (no off-screen rendering)

## Error Handling

All components include:
- Loading skeleton/spinner state
- Error boundary with informative messages
- Graceful fallbacks when data is unavailable
- Try-catch blocks in async operations

## Accessibility

Components follow WCAG accessibility guidelines:
- Semantic HTML structure
- ARIA labels where appropriate
- Color contrast meets standards
- Keyboard navigation support
- Error messages are clear and descriptive

## Future Enhancements

- [ ] Export dashboard as PDF
- [ ] Configurable dashboard widgets
- [ ] Custom date range selection for trends
- [ ] Drill-down from metrics to detailed views
- [ ] Real-time WebSocket updates
- [ ] Dark mode support
- [ ] More granular time-based filtering
