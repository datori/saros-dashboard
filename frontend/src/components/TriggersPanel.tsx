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
      {/* Fire buttons */}
      <div className="flex flex-wrap gap-2 mb-3">
        {triggers.map(t => (
          <button
            key={t.name}
            onClick={() => fireTrigger(t.name)}
            className="px-3 py-1.5 rounded-lg text-sm font-medium cursor-pointer transition-colors"
            style={{ background: '#1e3a5e', color: '#4f8ef7', border: '1px solid #4f8ef7' }}
          >
            {t.name} ({t.budget_min}m)
          </button>
        ))}
        {triggers.length > 0 && (
          <button
            onClick={stopWindow}
            className="px-3 py-1.5 rounded-lg text-sm font-medium cursor-pointer"
            style={{ background: '#3d1515', color: '#ef4444', border: '1px solid #ef4444' }}
          >
            Stop
          </button>
        )}
      </div>

      {/* Window status */}
      {windowStatus && (
        <div
          className="rounded-lg px-3 py-2 text-sm mb-3"
          style={windowStatus.active
            ? { background: '#1e3a2a', border: '1px solid #22c55e', color: '#22c55e' }
            : { background: 'var(--color-border)', color: 'var(--color-muted-foreground)' }
          }
        >
          {windowStatus.active
            ? `Window active — ${windowStatus.remaining_minutes} min remaining${windowStatus.current_clean ? ` · Cleaning ${windowStatus.current_clean.segment_ids.length} room(s)` : ''}`
            : 'No active window'
          }
        </div>
      )}

      {feedback && (
        <p className={`text-xs mb-3 ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>{feedback.msg}</p>
      )}

      {/* Manage triggers */}
      <div className="border-t border-border pt-3 mt-1">
        <div className="flex justify-between items-center mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Manage Triggers</span>
          <Button size="sm" className="h-7 px-2 text-xs" onClick={() => { setEditingTrigger(null); setModalOpen(true) }}>+ Add</Button>
        </div>
        {triggers.map(t => (
          <div key={t.name} className="flex justify-between items-center py-1.5 border-b border-border last:border-0">
            <div>
              <p className="font-medium text-sm">{t.name}</p>
              <p className="text-[11px] text-muted-foreground">{t.budget_min}min · {t.mode}{t.notes ? ' · ' + t.notes : ''}</p>
            </div>
            <div className="flex gap-1">
              <Button variant="outline" size="sm" className="h-7 px-2 text-xs" onClick={() => { setEditingTrigger(t); setModalOpen(true) }}>Edit</Button>
              <Button variant="destructive" size="sm" className="h-7 px-2 text-xs" onClick={() => deleteTrigger(t.name)}>Del</Button>
            </div>
          </div>
        ))}
        {triggers.length === 0 && <p className="text-muted-foreground italic text-sm">No triggers configured yet.</p>}
      </div>

      {/* Dispatch settings */}
      <div className="border-t border-border pt-3 mt-3">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Dispatch Settings</span>
        {(['vacuum', 'mop'] as const).map(m => {
          const s = dispatchSettings[m] ?? {}
          return (
            <div key={m} className="mt-2">
              <p className="text-xs font-semibold capitalize mb-1">{m}</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <span className="text-muted-foreground self-center">Fan speed</span>
                <DispatchSelect mode={m} field="fan_speed" value={s.fan_speed ?? null} options={FAN_SPEEDS} />
                <span className="text-muted-foreground self-center">Mop mode</span>
                <DispatchSelect mode={m} field="mop_mode" value={s.mop_mode ?? null} options={MOP_MODES} />
                <span className="text-muted-foreground self-center">Water flow</span>
                <DispatchSelect mode={m} field="water_flow" value={s.water_flow ?? null} options={WATER_FLOWS} />
                <span className="text-muted-foreground self-center">Route</span>
                <DispatchSelect mode={m} field="route" value={s.route ?? null} options={ROUTES} />
              </div>
            </div>
          )
        })}
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
