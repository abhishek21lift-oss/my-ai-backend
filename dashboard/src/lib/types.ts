export type PlatformEnum = 'youtube' | 'tiktok' | 'instagram' | 'twitter' | 'linkedin' | 'reddit' | 'other'
export type ContentTypeEnum = 'video' | 'post' | 'article' | 'thread' | 'reel' | 'short'
export type TrendPeriodEnum = 'daily' | 'weekly' | 'monthly'
export type TrendVelocityEnum = 'rising' | 'falling' | 'stable' | 'viral'
export type HookTypeEnum = 'question' | 'statement' | 'statistic' | 'story' | 'controversy' | 'list' | 'challenge'
export type ScriptStatusEnum = 'draft' | 'approved' | 'published'
export type AgentStatusEnum = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type ReportStatusEnum = 'draft' | 'processing' | 'completed' | 'archived'

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  offset: number
  limit: number
  has_more: boolean
}

export interface Topic {
  id: string
  user_id: string
  name: string
  description: string | null
  category: string | null
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface ViralContent {
  id: string
  user_id: string
  topic_id: string | null
  platform: PlatformEnum
  content_type: ContentTypeEnum | null
  title: string
  content_url: string | null
  views: number
  likes: number
  shares: number
  comments: number
  engagement_rate: number | null
  viral_score: number
  published_at: string | null
  collected_at: string
  created_at: string
}

export interface TrendAnalysis {
  id: string
  user_id: string
  topic_id: string | null
  period: TrendPeriodEnum
  trend_score: number
  velocity: TrendVelocityEnum
  keywords: string[]
  insights: string | null
  data_points: Record<string, unknown>[]
  platforms: string[]
  analyzed_at: string
  created_at: string
}

export interface ResearchReport {
  id: string
  user_id: string
  topic_id: string | null
  title: string
  summary: string | null
  content: string | null
  sources: Record<string, unknown>[]
  key_findings: string[]
  tags: string[]
  status: ReportStatusEnum
  word_count: number | null
  created_at: string
  updated_at: string | null
}

export interface Hook {
  id: string
  user_id: string
  topic_id: string | null
  viral_content_id: string | null
  hook_type: HookTypeEnum
  platform: PlatformEnum
  content: string
  character_count: number | null
  quality_score: number | null
  is_used: boolean
  created_at: string
}

export interface Script {
  id: string
  user_id: string
  topic_id: string | null
  hook_id: string | null
  title: string
  platform: PlatformEnum
  duration_seconds: number | null
  content: string
  outline: Record<string, unknown>[]
  word_count: number | null
  status: ScriptStatusEnum
  created_at: string
  updated_at: string | null
}

export interface RecommendationItem {
  type: string
  id: string
  title: string
  description: string
  priority: number
  action: string
  metadata: Record<string, unknown>
}

export interface DailyRecommendations {
  report_date: string
  user_id: string
  items: RecommendationItem[]
  summary: string
  top_platforms: string[]
  top_trending_topics: string[]
  tokens_quota_remaining: number | null
  generated_at: string
}

export interface AgentLog {
  id: string
  user_id: string | null
  agent_name: string
  task_type: string
  status: AgentStatusEnum
  input_tokens: number
  output_tokens: number
  duration_ms: number | null
  retry_count: number
  error: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface AgentRunResponse {
  orchestrator_log_id: string
  status: AgentStatusEnum
  message: string
  job_id: string | null
  result: Record<string, unknown> | null
  stages: AgentStage[] | null
}

export interface AgentStage {
  agent_name: string
  task_type: string
  status: AgentStatusEnum
  duration_ms: number | null
  input_tokens: number
  output_tokens: number
  error: string | null
}

export interface RunPipelineRequest {
  topic_id: string
  platform: PlatformEnum
}
