import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PanelProps {
  title: ReactNode
  children: ReactNode
  className?: string
  titleClassName?: string
  stale?: boolean
}

export default function Panel({ title, children, className, titleClassName, stale }: PanelProps) {
  return (
    <div className={cn('bg-card border border-border rounded-xl p-5', className)}>
      <div className={cn('text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-1.5', titleClassName, stale && 'opacity-60')}>
        {title}
        {stale && <span className="text-[10px]">⏱</span>}
      </div>
      {children}
    </div>
  )
}
