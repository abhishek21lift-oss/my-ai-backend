import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchHooks, rateHook } from '@/lib/api'
import type { PlatformEnum } from '@/lib/types'

export function useHooks(params: { offset?: number; limit?: number; platform?: PlatformEnum; unused_only?: boolean } = {}) {
  return useQuery({
    queryKey: ['hooks', params],
    queryFn: () => fetchHooks(params),
  })
}

export function useRateHook() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ hookId, rating, notes }: { hookId: string; rating: number; notes?: string }) =>
      rateHook(hookId, rating, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hooks'] })
    },
  })
}
