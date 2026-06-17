import { useQuery } from '@tanstack/react-query'
import { fetchViralContent, fetchTopViralContent } from '@/lib/api'
import type { PlatformEnum } from '@/lib/types'

export function useViralContent(params: { offset?: number; limit?: number; platform?: PlatformEnum; min_score?: number } = {}) {
  return useQuery({
    queryKey: ['viral-content', params],
    queryFn: () => fetchViralContent(params),
  })
}

export function useTopViralContent(limit = 10) {
  return useQuery({
    queryKey: ['viral-content', 'top', limit],
    queryFn: () => fetchTopViralContent(limit),
  })
}
