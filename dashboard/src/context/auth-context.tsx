'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { getApiKey, setApiKey as saveKey, removeApiKey } from '@/lib/auth'

interface AuthContextValue {
  apiKey: string | null
  login: (key: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null)

  useEffect(() => {
    setApiKey(getApiKey())
  }, [])

  const login = (key: string) => {
    saveKey(key)
    setApiKey(key)
  }

  const logout = () => {
    removeApiKey()
    setApiKey(null)
  }

  return (
    <AuthContext.Provider value={{ apiKey, login, logout, isAuthenticated: !!apiKey }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
