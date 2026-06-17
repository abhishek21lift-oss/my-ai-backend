import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  action?: React.ReactNode
  hover?: boolean
}

export function Card({ children, className, title, action, hover = false }: CardProps) {
  return (
    <div className={cn(
      'rounded-xl border border-gray-800 bg-gray-900',
      hover && 'transition-all hover:border-gray-700 hover:bg-gray-800/70 cursor-pointer',
      className
    )}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
          {title && <h3 className="text-sm font-semibold text-gray-200">{title}</h3>}
          {action && <div className="text-gray-400">{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
