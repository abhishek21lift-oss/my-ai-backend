import { cn, getScoreColor, getScoreTextColor } from '@/lib/utils'

interface ViralScoreBarProps {
  score: number
  showLabel?: boolean
  className?: string
  size?: 'sm' | 'md'
}

export function ViralScoreBar({ score, showLabel = true, className, size = 'sm' }: ViralScoreBarProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn('flex-1 rounded-full bg-gray-800', size === 'sm' ? 'h-1.5' : 'h-2')}>
        <div
          className={cn('h-full rounded-full transition-all', getScoreColor(score))}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn('text-xs font-semibold tabular-nums w-7 text-right', getScoreTextColor(score))}>
          {score.toFixed(0)}
        </span>
      )}
    </div>
  )
}
