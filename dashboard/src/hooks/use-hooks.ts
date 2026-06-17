import { useQuery } from '@tanstack/react-query'
import { fetchHooks } from '@/lib/api'
import type { PlatformEnum } from '@/lib/types'

export function useHooks(params: { offset?: number; limit?: number; platform?: PlatformEnum; unused_only?: boolean } = {}) {
  return useQuery({
    queryKey: ['hooks', params],
    queryFn: () => fetchHooks(params),
  })
}
