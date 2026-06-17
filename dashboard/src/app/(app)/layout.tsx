'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'
import { Sidebar } from '@/components/layout/sidebar'
import { Header } from '@/components/layout/header'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/viral-feed': 'Viral Feed',
  '/trends': 'Trend Center',
  '/research': 'Research Center',
  '/hooks': 'Hook Library',
  '/scripts': 'Script Library',
  '/recommendations': 'Daily Recommendations',
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isAuthenticated()) router.replace('/login')
  }, [router])

  const title = PAGE_TITLES[pathname] ?? 'ViralAI'

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
