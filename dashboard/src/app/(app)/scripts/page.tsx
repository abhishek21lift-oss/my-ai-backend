'use client'

import { useState } from 'react'
import { FileText, Clock, AlignLeft, CheckCircle2, BookOpen, ChevronDown, ChevronUp, Star } from 'lucide-react'
import { useScripts, useRateScript } from '@/hooks/use-scripts'
import { StatCard } from '@/components/shared/stat-card'
import { PlatformBadge } from '@/components/shared/platform-badge'
import { Pagination } from '@/components/shared/pagination'
import { EmptyState } from '@/components/shared/empty-state'
import { CardSkeleton } from '@/components/ui/skeleton'
import { Select } from '@/components/ui/select'
import { Modal } from '@/components/ui/modal'
import { cn, getScriptStatusColor, formatDate, PLATFORMS, SCRIPT_STATUSES, truncate } from '@/lib/utils'
import type { PlatformEnum, ScriptStatusEnum, ScriptFormatEnum, Script } from '@/lib/types'

const LIMIT = 8

const PLATFORM_OPTIONS = [
  { value: '', label: 'All Platforms' },
  ...PLATFORMS.map(p => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) })),
]

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  ...SCRIPT_STATUSES.map(s => ({ value: s, label: s.charAt(0).toUpperCase() + s.slice(1) })),
]

const FORMAT_COLORS: Record<ScriptFormatEnum, string> = {
  short_form: 'bg-green-500/20 text-green-400 border-green-500/30',
  long_form: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  carousel: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
  thread: 'bg-sky-500/20 text-sky-400 border-sky-500/30',
  experimental: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
}

const FORMAT_LABELS: Record<ScriptFormatEnum, string> = {
  short_form: 'Short',
  long_form: 'Long',
  carousel: 'Carousel',
  thread: 'Thread',
  experimental: 'Experimental',
}

function StarRating({ scriptId, currentRating }: { scriptId: string; currentRating: number | null }) {
  const [hovered, setHovered] = useState(0)
  const { mutate: rate, isPending } = useRateScript()

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          disabled={isPending}
          onClick={e => { e.stopPropagation(); rate({ scriptId, rating: star }) }}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          className="transition-transform hover:scale-110 disabled:opacity-50"
          title={`Rate ${star}`}
        >
          <Star
            className={cn(
              'h-3.5 w-3.5 transition-colors',
              (hovered || currentRating || 0) >= star
                ? 'text-amber-400 fill-amber-400'
                : 'text-gray-700'
            )}
          />
        </button>
      ))}
    </div>
  )
}

export default function ScriptsPage() {
  const [offset, setOffset] = useState(0)
  const [platform, setPlatform] = useState<PlatformEnum | ''>('')
  const [status, setStatus] = useState<ScriptStatusEnum | ''>('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [viewing, setViewing] = useState<Script | null>(null)

  const { data, isLoading } = useScripts({
    offset,
    limit: LIMIT,
    platform: platform || undefined,
    status: status || undefined,
  })

  const items = data?.items ?? []
  const drafts = items.filter(s => s.status === 'draft').length
  const approved = items.filter(s => s.status === 'approved').length
  const published = items.filter(s => s.status === 'published').length

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Scripts" value={data?.total ?? 0} icon={<FileText className="h-4 w-4" />} accent="purple" loading={isLoading} />
        <StatCard title="Drafts" value={drafts} icon={<AlignLeft className="h-4 w-4" />} accent="blue" loading={isLoading} />
        <StatCard title="Approved" value={approved} icon={<CheckCircle2 className="h-4 w-4" />} accent="green" loading={isLoading} />
        <StatCard title="Published" value={published} icon={<BookOpen className="h-4 w-4" />} accent="amber" loading={isLoading} />
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <Select
          options={PLATFORM_OPTIONS}
          value={platform}
          onChange={e => { setPlatform(e.target.value as PlatformEnum | ''); setOffset(0) }}
          className="w-40"
        />
        <Select
          options={STATUS_OPTIONS}
          value={status}
          onChange={e => { setStatus(e.target.value as ScriptStatusEnum | ''); setOffset(0) }}
          className="w-36"
        />
      </div>

      {/* Scripts list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-8 w-8" />}
          title="No scripts found"
          description="Run the AI pipeline to generate platform-optimized scripts from your hooks."
        />
      ) : (
        <div className="space-y-3">
          {items.map(script => (
            <div key={script.id} className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
              <div
                className="flex items-start justify-between gap-4 p-5 cursor-pointer hover:bg-gray-800/30 transition-colors"
                onClick={() => setExpanded(expanded === script.id ? null : script.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3 mb-2">
                    <h3 className="text-sm font-semibold text-gray-200 leading-snug">{script.title}</h3>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <PlatformBadge platform={script.platform as PlatformEnum} />
                    {script.script_format && (
                      <span className={cn(
                        'px-2 py-0.5 rounded-full text-xs font-medium border',
                        FORMAT_COLORS[script.script_format]
                      )}>
                        {FORMAT_LABELS[script.script_format]}
                      </span>
                    )}
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', getScriptStatusColor(script.status))}>
                      {script.status}
                    </span>
                    {script.duration_seconds && (
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <Clock className="h-3 w-3" />
                        {script.duration_seconds}s
                      </span>
                    )}
                    {script.word_count && (
                      <span className="text-xs text-gray-600">{script.word_count.toLocaleString()} words</span>
                    )}
                    <span className="text-xs text-gray-700">{formatDate(script.created_at)}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 line-clamp-2 leading-relaxed">{truncate(script.content, 120)}</p>
                </div>
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  <StarRating scriptId={script.id} currentRating={script.user_rating} />
                  {expanded === script.id
                    ? <ChevronUp className="h-4 w-4 text-gray-500" />
                    : <ChevronDown className="h-4 w-4 text-gray-500" />
                  }
                </div>
              </div>

              {/* Expanded */}
              {expanded === script.id && (
                <div className="border-t border-gray-800 p-5 space-y-4">
                  {script.outline && (script.outline as Record<string, unknown>[]).length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Outline</h4>
                      <div className="space-y-1.5">
                        {(script.outline as Record<string, unknown>[]).map((section, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-gray-400">
                            <span className="flex-shrink-0 text-purple-500 font-bold">{i + 1}.</span>
                            <span>{String(section.title ?? section.section ?? JSON.stringify(section))}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <button
                    onClick={() => setViewing(script)}
                    className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
                  >
                    View full script →
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {data && data.total > LIMIT && (
        <Pagination offset={offset} limit={LIMIT} total={data.total} onPageChange={setOffset} />
      )}

      {/* Full script modal */}
      <Modal open={!!viewing} onClose={() => setViewing(null)} title={viewing?.title ?? ''} size="xl">
        {viewing && (
          <div className="p-6 overflow-y-auto max-h-[70vh] space-y-5">
            <div className="flex flex-wrap gap-2">
              <PlatformBadge platform={viewing.platform as PlatformEnum} />
              {viewing.script_format && (
                <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', FORMAT_COLORS[viewing.script_format])}>
                  {FORMAT_LABELS[viewing.script_format]}
                </span>
              )}
              <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', getScriptStatusColor(viewing.status))}>
                {viewing.status}
              </span>
              {viewing.duration_seconds && (
                <span className="flex items-center gap-1 text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full border border-gray-700">
                  <Clock className="h-3 w-3" /> {viewing.duration_seconds}s
                </span>
              )}
              {viewing.word_count && (
                <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full border border-gray-700">
                  {viewing.word_count.toLocaleString()} words
                </span>
              )}
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Script Content</h4>
              <div className="rounded-lg bg-gray-800/60 border border-gray-700/50 p-4">
                <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{viewing.content}</p>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
