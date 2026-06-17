import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow } from 'date-fns'
import type { PlatformEnum, TrendVelocityEnum, AgentStatusEnum, ScriptStatusEnum, ReportStatusEnum } from './types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

export function formatDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

export function formatDateTime(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'MMM d, yyyy HH:mm')
  } catch {
    return dateStr
  }
}

export function timeAgo(dateStr: string): string {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
  } catch {
    return dateStr
  }
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength) + '…'
}

export function getPlatformColor(platform: PlatformEnum): string {
  const map: Record<PlatformEnum, string> = {
    youtube: 'bg-red-500/20 text-red-400 border-red-500/30',
    tiktok: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    instagram: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    twitter: 'bg-sky-500/20 text-sky-400 border-sky-500/30',
    linkedin: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    reddit: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    other: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }
  return map[platform] ?? map.other
}

export function getPlatformDot(platform: PlatformEnum): string {
  const map: Record<PlatformEnum, string> = {
    youtube: 'bg-red-500',
    tiktok: 'bg-pink-500',
    instagram: 'bg-purple-500',
    twitter: 'bg-sky-500',
    linkedin: 'bg-blue-500',
    reddit: 'bg-orange-500',
    other: 'bg-gray-500',
  }
  return map[platform] ?? 'bg-gray-500'
}

export function getVelocityColor(velocity: TrendVelocityEnum): string {
  const map: Record<TrendVelocityEnum, string> = {
    viral: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    rising: 'bg-green-500/20 text-green-400 border-green-500/30',
    stable: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    falling: 'bg-red-500/20 text-red-400 border-red-500/30',
  }
  return map[velocity] ?? map.stable
}

export function getScoreColor(score: number): string {
  if (score >= 70) return 'bg-green-500'
  if (score >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

export function getScoreTextColor(score: number): string {
  if (score >= 70) return 'text-green-400'
  if (score >= 40) return 'text-amber-400'
  return 'text-red-400'
}

export function getAgentStatusColor(status: AgentStatusEnum): string {
  const map: Record<AgentStatusEnum, string> = {
    completed: 'bg-green-500/20 text-green-400 border-green-500/30',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }
  return map[status] ?? map.pending
}

export function getScriptStatusColor(status: ScriptStatusEnum): string {
  const map: Record<ScriptStatusEnum, string> = {
    published: 'bg-green-500/20 text-green-400 border-green-500/30',
    approved: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    draft: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }
  return map[status] ?? map.draft
}

export function getReportStatusColor(status: ReportStatusEnum): string {
  const map: Record<ReportStatusEnum, string> = {
    completed: 'bg-green-500/20 text-green-400 border-green-500/30',
    processing: 'bg-blue-500/20 text-blue-400 border-blue-500/30 animate-pulse',
    draft: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    archived: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  }
  return map[status] ?? map.draft
}

export const PLATFORMS: PlatformEnum[] = ['youtube', 'tiktok', 'instagram', 'twitter', 'linkedin', 'reddit', 'other']
export const CONTENT_TYPES = ['video', 'post', 'article', 'thread', 'reel', 'short'] as const
export const TREND_PERIODS = ['daily', 'weekly', 'monthly'] as const
export const HOOK_TYPES = ['question', 'statement', 'statistic', 'story', 'controversy', 'list', 'challenge'] as const
export const SCRIPT_STATUSES = ['draft', 'approved', 'published'] as const
