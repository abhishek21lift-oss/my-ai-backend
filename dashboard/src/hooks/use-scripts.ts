import { useQuery } from '@tanstack/react-query'
import { fetchScripts } from '@/lib/api'
import type { PlatformEnum, ScriptStatusEnum } from '@/lib/types'

export function useScripts(params: { offset?: number; limit?: number; status?: ScriptStatusEnum; platform?: PlatformEnum } = {}) {
  return useQuery({
    queryKey: ['scripts', params],
    queryFn: () => fetchScripts(params),
  })
}
