'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/auth-context'
import { Cpu, Key, AlertCircle, ArrowRight, UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export default function LoginPage() {
  const [tab, setTab] = useState<'login' | 'register'>('login')

  // Login state
  const [key, setKey] = useState('')
  const [loginError, setLoginError] = useState('')

  // Register state
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [registerError, setRegisterError] = useState('')
  const [registering, setRegistering] = useState(false)
  const [newKey, setNewKey] = useState('')

  const { login } = useAuth()
  const router = useRouter()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = key.trim()
    if (!trimmed.startsWith('sk-')) {
      setLoginError('API key must start with "sk-"')
      return
    }
    if (trimmed.length < 10) {
      setLoginError('API key is too short')
      return
    }
    login(trimmed)
    router.push('/dashboard')
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) {
      setRegisterError('Email is required')
      return
    }
    setRegistering(true)
    setRegisterError('')
    try {
      const res = await fetch(`${BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), display_name: displayName.trim() || undefined }),
      })
      if (res.status === 409) {
        setRegisterError('Email already registered — use Sign In instead')
        return
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setRegisterError(data?.detail || 'Registration failed')
        return
      }
      const data = await res.json()
      setNewKey(data.api_key)
    } catch {
      setRegisterError('Could not reach the server. Check NEXT_PUBLIC_API_URL.')
    } finally {
      setRegistering(false)
    }
  }

  const handleUseKey = () => {
    login(newKey)
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
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
          {/* Tabs */}
          <div className="flex rounded-lg bg-gray-800/60 p-1 mb-6 gap-1">
            <button
              onClick={() => setTab('login')}
              className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'login' ? 'bg-gray-700 text-gray-100' : 'text-gray-500 hover:text-gray-300'}`}
            >
              Sign In
            </button>
            <button
              onClick={() => setTab('register')}
              className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'register' ? 'bg-gray-700 text-gray-100' : 'text-gray-500 hover:text-gray-300'}`}
            >
              Register
            </button>
          </div>

          {/* ── Sign In ── */}
          {tab === 'login' && (
            <>
              <p className="text-sm text-gray-500 mb-5">Paste your ViralAI API key to access the dashboard</p>
              <form onSubmit={handleLogin} className="space-y-4">
                <Input
                  label="API Key"
                  type="password"
                  placeholder="sk-..."
                  value={key}
                  onChange={e => { setKey(e.target.value); setLoginError('') }}
                  icon={<Key className="h-3.5 w-3.5" />}
                  error={loginError}
                  autoComplete="off"
                  autoFocus
                />
                <Button type="submit" className="w-full" size="md" loading={false}>
                  Continue to Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </form>
              <p className="text-xs text-gray-600 text-center mt-4">
                No account yet?{' '}
                <button onClick={() => setTab('register')} className="text-purple-400 hover:text-purple-300">
                  Register here
                </button>
              </p>
            </>
          )}

          {/* ── Register ── */}
          {tab === 'register' && !newKey && (
            <>
              <p className="text-sm text-gray-500 mb-5">Create a free account — your API key will be shown once</p>
              <form onSubmit={handleRegister} className="space-y-4">
                <Input
                  label="Email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => { setEmail(e.target.value); setRegisterError('') }}
                  autoFocus
                />
                <Input
                  label="Display Name (optional)"
                  type="text"
                  placeholder="Your name"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                />
                {registerError && (
                  <div className="flex items-start gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2.5">
                    <AlertCircle className="h-3.5 w-3.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-red-400">{registerError}</p>
                  </div>
                )}
                <Button type="submit" className="w-full" size="md" loading={registering}>
                  <UserPlus className="h-4 w-4" />
                  Create Account
                </Button>
              </form>
            </>
          )}

          {/* ── Key revealed after register ── */}
          {tab === 'register' && newKey && (
            <div className="space-y-4">
              <div className="rounded-lg bg-green-500/10 border border-green-500/20 p-4">
                <p className="text-xs font-medium text-green-400 mb-2">Account created! Save this key — shown once only.</p>
                <code className="block text-xs font-mono text-gray-200 break-all bg-gray-800 rounded-md px-3 py-2.5 select-all">
                  {newKey}
                </code>
              </div>
              <Button onClick={handleUseKey} className="w-full" size="md">
                Go to Dashboard
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        <p className="text-center text-xs text-gray-600 mt-5">
          Your key is stored locally and never sent to third parties.
        </p>
      </div>
    </div>
  )
}
