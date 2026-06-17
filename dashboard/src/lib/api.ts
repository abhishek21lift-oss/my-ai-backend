import axios from 'axios'
import { getApiKey } from './auth'
import type {
  PaginatedResponse, Topic, ViralContent, TrendAnalysis, ResearchReport,
  Hook, Script, DailyRecommendations, AgentLog, AgentRunResponse,
  PlatformEnum, TrendPeriodEnum, ScriptStatusEnum, RunPipelineRequest, KeywordItem,
} from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({ baseURL: BASE_URL })

apiClient.interceptors.request.use((config) => {
  const key = getApiKey()
  if (key) config.headers['Authorization'] = `Bearer ${key}`
  return config
})

// Topics
export const fetchTopics = (offset = 0, limit = 100) =>
  apiClient.get<PaginatedResponse<Topic>>('/topics', { params: { offset, limit } }).then(r => r.data)

// Viral Content
export const fetchViralContent = (params: { offset?: number; limit?: number; platform?: PlatformEnum; min_score?: number }) =>
  apiClient.get<PaginatedResponse<ViralContent>>('/viral-content', { params }).then(r => r.data)

export const fetchTopViralContent = (limit = 10) =>
  apiClient.get<ViralContent[]>('/viral-content/top', { params: { limit } }).then(r => r.data)

// Trends
export const fetchTrends = (params: { offset?: number; limit?: number; period?: TrendPeriodEnum }) =>
  apiClient.get<PaginatedResponse<TrendAnalysis>>('/trends', { params }).then(r => r.data)

export const fetchRisingTrends = (limit = 10) =>
  apiClient.get<TrendAnalysis[]>('/trends/rising', { params: { limit } }).then(r => r.data)

export const fetchViralTrends = (limit = 10) =>
  apiClient.get<TrendAnalysis[]>('/trends/viral', { params: { limit } }).then(r => r.data)

// Research
export const fetchResearchReports = (params: { offset?: number; limit?: number }) =>
  apiClient.get<PaginatedResponse<ResearchReport>>('/research', { params }).then(r => r.data)

// Keywords
export const fetchTopKeywords = (params: { days?: number; limit?: number } = {}) =>
  apiClient.get<KeywordItem[]>('/trends/keywords', { params }).then(r => r.data)

// Hooks
export const fetchHooks = (params: { offset?: number; limit?: number; platform?: PlatformEnum; unused_only?: boolean }) =>
  apiClient.get<PaginatedResponse<Hook>>('/hooks', { params }).then(r => r.data)

export const rateHook = (hookId: string, rating: number, notes?: string) =>
  apiClient.post<Hook>(`/hooks/${hookId}/rate`, { rating, notes }).then(r => r.data)

// Scripts
export const fetchScripts = (params: { offset?: number; limit?: number; status?: ScriptStatusEnum; platform?: PlatformEnum }) =>
  apiClient.get<PaginatedResponse<Script>>('/scripts', { params }).then(r => r.data)

export const rateScript = (scriptId: string, rating: number, notes?: string) =>
  apiClient.post<Script>(`/scripts/${scriptId}/rate`, { rating, notes }).then(r => r.data)

// Recommendations
export const fetchDailyRecommendations = () =>
  apiClient.get<DailyRecommendations>('/recommendations/daily').then(r => r.data)

// Agents
export const fetchAgentLogs = (params: { offset?: number; limit?: number }) =>
  apiClient.get<PaginatedResponse<AgentLog>>('/agents/logs', { params }).then(r => r.data)

export const fetchAgentStatus = (logId: string) =>
  apiClient.get<AgentRunResponse>(`/agents/run/${logId}`).then(r => r.data)

export const runPipeline = (payload: RunPipelineRequest) =>
  apiClient.post<AgentRunResponse>('/agents/run', payload).then(r => r.data)
