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
    <div
      className={cn(
        'rounded-[1.4rem] border border-white/10 bg-card/85 p-5 shadow-[var(--panel-shadow)] backdrop-blur-xl',
        'before:pointer-events-none before:absolute before:inset-px before:rounded-[calc(1.4rem-1px)] before:border before:border-white/5 before:content-[""]',
        'relative overflow-hidden',
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className={cn('mb-4 flex min-w-0 flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-muted-foreground', titleClassName, stale && 'opacity-60')}>
        {title}
        {stale && <span className="rounded-full border border-white/10 bg-white/5 px-1.5 py-0.5 text-[9px]">Stale</span>}
      </div>
      {children}
    </div>
  )
}
