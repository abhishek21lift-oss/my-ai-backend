'use client'

import { useState } from 'react'
import { Modal } from '@/components/ui/modal'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { useTopics } from '@/hooks/use-topics'
import { useRunPipeline, useAgentStatus } from '@/hooks/use-agents'
import { cn, getAgentStatusColor } from '@/lib/utils'
import type { PlatformEnum } from '@/lib/types'
import { CheckCircle2, XCircle, Loader2, Cpu } from 'lucide-react'

const PLATFORM_OPTIONS: { value: PlatformEnum; label: string }[] = [
  { value: 'youtube', label: 'YouTube' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'twitter', label: 'Twitter/X' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'reddit', label: 'Reddit' },
]

interface PipelineModalProps {
  open: boolean
  onClose: () => void
}

export function PipelineModal({ open, onClose }: PipelineModalProps) {
  const { data: topicsData } = useTopics()
  const [topicId, setTopicId] = useState('')
  const [platform, setPlatform] = useState<PlatformEnum>('youtube')
  const [runLogId, setRunLogId] = useState<string | null>(null)

  const runMutation = useRunPipeline()
  const { data: statusData } = useAgentStatus(runLogId)

  const topicOptions = (topicsData?.items ?? []).map(t => ({ value: t.id, label: t.name }))

  const handleRun = async () => {
    if (!topicId) return
    try {
      const result = await runMutation.mutateAsync({ topic_id: topicId, platform })
      setRunLogId(result.orchestrator_log_id)
    } catch {}
  }

  const handleClose = () => {
    setRunLogId(null)
    runMutation.reset()
    onClose()
  }

  const isDone = statusData?.status === 'completed' || statusData?.status === 'failed'

  return (
    <Modal open={open} onClose={handleClose} title="Run AI Pipeline" size="lg">
      <div className="p-6 space-y-5">
        {!runLogId ? (
          <>
            <p className="text-sm text-gray-400">
              Runs the full 5-agent pipeline: Viral Scout → Trend Detector → Fitness Scientist → Hook Generator → Script Writer.
            </p>
            <Select
              label="Topic"
              options={topicOptions}
              placeholder="Select a topic..."
              value={topicId}
              onChange={e => setTopicId(e.target.value)}
            />
            <Select
              label="Platform"
              options={PLATFORM_OPTIONS.map(p => ({ value: p.value, label: p.label }))}
              value={platform}
              onChange={e => setPlatform(e.target.value as PlatformEnum)}
            />
            <div className="flex gap-3 pt-1">
              <Button variant="secondary" className="flex-1" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                className="flex-1"
                onClick={handleRun}
                disabled={!topicId}
                loading={runMutation.isPending}
              >
                <Cpu className="h-4 w-4" />
                Run Pipeline
              </Button>
            </div>
            {runMutation.isError && (
              <p className="text-xs text-red-400 text-center">
                {(runMutation.error as Error)?.message ?? 'Pipeline failed to start'}
              </p>
            )}
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg bg-gray-800/60 border border-gray-700/50 p-4">
              {!isDone ? (
                <Loader2 className="h-5 w-5 text-purple-400 animate-spin flex-shrink-0" />
              ) : statusData?.status === 'completed' ? (
                <CheckCircle2 className="h-5 w-5 text-green-400 flex-shrink-0" />
              ) : (
                <XCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
              )}
              <div>
                <p className="text-sm font-medium text-gray-200">{statusData?.message ?? 'Pipeline queued…'}</p>
                <p className="text-xs text-gray-500 mt-0.5">Log ID: {runLogId.slice(0, 8)}…</p>
              </div>
            </div>

            {statusData?.stages && statusData.stages.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Stages</p>
                {statusData.stages.map((stage, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-gray-800/40 px-3 py-2">
                    <div>
                      <p className="text-xs font-medium text-gray-300 capitalize">{stage.agent_name.replace('_', ' ')}</p>
                      {stage.duration_ms && <p className="text-xs text-gray-600">{stage.duration_ms}ms</p>}
                    </div>
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium border', getAgentStatusColor(stage.status))}>
                      {stage.status}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {isDone && (
              <Button className="w-full" variant="secondary" onClick={handleClose}>
                Close
              </Button>
            )}
          </div>
        )}
      </div>
    </Modal>
  )
}
