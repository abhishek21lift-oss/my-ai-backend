'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface DataPoint {
  name: string
  score: number
}

interface TrendChartProps {
  data: DataPoint[]
  height?: number
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-lg border border-gray-700 bg-gray-900/95 px-3 py-2 shadow-xl">
        <p className="text-xs text-gray-400 mb-1">{label}</p>
        <p className="text-sm font-bold text-violet-400">{payload[0].value.toFixed(1)}</p>
      </div>
    )
  }
  return null
}

export function TrendChart({ data, height = 200 }: TrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#7c3aed"
          strokeWidth={2}
          dot={{ r: 3, fill: '#7c3aed', strokeWidth: 0 }}
          activeDot={{ r: 5, fill: '#a855f7' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
