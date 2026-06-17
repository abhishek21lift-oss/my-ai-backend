'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/auth-context'
import { Cpu, Key, AlertCircle, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function LoginPage() {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = key.trim()
    if (!trimmed.startsWith('sk-')) {
      setError('API key must start with "sk-"')
      return
    }
    if (trimmed.length < 10) {
      setError('API key is too short')
      return
    }
    login(trimmed)
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-violet-700 shadow-xl shadow-purple-900/50 mb-4">
            <Cpu className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-violet-300 bg-clip-text text-transparent">
            ViralAI
          </h1>
          <p className="text-sm text-gray-500 mt-1">AI-powered viral content creation</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-7 shadow-2xl">
          <h2 className="text-base font-semibold text-gray-100 mb-1">Sign in to your dashboard</h2>
          <p className="text-sm text-gray-500 mb-6">Enter your API key to access all features</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-..."
              value={key}
              onChange={e => { setKey(e.target.value); setError('') }}
              icon={<Key className="h-3.5 w-3.5" />}
              error={error}
              autoComplete="off"
              autoFocus
            />

            <Button type="submit" className="w-full" size="md" loading={false}>
              Continue to Dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          {/* Help */}
          <div className="mt-5 rounded-lg bg-gray-800/50 border border-gray-700/50 p-3.5">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="h-3.5 w-3.5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-medium text-gray-300 mb-1">How to get an API key</p>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Use <code className="text-purple-400 bg-gray-800 px-1 rounded">POST /api/v1/auth/keys</code> with your backend to generate an API key, then paste it here.
                </p>
              </div>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-5">
          Your key is stored locally and never sent to third parties.
        </p>
      </div>
    </div>
  )
}
