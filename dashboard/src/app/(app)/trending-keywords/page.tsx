'use client'

import { useState } from 'react'
import { Hash, TrendingUp, BarChart2 } from 'lucide-react'
import { useTopKeywords } from '@/hooks/use-trends'
import { StatCard } from '@/components/shared/stat-card'
import { CardSkeleton } from '@/components/ui/skeleton'
import { Select } from '@/components/ui/select'
import { EmptyState } from '@/components/shared/empty-state'

const DAYS_OPTIONS = [
  { value: '7', label: 'Last 7 days' },
  { value: '14', label: 'Last 14 days' },
  { value: '30', label: 'Last 30 days' },
]

function weightToSize(weight: number, maxWeight: number): string {
  const ratio = maxWeight > 0 ? weight / maxWeight : 0
  if (ratio > 0.8) return 'text-2xl font-bold'
  if (ratio > 0.6) return 'text-xl font-semibold'
  if (ratio > 0.4) return 'text-base font-medium'
  if (ratio > 0.2) return 'text-sm font-normal'
  return 'text-xs font-normal'
}

function weightToColor(weight: number, maxWeight: number): string {
  const ratio = maxWeight > 0 ? weight / maxWeight : 0
  if (ratio > 0.8) return 'text-purple-300'
  if (ratio > 0.6) return 'text-violet-400'
  if (ratio > 0.4) return 'text-indigo-400'
  if (ratio > 0.2) return 'text-blue-400'
  return 'text-gray-500'
}

export default function TrendingKeywordsPage() {
  const [days, setDays] = useState(7)

  const { data: keywords, isLoading } = useTopKeywords({ days, limit: 50 })

  const sorted = keywords ? [...keywords].sort((a, b) => b.weight - a.weight) : []
  const maxWeight = sorted[0]?.weight ?? 1
  const totalKeywords = sorted.length
  const avgFrequency = sorted.length
    ? Math.round(sorted.reduce((a, b) => a + b.frequency, 0) / sorted.length)
    : 0

  const topTen = sorted.slice(0, 10)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-100">Trending Keywords</h1>
          <p className="text-sm text-gray-500 mt-0.5">Top keywords extracted from trend analyses</p>
        </div>
        <Select
          options={DAYS_OPTIONS}
          value={String(days)}
          onChange={e => setDays(Number(e.target.value))}
          className="w-40"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard title="Total Keywords" value={totalKeywords} icon={<Hash className="h-4 w-4" />} accent="purple" loading={isLoading} />
        <StatCard title="Avg Frequency" value={avgFrequency} icon={<BarChart2 className="h-4 w-4" />} accent="blue" subtitle="trend mentions" loading={isLoading} />
        <StatCard title="Top Keyword" value={sorted[0]?.keyword ?? '—'} icon={<TrendingUp className="h-4 w-4" />} accent="amber" loading={isLoading} />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<Hash className="h-8 w-8" />}
          title="No keywords yet"
          description="Run the AI pipeline to analyze trends and extract keyword patterns."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Keyword Cloud */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-5">Keyword Cloud</h2>
            <div className="flex flex-wrap gap-2 items-end min-h-[200px]">
              {sorted.map(item => (
                <span
                  key={item.keyword}
                  className={`${weightToSize(item.weight, maxWeight)} ${weightToColor(item.weight, maxWeight)} transition-all hover:opacity-80 cursor-default`}
                  title={`Weight: ${item.weight.toFixed(2)} · Frequency: ${item.frequency}`}
                >
                  #{item.keyword}
                </span>
              ))}
            </div>
          </div>

          {/* Top 10 bar chart */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-5">Top 10 by Weight</h2>
            <div className="space-y-3">
              {topTen.map((item, i) => {
                const pct = maxWeight > 0 ? (item.weight / maxWeight) * 100 : 0
                return (
                  <div key={item.keyword} className="flex items-center gap-3">
                    <span className="text-xs text-gray-600 w-5 text-right">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-300 truncate">#{item.keyword}</span>
                        <span className="text-xs text-gray-600 ml-2 flex-shrink-0">×{item.frequency}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-gray-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-violet-400 transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 w-10 text-right">{item.weight.toFixed(1)}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
