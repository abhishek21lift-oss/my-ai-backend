'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard, TrendingUp, BarChart2, BookOpen,
  Zap, FileText, Sparkles, LogOut, X, Cpu, Hash,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/auth-context'
import { useRouter } from 'next/navigation'

const NAV_ITEMS = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/viral-feed', icon: TrendingUp, label: 'Viral Feed' },
  { href: '/trends', icon: BarChart2, label: 'Trend Center' },
  { href: '/trending-keywords', icon: Hash, label: 'Keywords' },
  { href: '/research', icon: BookOpen, label: 'Research' },
  { href: '/hooks', icon: Zap, label: 'Hook Library' },
  { href: '/scripts', icon: FileText, label: 'Script Library' },
  { href: '/recommendations', icon: Sparkles, label: 'Daily Recs' },
]

interface SidebarProps {
  open?: boolean
  onClose?: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname()
  const { logout, apiKey } = useAuth()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const keyPreview = apiKey ? `${apiKey.slice(0, 8)}...${apiKey.slice(-4)}` : '—'

  const content = (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex items-center justify-between px-5 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-violet-700 shadow-lg shadow-purple-900/40">
            <Cpu className="h-4 w-4 text-white" />
          </div>
          <span className="text-base font-bold bg-gradient-to-r from-purple-400 to-violet-300 bg-clip-text text-transparent">
            ViralAI
          </span>
        </div>
        {onClose && (
          <button onClick={onClose} className="rounded-lg p-1 text-gray-500 hover:text-gray-300 hover:bg-gray-800 lg:hidden">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || pathname.startsWith(href + '/')
          return (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all group',
                active
                  ? 'bg-purple-600/20 text-purple-300 border border-purple-500/20'
                  : 'text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'
              )}
            >
              <Icon className={cn('h-4 w-4 flex-shrink-0', active ? 'text-purple-400' : 'text-gray-500 group-hover:text-gray-300')} />
              {label}
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-purple-400" />}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-800 px-4 py-4">
        <div className="mb-3 rounded-lg bg-gray-800/50 border border-gray-700/50 px-3 py-2.5">
          <p className="text-xs text-gray-500 mb-0.5">API Key</p>
          <p className="text-xs font-mono text-gray-400 truncate">{keyPreview}</p>
        </div>
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop */}
      <aside className="hidden lg:flex flex-col w-60 h-screen flex-shrink-0 border-r border-gray-800 bg-gray-900/80 backdrop-blur-sm">
        {content}
      </aside>

      {/* Mobile drawer */}
      {open !== undefined && (
        <>
          {open && <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" onClick={onClose} />}
          <aside className={cn(
            'fixed left-0 top-0 z-50 flex flex-col w-60 h-screen border-r border-gray-800 bg-gray-900 lg:hidden transition-transform duration-200',
            open ? 'translate-x-0' : '-translate-x-full'
          )}>
            {content}
          </aside>
        </>
      )}
    </>
  )
}
