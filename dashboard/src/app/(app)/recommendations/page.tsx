'use client'

import {
  Sparkles, TrendingUp, BarChart2, BookOpen, Zap, FileText,
  ArrowRight, CalendarDays, Clock, Gauge, RefreshCw
} from 'lucide-react'
import { useDailyRecommendations } from '@/hooks/use-recommendations'
import { StatCard } from '@/components/shared/stat-card'
import { EmptyState } from '@/components/shared/empty-state'
import { StatSkeleton, Skeleton } from '@/components/ui/skeleton'
import { cn, formatDate, formatDateTime, getPlatformColor } from '@/lib/utils'
import type { RecommendationItem, PlatformEnum } from '@/lib/types'

const TYPE_ICONS: Record<string, React.ReactNode> = {
  hook: <Zap className="h-4 w-4" />,
  script: <FileText className="h-4 w-4" />,
  trend: <BarChart2 className="h-4 w-4" />,
  report: <BookOpen className="h-4 w-4" />,
  viral_content: <TrendingUp className="h-4 w-4" />,
}

const TYPE_COLORS: Record<string, string> = {
  hook: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  script: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  trend: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
  report: 'bg-green-500/10 border-green-500/20 text-green-400',
  viral_content: 'bg-pink-500/10 border-pink-500/20 text-pink-400',
}

const PRIORITY_COLOR = (p: number) => {
  if (p >= 8) return 'bg-red-500/20 text-red-400 border-red-500/30'
  if (p >= 5) return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
  return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
}

function RecCard({ item }: { item: RecommendationItem }) {
  const icon = TYPE_ICONS[item.type] ?? <Sparkles className="h-4 w-4" />
  const color = TYPE_COLORS[item.type] ?? 'bg-gray-500/10 border-gray-500/20 text-gray-400'

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 hover:border-gray-700 transition-all hover:shadow-lg hover:shadow-black/20">
      <div className="flex items-start gap-4">
        <div className={cn('flex-shrink-0 rounded-xl border p-2.5', color)}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <h3 className="text-sm font-semibold text-gray-200 leading-snug">{item.title}</h3>
            <span className={cn('flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-bold border tabular-nums', PRIORITY_COLOR(item.priority))}>
              P{item.priority}
            </span>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed mb-3">{item.description}</p>
          <div className="flex items-center justify-between">
            <span className="px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-500 capitalize">
              {item.type.replace('_', ' ')}
            </span>
            <button className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 transition-colors font-medium">
              {item.action}
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function RecommendationsPage() {
  const { data, isLoading, refetch, isRefetching } = useDailyRecommendations()

  const sorted = [...(data?.items ?? [])].sort((a, b) => b.priority - a.priority)
  const highPriority = sorted.filter(i => i.priority >= 8)
  const normal = sorted.filter(i => i.priority < 8)

  return (
    <div className="space-y-6">
      {/* Header card */}
      <div className="rounded-xl border border-purple-500/20 bg-gradient-to-r from-purple-600/10 to-violet-600/5 p-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <h2 className="text-sm font-semibold text-gray-200">Daily AI Recommendations</h2>
            </div>
            {isLoading ? (
              <Skeleton className="h-3 w-48 mt-1" />
            ) : data ? (
              <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <CalendarDays className="h-3 w-3" />
                  {formatDate(data.report_date)}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Generated {formatDateTime(data.generated_at)}
                </span>
                {data.tokens_quota_remaining !== null && (
                  <span className="flex items-center gap-1">
                    <Gauge className="h-3 w-3" />
                    {data.tokens_quota_remaining?.toLocaleString()} tokens remaining
                  </span>
                )}
              </div>
            ) : null}
          </div>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-600/10 px-3 py-1.5 text-xs font-medium text-purple-400 hover:bg-purple-600/20 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn('h-3 w-3', isRefetching && 'animate-spin')} />
            Refresh
          </button>
        </div>

        {/* Summary */}
        {data?.summary && (
          <p className="mt-3 text-xs text-gray-400 leading-relaxed border-t border-purple-500/10 pt-3">
            {data.summary}
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <StatSkeleton key={i} />)
        ) : (
          <>
            <StatCard title="Total Recs" value={data?.items.length ?? 0} icon={<Sparkles className="h-4 w-4" />} accent="purple" />
            <StatCard title="High Priority" value={highPriority.length} icon={<ArrowRight className="h-4 w-4" />} accent="pink" subtitle="priority ≥ 8" />
            <StatCard title="Top Platform" value={data?.top_platforms[0] ?? '—'} icon={<BarChart2 className="h-4 w-4" />} accent="blue" />
            <StatCard title="Trending Topics" value={data?.top_trending_topics.length ?? 0} icon={<TrendingUp className="h-4 w-4" />} accent="green" />
          </>
        )}
      </div>

      {/* Top Platforms & Topics */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.top_platforms.length > 0 && (
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Top Platforms</h3>
              <div className="flex flex-wrap gap-2">
                {data.top_platforms.map((p, i) => (
                  <span key={i} className={cn(
                    'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
                    getPlatformColor(p as PlatformEnum)
                  )}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
                    <span className="capitalize">{p}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
          {data.top_trending_topics.length > 0 && (
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Trending Topics</h3>
              <div className="flex flex-wrap gap-2">
                {data.top_trending_topics.map((topic, i) => (
                  <span key={i} className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-300">
                    <TrendingUp className="h-2.5 w-2.5 text-purple-500" />
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendations */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-3">
              <div className="flex gap-3">
                <Skeleton className="h-10 w-10 rounded-xl flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={<Sparkles className="h-8 w-8" />}
          title="No recommendations yet"
          description="Run the AI pipeline to generate personalized daily recommendations for your content strategy."
        />
      ) : (
        <>
          {highPriority.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">High Priority</h3>
                <span className="px-2 py-0.5 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium">
                  {highPriority.length}
                </span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {highPriority.map(item => <RecCard key={item.id} item={item} />)}
              </div>
            </div>
          )}

          {normal.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Other Recommendations</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {normal.map(item => <RecCard key={item.id} item={item} />)}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
