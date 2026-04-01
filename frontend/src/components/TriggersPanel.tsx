import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import Panel from './Panel'
import TriggerModal from './TriggerModal'
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'

interface Trigger { name: string; budget_min: number; mode: string; notes: string }
interface WindowStatus { active: boolean; remaining_minutes: number; current_clean?: { segment_ids: number[] } }

const FAN_SPEEDS  = ['off','quiet','balanced','turbo','max','max_plus','smart']
const MOP_MODES   = ['standard','fast','deep','deep_plus','smart']
const WATER_FLOWS = ['off','low','medium','high','extreme','smart']
const ROUTES      = ['standard','fast','deep','deep_plus','smart']

function DispatchSelect({ mode, field, value, options }: {
  mode: string; field: string; value: string | null; options: string[]
  onChange?: (v: string | null) => void
}) {
  async function handleChange(val: string) {
    const realVal = val === '__empty__' ? null : val
    await apiPatch(`/api/dispatch-settings/${mode}`, { [field]: realVal })
  }
  return (
    <Select value={value ?? '__empty__'} onValueChange={v => handleChange(v ?? '__empty__')}>
      <SelectTrigger className="h-7 text-xs"><SelectValue placeholder="—" /></SelectTrigger>
      <SelectContent>
        <SelectItem value="__empty__">—</SelectItem>
        {options.map(o => <SelectItem key={o} value={o}>{o.replace(/_/g, ' ')}</SelectItem>)}
      </SelectContent>
    </Select>
  )
}

export default function TriggersPanel({ refreshKey }: { refreshKey: number }) {
  const [triggers, setTriggers] = useState<Trigger[]>([])
  const [windowStatus, setWindowStatus] = useState<WindowStatus | null>(null)
  const [dispatchSettings, setDispatchSettings] = useState<Record<string, Record<string, string | null>>>({})
  const [feedback, setFeedback] = useState<{ msg: string; ok: boolean } | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTrigger, setEditingTrigger] = useState<Trigger | null>(null)

  async function load() {
    const [t, w, d] = await Promise.all([
      apiGet<Trigger[]>('/api/triggers').catch(() => []),
      apiGet<WindowStatus>('/api/window').catch(() => null),
      apiGet<Record<string, Record<string, string | null>>>('/api/dispatch-settings').catch(() => ({})),
    ])
    setTriggers(Array.isArray(t) ? t : [])
    setWindowStatus(w)
    setDispatchSettings(d)
  }

  useEffect(() => { load() }, [refreshKey])

  async function fireTrigger(name: string) {
    const res = await apiPost<{ ok?: boolean; detail?: string; window?: { remaining_minutes: number } }>(`/api/trigger/${encodeURIComponent(name)}/fire`)
    if (res.ok) {
      setFeedback({ msg: `${name} fired! Window: ${res.window?.remaining_minutes}min`, ok: true })
      const w = await apiGet<WindowStatus>('/api/window').catch(() => null)
      setWindowStatus(w)
    } else {
      setFeedback({ msg: res.detail ?? 'Error', ok: false })
    }
    setTimeout(() => setFeedback(null), 4000)
  }

  async function stopWindow() {
    const res = await apiPost<{ ok?: boolean; detail?: string }>('/api/trigger/stop')
    setFeedback({ msg: res.ok ? 'Window closed, vacuum docking' : (res.detail ?? 'Error'), ok: !!res.ok })
    const w = await apiGet<WindowStatus>('/api/window').catch(() => null)
    setWindowStatus(w)
    setTimeout(() => setFeedback(null), 4000)
  }

  async function deleteTrigger(name: string) {
    if (!confirm(`Delete trigger "${name}"?`)) return
    await apiDelete(`/api/triggers/${encodeURIComponent(name)}`)
    load()
  }

  return (
    <Panel title="Auto-Clean Triggers">
      <div className="space-y-4">
        <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Quick Fire</div>
              <p className="mt-1 text-sm text-slate-300">Open a cleaning window from a saved trigger.</p>
            </div>
            {triggers.length > 0 && (
              <Button variant="destructive" size="sm" className="h-8 rounded-xl px-3 text-xs" onClick={stopWindow}>
                Stop Window
              </Button>
            )}
          </div>

          <div className="grid gap-2 sm:grid-cols-2">
            {triggers.map(t => (
              <button
                key={t.name}
                onClick={() => fireTrigger(t.name)}
                className="flex min-w-0 items-center justify-between rounded-xl border border-sky-400/20 bg-sky-500/10 px-3 py-2 text-left transition hover:bg-sky-500/14"
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-slate-100">{t.name}</span>
                  <span className="text-[11px] text-sky-200/85">{t.budget_min} min window</span>
                </span>
                <span className="rounded-full border border-sky-400/20 bg-slate-950/35 px-2 py-0.5 text-[10px] text-sky-100">
                  Fire
                </span>
              </button>
            ))}
            {triggers.length === 0 && <p className="text-sm italic text-muted-foreground">No triggers configured yet.</p>}
          </div>

          {windowStatus && (
            <div
              className="mt-3 rounded-xl px-3 py-2 text-sm"
              style={windowStatus.active
                ? { background: '#1e3a2a', border: '1px solid #22c55e', color: '#86efac' }
                : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--color-muted-foreground)' }
              }
            >
              {windowStatus.active
                ? `Window active · ${windowStatus.remaining_minutes} min remaining${windowStatus.current_clean ? ` · Cleaning ${windowStatus.current_clean.segment_ids.length} room(s)` : ''}`
                : 'No active window'}
            </div>
          )}

          {feedback && (
            <p className={`mt-2 text-xs ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>{feedback.msg}</p>
          )}
        </div>

        <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Manage Triggers</div>
            <Button size="sm" className="h-8 rounded-xl px-3 text-xs" onClick={() => { setEditingTrigger(null); setModalOpen(true) }}>Add Trigger</Button>
          </div>

          <div className="space-y-2">
            {triggers.map(t => (
              <div key={t.name} className="flex items-start justify-between gap-3 rounded-xl border border-white/8 bg-slate-950/35 px-3 py-2.5">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-100">{t.name}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">{t.budget_min} min · {t.mode}{t.notes ? ` · ${t.notes}` : ''}</p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button variant="outline" size="sm" className="h-7 rounded-lg px-2 text-xs" onClick={() => { setEditingTrigger(t); setModalOpen(true) }}>Edit</Button>
                  <Button variant="destructive" size="sm" className="h-7 rounded-lg px-2 text-xs" onClick={() => deleteTrigger(t.name)}>Del</Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
          <div className="mb-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Dispatch Defaults</div>
            <p className="mt-1 text-sm text-slate-300">Default settings applied when triggers fire vacuum or mop dispatches.</p>
          </div>
          {(['vacuum', 'mop'] as const).map(m => {
            const s = dispatchSettings[m] ?? {}
            return (
              <div key={m} className="mt-3 rounded-xl border border-white/8 bg-slate-950/35 p-3 first:mt-0">
                <p className="mb-2 text-xs font-semibold capitalize text-slate-100">{m}</p>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <span className="mb-1 block text-[11px] text-muted-foreground">Fan speed</span>
                    <DispatchSelect mode={m} field="fan_speed" value={s.fan_speed ?? null} options={FAN_SPEEDS} />
                  </div>
                  <div>
                    <span className="mb-1 block text-[11px] text-muted-foreground">Mop mode</span>
                    <DispatchSelect mode={m} field="mop_mode" value={s.mop_mode ?? null} options={MOP_MODES} />
                  </div>
                  <div>
                    <span className="mb-1 block text-[11px] text-muted-foreground">Water flow</span>
                    <DispatchSelect mode={m} field="water_flow" value={s.water_flow ?? null} options={WATER_FLOWS} />
                  </div>
                  <div>
                    <span className="mb-1 block text-[11px] text-muted-foreground">Route</span>
                    <DispatchSelect mode={m} field="route" value={s.route ?? null} options={ROUTES} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <TriggerModal
        open={modalOpen}
        editing={editingTrigger}
        onClose={() => setModalOpen(false)}
        onSaved={load}
      />
    </Panel>
  )
}
