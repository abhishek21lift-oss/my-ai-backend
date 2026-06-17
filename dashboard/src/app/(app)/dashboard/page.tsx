'use client'

import { TrendingUp, BarChart2, BookOpen, Zap, FileText, Cpu, Clock } from 'lucide-react'
import { StatCard } from '@/components/shared/stat-card'
import { ViralScoreChart } from '@/components/charts/viral-score-chart'
import { PlatformDistributionChart } from '@/components/charts/platform-distribution-chart'
import { Card } from '@/components/ui/card'
import { PlatformBadge } from '@/components/shared/platform-badge'
import { ViralScoreBar } from '@/components/shared/viral-score-bar'
import { Badge } from '@/components/ui/badge'
import { CardSkeleton, Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/shared/empty-state'
import { useTopViralContent } from '@/hooks/use-viral-content'
import { useRisingTrends } from '@/hooks/use-trends'
import { useResearchReports } from '@/hooks/use-research'
import { useScripts } from '@/hooks/use-scripts'
import { useAgentLogs } from '@/hooks/use-agents'
import { useHooks } from '@/hooks/use-hooks'
import { formatDate, timeAgo, getAgentStatusColor, getVelocityColor, cn } from '@/lib/utils'
import type { PlatformEnum } from '@/lib/types'

export default function DashboardPage() {
  const { data: topViral, isLoading: loadingViral } = useTopViralContent(8)
  const { data: risingTrends, isLoading: loadingTrends } = useRisingTrends(6)
  const { data: reports } = useResearchReports({ limit: 5 })
  const { data: scripts } = useScripts({ limit: 5 })
  const { data: hooks } = useHooks({ limit: 5 })
  const { data: agentLogs, isLoading: loadingLogs } = useAgentLogs({ limit: 5 })

  // Build chart data from top viral content
  const chartData = (topViral ?? []).slice(0, 8).map(v => ({
    name: v.title.slice(0, 20),
    score: v.viral_score,
  }))

  // Build platform distribution from top viral content
  const platformCounts: Record<string, number> = {}
  for (const v of topViral ?? []) {
    platformCounts[v.platform] = (platformCounts[v.platform] ?? 0) + 1
  }
  const platformData = Object.entries(platformCounts).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Viral Content"
          value={topViral?.length ?? 0}
          icon={<TrendingUp className="h-4 w-4" />}
          accent="purple"
          change={12}
          subtitle="vs last week"
          loading={loadingViral}
        />
        <StatCard
          title="Research Reports"
          value={reports?.total ?? 0}
          icon={<BookOpen className="h-4 w-4" />}
          accent="blue"
          change={5}
          subtitle="total reports"
          loading={!reports}
        />
        <StatCard
          title="Hooks Created"
          value={hooks?.total ?? 0}
          icon={<Zap className="h-4 w-4" />}
          accent="amber"
          change={8}
          subtitle="total hooks"
          loading={!hooks}
        />
        <StatCard
          title="Scripts Ready"
          value={scripts?.total ?? 0}
          icon={<FileText className="h-4 w-4" />}
          accent="green"
          change={3}
          subtitle="total scripts"
          loading={!scripts}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Viral Score Distribution" className="lg:col-span-2">
          <div className="p-5">
            {loadingViral ? (
              <Skeleton className="h-56 w-full" />
            ) : chartData.length === 0 ? (
              <div className="flex items-center justify-center h-56 text-gray-600 text-sm">
                No data yet — run the pipeline to discover viral content
              </div>
            ) : (
              <ViralScoreChart data={chartData} height={224} />
            )}
          </div>
        </Card>
        <Card title="Platform Distribution">
          <div className="p-5">
            {loadingViral ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <PlatformDistributionChart data={platformData} height={224} />
            )}
          </div>
        </Card>
      </div>

      {/* Content columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Viral Content */}
        <Card title="Top Viral Content" action={
          <a href="/viral-feed" className="text-xs text-purple-400 hover:text-purple-300">View all</a>
        }>
          <div className="divide-y divide-gray-800">
            {loadingViral ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="px-5 py-3 space-y-2">
                  <Skeleton className="h-3.5 w-4/5" />
                  <div className="flex gap-2">
                    <Skeleton className="h-4 w-16 rounded-full" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </div>
              ))
            ) : (topViral ?? []).length === 0 ? (
              <div className="px-5 py-8 text-center text-sm text-gray-600">
                No viral content yet. Run the pipeline to discover content.
              </div>
            ) : (
              (topViral ?? []).slice(0, 6).map(item => (
                <div key={item.id} className="flex items-center gap-3 px-5 py-3 hover:bg-gray-800/40 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-200 truncate">{item.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <PlatformBadge platform={item.platform as PlatformEnum} />
                      {item.content_type && (
                        <span className="text-xs text-gray-600 capitalize">{item.content_type}</span>
                      )}
                    </div>
                  </div>
                  <div className="w-20 flex-shrink-0">
                    <ViralScoreBar score={item.viral_score} />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Rising Trends */}
        <Card title="Rising Trends" action={
          <a href="/trends" className="text-xs text-purple-400 hover:text-purple-300">View all</a>
        }>
          <div className="divide-y divide-gray-800">
            {loadingTrends ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="px-5 py-3 space-y-2">
                  <div className="flex justify-between">
                    <Skeleton className="h-3.5 w-1/2" />
                    <Skeleton className="h-4 w-14 rounded-full" />
                  </div>
                  <Skeleton className="h-2 w-full rounded-full" />
                </div>
              ))
            ) : (risingTrends ?? []).length === 0 ? (
              <div className="px-5 py-8 text-center text-sm text-gray-600">
                No trends yet. Run the pipeline to analyze trends.
              </div>
            ) : (
              (risingTrends ?? []).slice(0, 6).map(trend => (
                <div key={trend.id} className="px-5 py-3 hover:bg-gray-800/40 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-200 capitalize">
                        {(trend.keywords as string[])[0] ?? `Trend ${trend.id.slice(0, 6)}`}
                      </p>
                      <p className="text-xs text-gray-600 capitalize">{trend.period}</p>
                    </div>
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border flex-shrink-0', getVelocityColor(trend.velocity))}>
                      {trend.velocity}
                    </span>
                  </div>
                  <ViralScoreBar score={trend.trend_score} />
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Recent Agent Runs */}
      <Card title="Recent Pipeline Runs" action={
        <a href="/recommendations" className="text-xs text-purple-400 hover:text-purple-300">View recs</a>
      }>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="px-5 py-3 text-left font-medium text-gray-500">Agent</th>
                <th className="px-5 py-3 text-left font-medium text-gray-500">Task</th>
                <th className="px-5 py-3 text-left font-medium text-gray-500">Status</th>
                <th className="px-5 py-3 text-left font-medium text-gray-500">Duration</th>
                <th className="px-5 py-3 text-left font-medium text-gray-500">Tokens</th>
                <th className="px-5 py-3 text-left font-medium text-gray-500">When</th>
              </tr>
            </thead>
            <tbody>
              {loadingLogs ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-800/50">
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-5 py-3">
                        <Skeleton className="h-3.5 w-full" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : (agentLogs?.items ?? []).length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-gray-600">
                    No pipeline runs yet. Click "Run Pipeline" to start.
                  </td>
                </tr>
              ) : (
                (agentLogs?.items ?? []).map(log => (
                  <tr key={log.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        <Cpu className="h-3 w-3 text-purple-500" />
                        <span className="text-gray-300 capitalize">{log.agent_name.replace(/_/g, ' ')}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-gray-500 capitalize">{log.task_type.replace(/_/g, ' ')}</td>
                    <td className="px-5 py-3">
                      <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', getAgentStatusColor(log.status))}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-500 tabular-nums">
                      {log.duration_ms ? `${(log.duration_ms / 1000).toFixed(1)}s` : '—'}
                    </td>
                    <td className="px-5 py-3 text-gray-500 tabular-nums">
                      {(log.input_tokens + log.output_tokens).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-gray-600">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {timeAgo(log.created_at)}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
