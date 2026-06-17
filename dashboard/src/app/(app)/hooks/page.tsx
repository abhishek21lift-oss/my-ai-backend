'use client'

import { useState } from 'react'
import { Zap, Star, CheckCircle, XCircle, Filter } from 'lucide-react'
import { useHooks } from '@/hooks/use-hooks'
import { StatCard } from '@/components/shared/stat-card'
import { PlatformBadge } from '@/components/shared/platform-badge'
import { Pagination } from '@/components/shared/pagination'
import { EmptyState } from '@/components/shared/empty-state'
import { CardSkeleton } from '@/components/ui/skeleton'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { cn, PLATFORMS, HOOK_TYPES } from '@/lib/utils'
import type { PlatformEnum, HookTypeEnum } from '@/lib/types'

const LIMIT = 15

const HOOK_TYPE_COLORS: Record<HookTypeEnum, string> = {
  question: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  statement: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  statistic: 'bg-green-500/20 text-green-400 border-green-500/30',
  story: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  controversy: 'bg-red-500/20 text-red-400 border-red-500/30',
  list: 'bg-sky-500/20 text-sky-400 border-sky-500/30',
  challenge: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
}

const PLATFORM_OPTIONS = [
  { value: '', label: 'All Platforms' },
  ...PLATFORMS.map(p => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) })),
]

const HOOK_TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  ...HOOK_TYPES.map(t => ({ value: t, label: t.charAt(0).toUpperCase() + t.slice(1) })),
]

export default function HooksPage() {
  const [offset, setOffset] = useState(0)
  const [platform, setPlatform] = useState<PlatformEnum | ''>('')
  const [unusedOnly, setUnusedOnly] = useState(false)
  const [hookType, setHookType] = useState<HookTypeEnum | ''>('')

  const { data, isLoading } = useHooks({
    offset,
    limit: LIMIT,
    platform: platform || undefined,
    unused_only: unusedOnly,
  })

  const items = data?.items ?? []
  const filtered = hookType ? items.filter(h => h.hook_type === hookType) : items

  const totalUnused = items.filter(h => !h.is_used).length
  const avgQuality = items.filter(h => h.quality_score).length
    ? items.filter(h => h.quality_score).reduce((a, b) => a + (b.quality_score ?? 0), 0) / items.filter(h => h.quality_score).length
    : 0

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Hooks" value={data?.total ?? 0} icon={<Zap className="h-4 w-4" />} accent="amber" loading={isLoading} />
        <StatCard title="Unused" value={totalUnused} icon={<CheckCircle className="h-4 w-4" />} accent="green" subtitle="ready to use" loading={isLoading} />
        <StatCard title="Used" value={items.filter(h => h.is_used).length} icon={<XCircle className="h-4 w-4" />} accent="blue" subtitle="already used" loading={isLoading} />
        <StatCard title="Avg Quality" value={avgQuality.toFixed(1)} icon={<Star className="h-4 w-4" />} accent="purple" subtitle="/ 100" loading={isLoading} />
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Select
          options={PLATFORM_OPTIONS}
          value={platform}
          onChange={e => { setPlatform(e.target.value as PlatformEnum | ''); setOffset(0) }}
          className="w-40"
        />
        <Select
          options={HOOK_TYPE_OPTIONS}
          value={hookType}
          onChange={e => { setHookType(e.target.value as HookTypeEnum | ''); setOffset(0) }}
          className="w-40"
        />
        <button
          onClick={() => { setUnusedOnly(!unusedOnly); setOffset(0) }}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg border text-xs font-medium transition-all',
            unusedOnly
              ? 'bg-purple-600/20 border-purple-500/30 text-purple-300'
              : 'border-gray-700 text-gray-400 hover:border-gray-600 hover:text-gray-300'
          )}
        >
          <Filter className="h-3.5 w-3.5" />
          Unused Only
        </button>
      </div>

      {/* Hooks grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
          {Array.from({ length: 9 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Zap className="h-8 w-8" />}
          title="No hooks found"
          description="Run the AI pipeline to generate compelling hooks for your content."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
          {filtered.map(hook => (
            <div key={hook.id} className={cn(
              'rounded-xl border bg-gray-900 p-4 transition-all hover:shadow-lg',
              hook.is_used ? 'border-gray-800 opacity-60' : 'border-gray-800 hover:border-gray-700'
            )}>
              {/* Type + Platform + Used badge */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={cn(
                    'px-2 py-0.5 rounded-full text-xs font-medium border capitalize',
                    HOOK_TYPE_COLORS[hook.hook_type]
                  )}>
                    {hook.hook_type}
                  </span>
                  <PlatformBadge platform={hook.platform as PlatformEnum} />
                </div>
                {hook.is_used && (
                  <span className="text-xs text-gray-600 flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-600" /> Used
                  </span>
                )}
              </div>

              {/* Content */}
              <p className="text-sm text-gray-200 leading-relaxed mb-3 min-h-[3rem]">
                "{hook.content}"
              </p>

              {/* Footer stats */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-800">
                <div className="flex items-center gap-3 text-xs text-gray-600">
                  {hook.character_count && (
                    <span>{hook.character_count} chars</span>
                  )}
                </div>
                {hook.quality_score !== null && (
                  <div className="flex items-center gap-1">
                    <Star className="h-3 w-3 text-amber-500" />
                    <span className="text-xs font-semibold text-amber-400">{hook.quality_score?.toFixed(0)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {data && data.total > LIMIT && (
        <Pagination offset={offset} limit={LIMIT} total={data.total} onPageChange={setOffset} />
      )}
    </div>
  )
}
