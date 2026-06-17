import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  change?: number
  subtitle?: string
  loading?: boolean
  accent?: 'purple' | 'blue' | 'green' | 'amber' | 'pink'
}

const accentClasses = {
  purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  green: 'text-green-400 bg-green-500/10 border-green-500/20',
  amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  pink: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
}

export function StatCard({ title, value, icon, change, subtitle, loading, accent = 'purple' }: StatCardProps) {
  if (loading) return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-9 w-9 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-3 w-16" />
    </div>
  )

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</p>
        <div className={cn('rounded-lg border p-2', accentClasses[accent])}>
          {icon}
        </div>
      </div>
      <p className="mt-3 text-3xl font-bold text-gray-100">{value}</p>
      <div className="mt-1.5 flex items-center gap-2">
        {change !== undefined && (
          <span className={cn('flex items-center gap-0.5 text-xs font-medium', change >= 0 ? 'text-green-400' : 'text-red-400')}>
            {change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {Math.abs(change)}%
          </span>
        )}
        {subtitle && <span className="text-xs text-gray-500">{subtitle}</span>}
      </div>
    </div>
  )
}
