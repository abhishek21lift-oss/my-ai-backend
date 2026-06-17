import { cn, getPlatformColor } from '@/lib/utils'
import type { PlatformEnum } from '@/lib/types'

const PLATFORM_LABELS: Record<PlatformEnum, string> = {
  youtube: 'YouTube',
  tiktok: 'TikTok',
  instagram: 'Instagram',
  twitter: 'Twitter/X',
  linkedin: 'LinkedIn',
  reddit: 'Reddit',
  other: 'Other',
}

interface PlatformBadgeProps {
  platform: PlatformEnum
  className?: string
}

export function PlatformBadge({ platform, className }: PlatformBadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border',
      getPlatformColor(platform),
      className
    )}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {PLATFORM_LABELS[platform]}
    </span>
  )
}
