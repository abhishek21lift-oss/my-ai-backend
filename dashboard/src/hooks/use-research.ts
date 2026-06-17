import { useQuery } from '@tanstack/react-query'
import { fetchResearchReports } from '@/lib/api'

export function useResearchReports(params: { offset?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['research', params],
    queryFn: () => fetchResearchReports(params),
  })
}
