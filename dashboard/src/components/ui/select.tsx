import { cn } from '@/lib/utils'
import { forwardRef } from 'react'

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: { value: string; label: string }[]
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, placeholder, className, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-xs font-medium text-gray-400">{label}</label>}
      <select
        ref={ref}
        className={cn(
          'bg-gray-800/60 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200',
          'focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all',
          'appearance-none cursor-pointer',
          className
        )}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(opt => (
          <option key={opt.value} value={opt.value} className="bg-gray-900">
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
)
Select.displayName = 'Select'
