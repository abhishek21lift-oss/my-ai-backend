'use client'

import { useState } from 'react'
import { TrendingUp, Eye, Heart, Share2, MessageSquare, ExternalLink, Search, SlidersHorizontal } from 'lucide-react'
import { useViralContent } from '@/hooks/use-viral-content'
import { StatCard } from '@/components/shared/stat-card'
import { PlatformBadge } from '@/components/shared/platform-badge'
import { ViralScoreBar } from '@/components/shared/viral-score-bar'
import { Pagination } from '@/components/shared/pagination'
import { EmptyState } from '@/components/shared/empty-state'
import { CardSkeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { cn, formatNumber, formatDate, PLATFORMS } from '@/lib/utils'
import type { PlatformEnum } from '@/lib/types'

const PLATFORM_OPTIONS = [
  { value: '', label: 'All Platforms' },
  ...PLATFORMS.map(p => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) })),
]

const LIMIT = 12

export default function ViralFeedPage() {
  const [offset, setOffset] = useState(0)
  const [platform, setPlatform] = useState<PlatformEnum | ''>('')
  const [minScore, setMinScore] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading, error } = useViralContent({
    offset,
    limit: LIMIT,
    platform: platform || undefined,
    min_score: minScore ? Number(minScore) : undefined,
  })

  const items = data?.items ?? []
  const filtered = search
    ? items.filter(i => i.title.toLowerCase().includes(search.toLowerCase()))
    : items

  const avgScore = items.length ? items.reduce((a, b) => a + b.viral_score, 0) / items.length : 0

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Items" value={data?.total ?? 0} icon={<TrendingUp className="h-4 w-4" />} accent="purple" loading={isLoading} />
        <StatCard title="Avg Viral Score" value={avgScore.toFixed(1)} icon={<TrendingUp className="h-4 w-4" />} accent="green" loading={isLoading} />
        <StatCard
          title="High Performers"
          value={items.filter(i => i.viral_score >= 70).length}
          icon={<TrendingUp className="h-4 w-4" />}
          accent="amber"
          subtitle="score ≥ 70"
          loading={isLoading}
        />
        <StatCard
          title="Platforms"
          value={new Set(items.map(i => i.platform)).size}
          icon={<TrendingUp className="h-4 w-4" />}
          accent="blue"
          subtitle="active"
          loading={isLoading}
        />
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search content…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            icon={<Search className="h-3.5 w-3.5" />}
          />
        </div>
        <div className="flex gap-3">
          <Select
            options={PLATFORM_OPTIONS}
            value={platform}
            onChange={e => { setPlatform(e.target.value as PlatformEnum | ''); setOffset(0) }}
            className="w-36"
          />
          <Input
            placeholder="Min score"
            type="number"
            min="0"
            max="100"
            value={minScore}
            onChange={e => { setMinScore(e.target.value); setOffset(0) }}
            className="w-28"
            icon={<SlidersHorizontal className="h-3.5 w-3.5" />}
          />
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 text-center text-sm text-red-400">
          Failed to load viral content. Check your API connection.
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<TrendingUp className="h-8 w-8" />}
          title="No viral content found"
          description="Try adjusting your filters or run the AI pipeline to discover viral content."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(item => (
            <div key={item.id} className="rounded-xl border border-gray-800 bg-gray-900 p-4 hover:border-gray-700 transition-all hover:shadow-lg hover:shadow-black/30">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-200 line-clamp-2 leading-snug">{item.title}</h3>
                </div>
                {item.content_url && (
                  <a href={item.content_url} target="_blank" rel="noopener noreferrer"
                    className="flex-shrink-0 text-gray-600 hover:text-purple-400 transition-colors p-1">
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-1.5 mb-3">
                <PlatformBadge platform={item.platform as PlatformEnum} />
                {item.content_type && (
                  <Badge variant="default">{item.content_type}</Badge>
                )}
              </div>

              {/* Viral score */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-500">Viral Score</span>
                </div>
                <ViralScoreBar score={item.viral_score} size="md" />
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-gray-800">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-0.5 text-gray-600 mb-0.5">
                    <Eye className="h-3 w-3" />
                  </div>
                  <p className="text-xs font-medium text-gray-300">{formatNumber(item.views)}</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-0.5 text-gray-600 mb-0.5">
                    <Heart className="h-3 w-3" />
                  </div>
                  <p className="text-xs font-medium text-gray-300">{formatNumber(item.likes)}</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-0.5 text-gray-600 mb-0.5">
                    <Share2 className="h-3 w-3" />
                  </div>
                  <p className="text-xs font-medium text-gray-300">{formatNumber(item.shares)}</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-0.5 text-gray-600 mb-0.5">
                    <MessageSquare className="h-3 w-3" />
                  </div>
                  <p className="text-xs font-medium text-gray-300">{formatNumber(item.comments)}</p>
                </div>
              </div>

              {item.published_at && (
                <p className="text-xs text-gray-600 mt-2 text-right">{formatDate(item.published_at)}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total > LIMIT && (
        <Pagination offset={offset} limit={LIMIT} total={data.total} onPageChange={setOffset} />
      )}
    </div>
  )
}
