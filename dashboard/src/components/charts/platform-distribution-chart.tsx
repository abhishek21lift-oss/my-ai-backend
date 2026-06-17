'use client'

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

const PLATFORM_COLORS: Record<string, string> = {
  youtube: '#ef4444',
  tiktok: '#ec4899',
  instagram: '#a855f7',
  twitter: '#0ea5e9',
  linkedin: '#3b82f6',
  reddit: '#f97316',
  other: '#6b7280',
}

interface DataPoint {
  name: string
  value: number
}

interface PlatformDistributionChartProps {
  data: DataPoint[]
  height?: number
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { name: string; value: number }[] }) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-lg border border-gray-700 bg-gray-900/95 px-3 py-2 shadow-xl">
        <p className="text-xs font-medium text-gray-200 capitalize">{payload[0].name}</p>
        <p className="text-sm font-bold text-purple-400">{payload[0].value} items</p>
      </div>
    )
  }
  return null
}

export function PlatformDistributionChart({ data, height = 220 }: PlatformDistributionChartProps) {
  if (!data.length) return (
    <div className="flex items-center justify-center" style={{ height }}>
      <p className="text-xs text-gray-600">No data available</p>
    </div>
  )

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={PLATFORM_COLORS[entry.name.toLowerCase()] ?? '#6b7280'}
              stroke="transparent"
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value: string) => <span className="text-xs text-gray-400 capitalize">{value}</span>}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
