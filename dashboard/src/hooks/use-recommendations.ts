import { useQuery } from '@tanstack/react-query'
import { fetchDailyRecommendations } from '@/lib/api'

export function useDailyRecommendations() {
  return useQuery({
    queryKey: ['recommendations', 'daily'],
    queryFn: fetchDailyRecommendations,
  })
}
