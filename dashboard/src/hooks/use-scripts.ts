import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchScripts, rateScript } from '@/lib/api'
import type { PlatformEnum, ScriptStatusEnum } from '@/lib/types'

export function useScripts(params: { offset?: number; limit?: number; status?: ScriptStatusEnum; platform?: PlatformEnum } = {}) {
  return useQuery({
    queryKey: ['scripts', params],
    queryFn: () => fetchScripts(params),
  })
}

export function useRateScript() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ scriptId, rating, notes }: { scriptId: string; rating: number; notes?: string }) =>
      rateScript(scriptId, rating, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scripts'] })
    },
  })
}
