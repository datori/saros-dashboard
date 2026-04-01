import { useState, useEffect, type CSSProperties } from 'react'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Play, Square, Pause, Home, Bell, BatteryCharging, Gauge, Timer, Bot } from 'lucide-react'
import { apiGet, apiPost, fmt } from '@/lib/api'

interface StatusData {
  state: string | null
  battery: number | null
  in_dock: boolean
  error_code: number
  _stale?: boolean
  error?: string
}

interface WindowStatus {
  active: boolean
  remaining_minutes: number
  current_clean?: { segment_ids: number[] }
}

function stateVariant(state: string | null): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (!state) return 'secondary'
  if (state.toLowerCase().includes('clean')) return 'default'
  if (state === 'charging' || state === 'charging_complete') return 'secondary'
  if (state === 'error') return 'destructive'
  return 'outline'
}

const ACTIONS = [
  { name: 'start',  Icon: Play,   title: 'Start',  variant: 'default'     as const, extraClass: '' },
  { name: 'stop',   Icon: Square, title: 'Stop',   variant: 'destructive' as const, extraClass: '' },
  { name: 'pause',  Icon: Pause,  title: 'Pause',  variant: 'secondary'   as const, extraClass: 'bg-yellow-600 hover:bg-yellow-500 text-black border-0' },
  { name: 'dock',   Icon: Home,   title: 'Dock',   variant: 'outline'     as const, extraClass: '' },
  { name: 'locate', Icon: Bell,   title: 'Locate', variant: 'outline'     as const, extraClass: '' },
]

export default function StatusBar({
  refreshKey,
  onStatusChange,
}: {
  refreshKey: number
  onStatusChange: () => void
}) {
  const [data, setData] = useState<StatusData | null>(null)
  const [windowStatus, setWindowStatus] = useState<WindowStatus | null>(null)
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<{ msg: string; ok: boolean } | null>(null)

  useEffect(() => {
    Promise.all([
      apiGet<StatusData>('/api/status'),
      apiGet<WindowStatus>('/api/window').catch(() => null),
    ]).then(([d, w]) => {
      setData(d)
      setWindowStatus(w)
    }).catch(() => {})
  }, [refreshKey])

  async function doAction(name: string) {
    setBusy(true)
    setFeedback(null)
    try {
      const res = await apiPost<{ ok?: boolean; detail?: string }>(`/api/action/${name}`, {})
      setFeedback({ msg: res.ok ? `${name} sent!` : (res.detail ?? 'Error'), ok: !!res.ok })
      if (res.ok && name !== 'locate') setTimeout(onStatusChange, 2000)
    } catch (e) {
      setFeedback({ msg: String(e), ok: false })
    } finally {
      setBusy(false)
      setTimeout(() => setFeedback(null), 4000)
    }
  }

  const battery = data?.battery ?? 0
  const batteryColor = battery > 50 ? '' : battery > 20 ? 'warning' : 'danger'
  const isStale = data?._stale
  const windowLabel = windowStatus?.active ? `${windowStatus.remaining_minutes} min left` : 'No window'

  return (
    <div className={`mb-3 rounded-[1.25rem] border border-white/10 bg-card/80 p-2.5 shadow-[var(--panel-shadow)] backdrop-blur-xl transition-opacity sm:p-3 ${isStale ? 'opacity-60' : ''}`}>
      {!data ? (
        <span className="text-sm text-muted-foreground italic">Loading…</span>
      ) : data.error ? (
        <span className="text-sm text-destructive">Error: {data.error}</span>
      ) : (
        <div className="flex min-w-0 flex-col gap-2.5 xl:flex-row xl:items-center xl:justify-between">
          <div className="rounded-2xl border border-white/8 bg-white/5 p-2.5 sm:hidden">
            <div className="flex min-w-0 items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.16em] text-muted-foreground">
                  <Bot size={13} />
                  Robot Status
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <Badge variant={stateVariant(data.state)} className="shrink-0 text-[10px]">
                    {isStale && '⏱ '}{fmt(data.state)}
                  </Badge>
                  {data.error_code ? (
                    <Badge variant="destructive" className="shrink-0 text-[10px]">Error {data.error_code}</Badge>
                  ) : null}
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  {data.in_dock
                    ? <Badge variant="secondary" className="bg-emerald-950/70 text-[10px] text-emerald-300 border-emerald-700/50">In dock</Badge>
                    : <Badge variant="secondary" className="bg-amber-950/70 text-[10px] text-amber-300 border-amber-700/50">Away</Badge>
                  }
                  <span className={`text-[11px] font-medium ${windowStatus?.active ? 'text-emerald-300' : 'text-slate-300'}`}>
                    {windowLabel}
                  </span>
                </div>
              </div>

              <div className="min-w-[88px] text-right">
                <div className="text-[9px] uppercase tracking-[0.16em] text-muted-foreground">Battery</div>
                <div className="mt-1 flex items-center justify-end gap-2">
                  <div className="w-16">
                    <Progress
                      value={battery}
                      className="h-2"
                      style={batteryColor === 'danger'
                        ? { '--progress-color': 'var(--destructive)' } as CSSProperties
                        : batteryColor === 'warning'
                        ? { '--progress-color': 'oklch(75% 0.18 85)' } as CSSProperties
                        : undefined}
                    />
                  </div>
                  <span className="text-[12px] font-medium text-slate-200">{data.battery ?? '?'}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="hidden min-w-0 gap-2 sm:grid sm:grid-cols-2 xl:grid-cols-4">
            <div className="min-w-0 rounded-2xl border border-white/8 bg-white/5 px-2.5 py-2 sm:px-3 sm:py-2.5">
              <div className="mb-1 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.16em] text-muted-foreground sm:text-[10px] sm:tracking-[0.2em]">
                <Bot size={14} />
                Robot State
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={stateVariant(data.state)} className="shrink-0 text-[10px]">
                  {isStale && '⏱ '}{fmt(data.state)}
                </Badge>
                {data.error_code ? (
                  <Badge variant="destructive" className="shrink-0 text-[10px]">Error {data.error_code}</Badge>
                ) : null}
              </div>
            </div>

            <div className="min-w-0 rounded-2xl border border-white/8 bg-white/5 px-2.5 py-2 sm:px-3 sm:py-2.5">
              <div className="mb-1 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.16em] text-muted-foreground sm:text-[10px] sm:tracking-[0.2em]">
                <Gauge size={14} />
                Docking
              </div>
              {data.in_dock
                ? <Badge variant="secondary" className="bg-emerald-950/70 text-[10px] text-emerald-300 border-emerald-700/50">In dock</Badge>
                : <Badge variant="secondary" className="bg-amber-950/70 text-[10px] text-amber-300 border-amber-700/50">Away</Badge>
              }
            </div>

            <div className="min-w-0 rounded-2xl border border-white/8 bg-white/5 px-2.5 py-2 sm:px-3 sm:py-2.5">
              <div className="mb-1 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.16em] text-muted-foreground sm:text-[10px] sm:tracking-[0.2em]">
                <Timer size={14} />
                Window
              </div>
              <div className={`text-[12px] font-medium sm:text-sm ${windowStatus?.active ? 'text-emerald-300' : 'text-slate-300'}`}>
                {windowLabel}
              </div>
            </div>

            <div className="min-w-0 rounded-2xl border border-white/8 bg-white/5 px-2.5 py-2 sm:px-3 sm:py-2.5">
              <div className="mb-1 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.16em] text-muted-foreground sm:text-[10px] sm:tracking-[0.2em]">
                <BatteryCharging size={14} />
                Battery
              </div>
              <div className="flex items-center gap-2.5">
                <Progress
                  value={battery}
                  className="h-2 flex-1 sm:h-2.5"
                  style={batteryColor === 'danger'
                    ? { '--progress-color': 'var(--destructive)' } as CSSProperties
                    : batteryColor === 'warning'
                    ? { '--progress-color': 'oklch(75% 0.18 85)' } as CSSProperties
                    : undefined}
                />
                <span className="min-w-[38px] text-right text-[12px] font-medium text-slate-200 sm:text-sm">{data.battery ?? '?'}%</span>
              </div>
            </div>
          </div>

          <div className="flex min-w-0 flex-col items-start gap-1.5 xl:items-end">
            {feedback && (
              <span className={`max-w-full text-xs ${feedback.ok ? 'text-emerald-300' : 'text-destructive'}`}>
                {feedback.msg}
              </span>
            )}

            <div className="flex flex-wrap items-center gap-1.5 sm:hidden">
              {ACTIONS.map(({ name, Icon, title, variant, extraClass }) => (
                <Button
                  key={name}
                  variant={variant}
                  size="sm"
                  disabled={busy}
                  title={title}
                  aria-label={title}
                  onClick={() => doAction(name)}
                  className={`h-7 min-w-7 rounded-xl px-2 ${extraClass}`}
                >
                  <Icon size={13} />
                </Button>
              ))}
            </div>

            <div className="hidden flex-wrap items-center gap-1.5 sm:flex">
              {ACTIONS.map(({ name, Icon, title, variant, extraClass }) => (
                <Button
                  key={name}
                  variant={variant}
                  size="sm"
                  disabled={busy}
                  title={title}
                  aria-label={title}
                  onClick={() => doAction(name)}
                  className={`h-8 min-w-8 rounded-xl px-2 sm:h-7 sm:min-w-7 ${extraClass}`}
                >
                  <Icon size={14} />
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
