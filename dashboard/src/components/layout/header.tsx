'use client'

import { useState } from 'react'
import { Menu, Cpu, Key } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PipelineModal } from './pipeline-modal'
import { useAuth } from '@/context/auth-context'

interface HeaderProps {
  title: string
  onMenuClick: () => void
}

export function Header({ title, onMenuClick }: HeaderProps) {
  const [pipelineOpen, setPipelineOpen] = useState(false)
  const { apiKey } = useAuth()

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="rounded-lg p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="text-sm font-semibold text-gray-200">{title}</h1>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-1.5 rounded-lg bg-gray-800/60 border border-gray-700/50 px-3 py-1.5">
            <Key className="h-3 w-3 text-green-400" />
            <span className="text-xs text-gray-500 font-mono">
              {apiKey ? `${apiKey.slice(0, 6)}…` : 'No key'}
            </span>
          </div>
          <Button size="sm" onClick={() => setPipelineOpen(true)}>
            <Cpu className="h-3.5 w-3.5" />
            Run Pipeline
          </Button>
        </div>
      </header>
      <PipelineModal open={pipelineOpen} onClose={() => setPipelineOpen(false)} />
    </>
  )
}
