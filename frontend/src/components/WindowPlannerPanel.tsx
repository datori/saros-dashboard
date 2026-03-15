import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
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
  const targetMode = queue[0]?.mode

  const selected: (QueueEntry & { cumul: number })[] = []
  const excluded: (QueueEntry & { reason: string })[] = []
  let runSec = 0

  for (const entry of queue) {
    if (entry.mode !== targetMode) { excluded.push({ ...entry, reason: 'mode' }); continue }
    const est = entry.estimated_sec
    if (est == null) {
      selected.push({ ...entry, cumul: runSec })
    } else if (runSec + est <= budgetSec) {
      runSec += est
      selected.push({ ...entry, cumul: runSec })
    } else {
      excluded.push({ ...entry, reason: 'budget' })
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
          <Button variant="outline" size="sm" className="h-6 px-2 text-[11px] font-normal" onClick={loadPreview}>Refresh</Button>
        </span>
      }
    >
      {/* Budget slider */}
      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm text-muted-foreground whitespace-nowrap">Budget:</label>
        <input
          type="range"
          min={5}
          max={90}
          step={1}
          value={budget}
          onChange={e => setBudget(parseInt(e.target.value))}
          className="flex-1 accent-primary"
        />
        <span className="text-sm font-semibold min-w-[50px]">{budget} min</span>
      </div>

      {error ? (
        <p className="text-muted-foreground italic text-sm">Preview unavailable: {error}</p>
      ) : queue.length === 0 ? (
        <p className="text-muted-foreground text-sm">No overdue rooms</p>
      ) : (
        <div className="space-y-1.5">
          {selected.map(r => {
            const estMin = r.estimated_sec != null ? `${Math.round(r.estimated_sec / 60)}m` : '?'
            const score = r.priority_score != null ? r.priority_score.toFixed(1) : '∞'
            const pct = budgetSec > 0 ? Math.min(100, (r.cumul / budgetSec) * 100) : 0
            return (
              <div key={r.name} className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
                <span className="min-w-[90px]">{r.name}</span>
                <span className="text-muted-foreground text-[11px] min-w-[30px]">{r.mode}</span>
                <span className="text-muted-foreground text-[11px] min-w-[35px] text-right">{estMin}</span>
                <span className="text-muted-foreground text-[11px] min-w-[35px] text-right">{score}</span>
                <div className="flex-1 h-2.5 bg-border rounded-full overflow-hidden min-w-[60px]">
                  <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct.toFixed(1)}%` }} />
                </div>
              </div>
            )
          })}
          {excluded.length > 0 && (
            <div className="border-t border-dashed border-border my-1.5 pt-1.5 space-y-1.5">
              {excluded.map(r => {
                const estMin = r.estimated_sec != null ? `${Math.round(r.estimated_sec / 60)}m` : '?'
                const note = r.reason === 'mode' ? r.mode : "won't fit"
                return (
                  <div key={r.name} className="flex items-center gap-2 text-sm opacity-50">
                    <span className="w-2 h-2 rounded-full border-2 border-muted-foreground flex-shrink-0" />
                    <span className="min-w-[90px] text-muted-foreground">{r.name}</span>
                    <span className="text-muted-foreground text-[11px] min-w-[30px]">{note}</span>
                    <span className="text-muted-foreground text-[11px] min-w-[35px] text-right">{estMin}</span>
                  </div>
                )
              })}
            </div>
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            {selected.length > 0
              ? `${selected.length} room${selected.length > 1 ? 's' : ''} · ${Math.round(runSec / 60)} min of ${budget} min budget`
              : 'No rooms fit in budget'}
          </p>
        </div>
      )}

      <div className="mt-4">
        <Button onClick={openWindow}>Open Window</Button>
      </div>
    </Panel>
  )
}
