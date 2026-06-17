import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PaginationProps {
  offset: number
  limit: number
  total: number
  onPageChange: (offset: number) => void
}

export function Pagination({ offset, limit, total, onPageChange }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.max(1, Math.ceil(total / limit))

  const pages = buildPageList(currentPage, totalPages)

  return (
    <div className="flex items-center justify-between pt-4 border-t border-gray-800">
      <p className="text-xs text-gray-500">
        Showing {Math.min(offset + 1, total)}–{Math.min(offset + limit, total)} of {total}
      </p>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(Math.max(0, offset - limit))}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {pages.map((p, i) =>
          p === '...' ? (
            <span key={`ellipsis-${i}`} className="px-2 text-gray-600 text-sm">…</span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange((Number(p) - 1) * limit)}
              className={cn(
                'w-8 h-8 rounded-lg text-xs font-medium transition-colors',
                p === currentPage
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              )}
            >
              {p}
            </button>
          )
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(offset + limit)}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

function buildPageList(current: number, total: number): (number | '...')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | '...')[] = [1]
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i)
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
}
