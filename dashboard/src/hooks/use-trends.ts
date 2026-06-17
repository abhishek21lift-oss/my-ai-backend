import { useQuery } from '@tanstack/react-query'
import { fetchTrends, fetchRisingTrends, fetchViralTrends } from '@/lib/api'
import type { TrendPeriodEnum } from '@/lib/types'

export function useTrends(params: { offset?: number; limit?: number; period?: TrendPeriodEnum } = {}) {
  return useQuery({
    queryKey: ['trends', params],
    queryFn: () => fetchTrends(params),
  })
}

export function useRisingTrends(limit = 10) {
  return useQuery({
    queryKey: ['trends', 'rising', limit],
    queryFn: () => fetchRisingTrends(limit),
  })
}

export function useViralTrends(limit = 10) {
  return useQuery({
    queryKey: ['trends', 'viral', limit],
    queryFn: () => fetchViralTrends(limit),
  })
}
