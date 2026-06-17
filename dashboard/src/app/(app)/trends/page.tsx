'use client'

import { useState } from 'react'
import { BarChart2, TrendingUp, Zap, Activity } from 'lucide-react'
import { useTrends, useRisingTrends, useViralTrends } from '@/hooks/use-trends'
import { StatCard } from '@/components/shared/stat-card'
import { ViralScoreBar } from '@/components/shared/viral-score-bar'
import { Pagination } from '@/components/shared/pagination'
import { EmptyState } from '@/components/shared/empty-state'
import { TrendChart } from '@/components/charts/trend-chart'
import { CardSkeleton, Skeleton } from '@/components/ui/skeleton'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { cn, getVelocityColor, formatDate } from '@/lib/utils'
import type { TrendPeriodEnum } from '@/lib/types'

const PERIOD_OPTIONS = [
  { value: '', label: 'All Periods' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
]

const TABS = ['all', 'rising', 'viral'] as const
type Tab = typeof TABS[number]

const LIMIT = 10

export default function TrendsPage() {
  const [tab, setTab] = useState<Tab>('all')
  const [period, setPeriod] = useState<TrendPeriodEnum | ''>('')
  const [offset, setOffset] = useState(0)

  const { data: allData, isLoading: loadingAll } = useTrends({ offset, limit: LIMIT, period: period || undefined })
  const { data: rising, isLoading: loadingRising } = useRisingTrends(20)
  const { data: viral, isLoading: loadingViral } = useViralTrends(20)

  const activeData = tab === 'all' ? allData?.items ?? [] : tab === 'rising' ? rising ?? [] : viral ?? []
  const isLoading = tab === 'all' ? loadingAll : tab === 'rising' ? loadingRising : loadingViral

  const allItems = allData?.items ?? []
  const avgScore = allItems.length ? allItems.reduce((a, b) => a + b.trend_score, 0) / allItems.length : 0

  // Chart data from all trends
  const chartData = [...(rising ?? [])].slice(0, 10).map((t, i) => ({
    name: `Trend ${i + 1}`,
    score: t.trend_score,
  }))

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Trends" value={allData?.total ?? 0} icon={<BarChart2 className="h-4 w-4" />} accent="purple" loading={loadingAll} />
        <StatCard title="Rising" value={rising?.length ?? 0} icon={<TrendingUp className="h-4 w-4" />} accent="green" loading={loadingRising} />
        <StatCard title="Going Viral" value={viral?.length ?? 0} icon={<Zap className="h-4 w-4" />} accent="pink" loading={loadingViral} />
        <StatCard title="Avg Score" value={avgScore.toFixed(1)} icon={<Activity className="h-4 w-4" />} accent="amber" loading={loadingAll} />
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <Card title="Trend Score Overview">
          <div className="p-5">
            <TrendChart data={chartData} height={200} />
          </div>
        </Card>
      )}

      {/* Tabs + Filter */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex rounded-lg border border-gray-800 p-1 gap-1">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => { setTab(t); setOffset(0) }}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors',
                tab === t ? 'bg-purple-600/20 text-purple-300' : 'text-gray-500 hover:text-gray-300'
              )}
            >
              {t === 'all' ? 'All Trends' : t === 'rising' ? 'Rising' : 'Going Viral'}
            </button>
          ))}
        </div>
        {tab === 'all' && (
          <Select
            options={PERIOD_OPTIONS}
            value={period}
            onChange={e => { setPeriod(e.target.value as TrendPeriodEnum | ''); setOffset(0) }}
            className="w-36"
          />
        )}
      </div>

      {/* Trend cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : activeData.length === 0 ? (
        <EmptyState
          icon={<BarChart2 className="h-8 w-8" />}
          title="No trends found"
          description="Run the AI pipeline to analyze trends for your topics."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {activeData.map(trend => (
            <div key={trend.id} className="rounded-xl border border-gray-800 bg-gray-900 p-5 hover:border-gray-700 transition-all">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', getVelocityColor(trend.velocity))}>
                      {trend.velocity}
                    </span>
                    <span className="text-xs text-gray-600 capitalize">{trend.period}</span>
                  </div>
                </div>
                <span className="text-lg font-bold text-gray-200 tabular-nums">{trend.trend_score.toFixed(0)}</span>
              </div>

              {/* Score bar */}
              <ViralScoreBar score={trend.trend_score} size="md" className="mb-3" />

              {/* Keywords */}
              {(trend.keywords as string[]).length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {(trend.keywords as string[]).slice(0, 5).map((kw, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-400">
                      {kw}
                    </span>
                  ))}
                </div>
              )}

              {/* Insights */}
              {trend.insights && (
                <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">{trend.insights}</p>
              )}

              <p className="text-xs text-gray-700 mt-2">{formatDate(trend.analyzed_at)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Pagination (all tab only) */}
      {tab === 'all' && allData && allData.total > LIMIT && (
        <Pagination offset={offset} limit={LIMIT} total={allData.total} onPageChange={setOffset} />
      )}
    </div>
  )
}
