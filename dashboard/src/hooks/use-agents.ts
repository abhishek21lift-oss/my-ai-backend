import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAgentLogs, fetchAgentStatus, runPipeline } from '@/lib/api'
import type { RunPipelineRequest } from '@/lib/types'

export function useAgentLogs(params: { offset?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['agent-logs', params],
    queryFn: () => fetchAgentLogs(params),
  })
}

export function useAgentStatus(logId: string | null) {
  return useQuery({
    queryKey: ['agent-status', logId],
    queryFn: () => fetchAgentStatus(logId!),
    enabled: !!logId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed' || status === 'cancelled') return false
      return 3000
    },
  })
}

export function useRunPipeline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: RunPipelineRequest) => runPipeline(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-logs'] })
    },
  })
}
