'use client'

import { useState } from 'react'
import { BookOpen, FileCheck, Loader2, Archive, Search, ChevronDown, ChevronUp, Tag } from 'lucide-react'
import { useResearchReports } from '@/hooks/use-research'
import { StatCard } from '@/components/shared/stat-card'
import { Pagination } from '@/components/shared/pagination'
import { EmptyState } from '@/components/shared/empty-state'
import { CardSkeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Modal } from '@/components/ui/modal'
import { cn, formatDate, getReportStatusColor, truncate } from '@/lib/utils'
import type { ResearchReport } from '@/lib/types'

const LIMIT = 10

export default function ResearchPage() {
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [viewing, setViewing] = useState<ResearchReport | null>(null)

  const { data, isLoading } = useResearchReports({ offset, limit: LIMIT })

  const items = data?.items ?? []
  const filtered = search
    ? items.filter(r => r.title.toLowerCase().includes(search.toLowerCase()) || r.summary?.toLowerCase().includes(search.toLowerCase()))
    : items

  const completed = items.filter(r => r.status === 'completed').length
  const processing = items.filter(r => r.status === 'processing').length

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Reports" value={data?.total ?? 0} icon={<BookOpen className="h-4 w-4" />} accent="blue" loading={isLoading} />
        <StatCard title="Completed" value={completed} icon={<FileCheck className="h-4 w-4" />} accent="green" loading={isLoading} />
        <StatCard title="Processing" value={processing} icon={<Loader2 className="h-4 w-4" />} accent="amber" loading={isLoading} />
        <StatCard title="Avg Words" value={
          items.filter(r => r.word_count).length
            ? Math.round(items.filter(r => r.word_count).reduce((a, b) => a + (b.word_count ?? 0), 0) / items.filter(r => r.word_count).length).toLocaleString()
            : '0'
        } icon={<Archive className="h-4 w-4" />} accent="purple" loading={isLoading} />
      </div>

      {/* Search */}
      <Input
        placeholder="Search reports by title or summary…"
        value={search}
        onChange={e => setSearch(e.target.value)}
        icon={<Search className="h-3.5 w-3.5" />}
      />

      {/* Reports */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="h-8 w-8" />}
          title="No research reports"
          description="Run the AI pipeline to generate in-depth research reports on your topics."
        />
      ) : (
        <div className="space-y-3">
          {filtered.map(report => (
            <div key={report.id} className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
              <div
                className="flex items-start gap-4 p-5 cursor-pointer hover:bg-gray-800/40 transition-colors"
                onClick={() => setExpanded(expanded === report.id ? null : report.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-gray-200 leading-snug">{report.title}</h3>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', getReportStatusColor(report.status))}>
                        {report.status}
                      </span>
                      {expanded === report.id ? (
                        <ChevronUp className="h-4 w-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                      )}
                    </div>
                  </div>

                  {report.summary && (
                    <p className="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">{report.summary}</p>
                  )}

                  <div className="flex flex-wrap items-center gap-3 mt-2.5">
                    {report.key_findings.length > 0 && (
                      <span className="text-xs text-gray-600">{report.key_findings.length} key findings</span>
                    )}
                    {report.word_count && (
                      <span className="text-xs text-gray-600">{report.word_count.toLocaleString()} words</span>
                    )}
                    <span className="text-xs text-gray-700">{formatDate(report.created_at)}</span>
                  </div>

                  {(report.tags as string[]).length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2.5">
                      {(report.tags as string[]).slice(0, 4).map((tag, i) => (
                        <span key={i} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-400">
                          <Tag className="h-2.5 w-2.5" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Expanded section */}
              {expanded === report.id && (
                <div className="border-t border-gray-800 px-5 pb-5 pt-4 space-y-4">
                  {report.key_findings.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Key Findings</h4>
                      <ul className="space-y-1.5">
                        {(report.key_findings as string[]).map((finding, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
                            <span className="flex-shrink-0 w-4 h-4 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 text-xs font-bold">{i + 1}</span>
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {report.content && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Preview</h4>
                      <p className="text-xs text-gray-500 leading-relaxed">{truncate(report.content, 400)}</p>
                      {report.content.length > 400 && (
                        <button
                          onClick={() => setViewing(report)}
                          className="mt-2 text-xs text-purple-400 hover:text-purple-300 transition-colors"
                        >
                          Read full report →
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {data && data.total > LIMIT && (
        <Pagination offset={offset} limit={LIMIT} total={data.total} onPageChange={setOffset} />
      )}

      {/* Full report modal */}
      <Modal open={!!viewing} onClose={() => setViewing(null)} title={viewing?.title ?? ''} size="xl">
        {viewing && (
          <div className="p-6 overflow-y-auto max-h-[70vh] space-y-5">
            {viewing.summary && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Summary</h4>
                <p className="text-sm text-gray-300 leading-relaxed">{viewing.summary}</p>
              </div>
            )}
            {(viewing.key_findings as string[]).length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Key Findings</h4>
                <ul className="space-y-2">
                  {(viewing.key_findings as string[]).map((f, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-gray-400">
                      <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 text-xs font-bold">
                        {i + 1}
                      </span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {viewing.content && (
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Full Content</h4>
                <div className="prose prose-sm prose-invert max-w-none">
                  <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-wrap">{viewing.content}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
