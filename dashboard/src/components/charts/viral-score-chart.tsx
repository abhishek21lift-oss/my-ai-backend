'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { truncate } from '@/lib/utils'

interface DataPoint {
  name: string
  score: number
}

interface ViralScoreChartProps {
  data: DataPoint[]
  height?: number
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-lg border border-gray-700 bg-gray-900/95 px-3 py-2 shadow-xl">
        <p className="text-xs text-gray-400 mb-1">{label}</p>
        <p className="text-sm font-bold text-purple-400">{payload[0].value.toFixed(1)}</p>
      </div>
    )
  }
  return null
}

export function ViralScoreChart({ data, height = 240 }: ViralScoreChartProps) {
  const chartData = data.map(d => ({ ...d, name: truncate(d.name, 16) }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#374151', opacity: 0.4 }} />
        <Bar dataKey="score" fill="#9333ea" radius={[4, 4, 0, 0]} maxBarSize={40} />
      </BarChart>
    </ResponsiveContainer>
  )
}
