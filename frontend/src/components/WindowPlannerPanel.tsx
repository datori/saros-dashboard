import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Gauge, Clock3, Sparkles } from 'lucide-react'
import Panel from './Panel'
import { apiGet, apiPost } from '@/lib/api'

interface QueueEntry {
  name: string
  mode: string
  estimated_sec: number | null
  priority_score: number | null
}

interface PlannerPreview { queue: QueueEntry[] }

export default function WindowPlannerPanel() {
  const [queue, setQueue] = useState<QueueEntry[]>([])
  const [budget, setBudget] = useState(30)
  const [error, setError] = useState<string | null>(null)

  async function loadPreview() {
    try {
      const data = await apiGet<PlannerPreview>('/api/window/preview')
      setQueue(data.queue ?? [])
      setError(null)
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => { loadPreview() }, [])

  const budgetSec = budget * 60

  const selected: (QueueEntry & { cumul: number })[] = []
  const excluded: (QueueEntry & { reason: string })[] = []
  const targetMode = queue[0]?.mode ?? null
  let runSec = 0

  for (const entry of queue) {
    if (targetMode && entry.mode !== targetMode) {
      excluded.push({ ...entry, reason: `${entry.mode} queued behind ${targetMode}` })
      continue
    }
    const est = entry.estimated_sec
    if (est == null) {
      selected.push({ ...entry, cumul: runSec })
    } else if (runSec + est <= budgetSec) {
      runSec += est
      selected.push({ ...entry, cumul: runSec })
    } else {
      excluded.push({ ...entry, reason: 'outside budget' })
    }
  }

  async function openWindow() {
    await apiPost('/api/window/open', { budget_min: budget })
  }

  return (
    <Panel
      title={
        <span className="flex items-center gap-2">
          Window Planner
          <Button variant="outline" size="sm" className="h-7 rounded-lg border-white/10 bg-white/5 px-2.5 text-[11px] font-normal hover:bg-white/10" onClick={loadPreview}>Refresh</Button>
        </span>
      }
    >
      <div className="mb-4 rounded-2xl border border-white/8 bg-white/5 p-4">
        <div className="mb-3 flex items-start justify-between gap-4">
          <div>
            <div className="mb-1 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
              <Gauge size={14} />
              Budget
            </div>
            <p className="text-sm text-slate-300">Choose how much time this cleaning window can spend before lower-priority rooms are deferred.</p>
          </div>
          <div className="rounded-xl border border-primary/25 bg-primary/10 px-3 py-2 text-right">
            <div className="text-[10px] uppercase tracking-[0.2em] text-sky-200/70">Available</div>
            <div className="text-lg font-semibold text-white">{budget}<span className="ml-1 text-sm text-slate-300">min</span></div>
          </div>
        </div>

        <input
          type="range"
          min={5}
          max={90}
          step={1}
          value={budget}
          onChange={e => setBudget(parseInt(e.target.value))}
          className="flex-1 accent-primary"
        />
      </div>

      {error ? (
        <p className="text-muted-foreground italic text-sm">Preview unavailable: {error}</p>
      ) : queue.length === 0 ? (
        <p className="text-muted-foreground text-sm">No rooms are due today or overdue.</p>
      ) : (
        <div className="space-y-2">
          {targetMode && (
            <p className="text-[11px] text-muted-foreground">
              Preview is locked to the highest-priority <span className="uppercase">{targetMode}</span> batch, matching auto-dispatch.
            </p>
          )}
          {selected.map(r => {
            const estMin = r.estimated_sec != null ? `${Math.round(r.estimated_sec / 60)}m` : '?'
            const score = r.priority_score != null ? r.priority_score.toFixed(1) : '∞'
            const pct = budgetSec > 0 ? Math.min(100, (r.cumul / budgetSec) * 100) : 0
            return (
              <div key={r.name} className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
                <div className="mb-2 flex items-center gap-2 text-sm">
                  <span className="h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_16px_rgba(96,165,250,0.6)]" />
                  <span className="flex-1 font-medium text-slate-100">{r.name}</span>
                  <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-[0.18em] text-slate-300">{r.mode}</span>
                </div>
                <div className="mb-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1"><Clock3 size={12} />{estMin}</span>
                  <span className="flex items-center gap-1"><Sparkles size={12} />Score {score}</span>
                </div>
                <div className="h-2.5 min-w-[60px] overflow-hidden rounded-full bg-border/70">
                  <div className="h-full rounded-full bg-[linear-gradient(90deg,rgba(96,165,250,1),rgba(125,211,252,0.82))] transition-all" style={{ width: `${pct.toFixed(1)}%` }} />
                </div>
              </div>
            )
          })}
          {excluded.length > 0 && (
            <div className="space-y-2 border-t border-dashed border-border pt-3">
              {excluded.map(r => {
                const estMin = r.estimated_sec != null ? `${Math.round(r.estimated_sec / 60)}m` : '?'
                return (
                  <div key={r.name} className="flex items-center gap-2 rounded-xl border border-dashed border-white/8 bg-white/[0.025] px-3 py-2 text-sm opacity-60">
                    <span className="h-2.5 w-2.5 rounded-full border border-muted-foreground" />
                    <span className="flex-1 text-muted-foreground">{r.name}</span>
                    <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{r.mode}</span>
                    <span className="text-[11px] text-muted-foreground">{estMin}</span>
                    <span className="text-[10px] text-muted-foreground">{r.reason}</span>
                  </div>
                )
              })}
            </div>
          )}
          <p className="mt-2 text-[11px] text-muted-foreground">
            {selected.length > 0
              ? `${selected.length} room${selected.length > 1 ? 's' : ''} · ${Math.round(runSec / 60)} min of ${budget} min budget`
              : 'No rooms fit in budget'}
          </p>
        </div>
      )}

      <div className="mt-4">
        <Button onClick={openWindow} className="h-10 rounded-xl px-4">Open Window</Button>
      </div>
    </Panel>
  )
}
