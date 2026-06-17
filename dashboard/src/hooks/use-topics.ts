import { useQuery } from '@tanstack/react-query'
import { fetchTopics } from '@/lib/api'

export function useTopics() {
  return useQuery({
    queryKey: ['topics'],
    queryFn: () => fetchTopics(0, 100),
  })
}
