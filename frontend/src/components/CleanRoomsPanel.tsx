import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import Panel from './Panel'
import { apiGet, apiPost } from '@/lib/api'

interface Room { id: number; name: string }

type Scope = 'all' | 'select'

const CLEAN_MODES = [
  { value: '', label: '— no preference —' },
  { value: 'vacuum', label: 'Vacuum only' },
  { value: 'mop', label: 'Mop only' },
  { value: 'both', label: 'Both (simultaneous)' },
  { value: 'vac_then_mop', label: 'Vacuum, then Mop' },
]
const FAN_SPEEDS = ['', 'QUIET', 'BALANCED', 'TURBO', 'MAX', 'MAX_PLUS', 'OFF']
const MOP_MODES = ['', 'STANDARD', 'FAST', 'DEEP', 'DEEP_PLUS']
const WATER_FLOWS = ['', 'OFF', 'LOW', 'MEDIUM', 'HIGH', 'EXTREME', 'VAC_THEN_MOP']
const ROUTES = ['', 'STANDARD', 'FAST', 'DEEP', 'DEEP_PLUS']

function Sel({ id, options, value, onChange }: {
  id: string
  options: string[] | { value: string; label: string }[]
  value: string
  onChange: (v: string) => void
}) {
  const wrap = (v: string | null) => onChange(v ?? '')
  const items = options.map(o => typeof o === 'string' ? { value: o, label: o || '— device default —' } : o)
  return (
    <Select value={value} onValueChange={wrap}>
      <SelectTrigger id={id} className="h-8 text-xs">
        <SelectValue placeholder={items[0].label} />
      </SelectTrigger>
      <SelectContent>
        {items.map(item => (
          <SelectItem key={item.value} value={item.value || '__empty__'}>{item.label}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export default function CleanRoomsPanel({ refreshKey }: { refreshKey: number }) {
  const [rooms, setRooms] = useState<Room[]>([])
  const [scope, setScope] = useState<Scope>('select')
  const [checked, setChecked] = useState<Set<number>>(new Set())
  const [cleanMode, setCleanMode] = useState('')
  const [fanSpeed, setFanSpeed] = useState('')
  const [mopMode, setMopMode] = useState('')
  const [waterFlow, setWaterFlow] = useState('')
  const [route, setRoute] = useState('')
  const [repeat, setRepeat] = useState(1)
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<{ msg: string; ok: boolean } | null>(null)

  useEffect(() => {
    apiGet<Room[]>('/api/rooms').then(r => {
      if (Array.isArray(r)) setRooms(r)
    }).catch(() => {})
  }, [refreshKey])

  function applyCleanMode(mode: string) {
    setCleanMode(mode)
    if (mode === 'vacuum') {
      setFanSpeed('')
      setWaterFlow('OFF')
    } else if (mode === 'mop') {
      setFanSpeed('OFF')
      setWaterFlow('')
    } else if (mode === 'vac_then_mop') {
      setFanSpeed('')
      setWaterFlow('VAC_THEN_MOP')
    } else {
      setFanSpeed('')
      setWaterFlow('')
    }
  }

  function toggleRoom(id: number) {
    setChecked(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  async function startClean() {
    setBusy(true)
    setFeedback(null)
    try {
      let res: { ok?: boolean; detail?: string }
      if (scope === 'all') {
        const body: Record<string, string> = {}
        if (fanSpeed) body.fan_speed = fanSpeed
        if (waterFlow) body.water_flow = waterFlow
        res = await apiPost('/api/action/start', body)
      } else {
        if (!checked.size) { setFeedback({ msg: 'Select at least one room.', ok: false }); setBusy(false); return }
        const body: Record<string, unknown> = { segment_ids: [...checked], repeat }
        if (fanSpeed) body.fan_speed = fanSpeed
        if (mopMode) body.mop_mode = mopMode
        if (waterFlow) body.water_flow = waterFlow
        if (route) body.route = route
        res = await apiPost('/api/rooms/clean', body)
      }
      setFeedback({ msg: res.ok ? 'Cleaning started!' : (res.detail ?? 'Error'), ok: !!res.ok })
    } catch (e) {
      setFeedback({ msg: String(e), ok: false })
    } finally {
      setBusy(false)
      setTimeout(() => setFeedback(null), 4000)
    }
  }

  const realVal = (v: string) => v === '__empty__' ? '' : v
  const selectedCount = checked.size

  return (
    <Panel title="Manual Dispatch">
      <div className="space-y-4">
        <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Scope</div>
              <p className="mt-1 text-sm text-slate-300">Run a full clean or dispatch selected rooms.</p>
            </div>
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] text-slate-300">
              {scope === 'all' ? 'All rooms' : `${selectedCount} selected`}
            </span>
          </div>

          <RadioGroup
            value={scope}
            onValueChange={(v) => setScope(v as Scope)}
            className="grid grid-cols-2 gap-2"
          >
            <Label htmlFor="scope-all" className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/8 bg-slate-950/35 px-3 py-2.5 font-normal">
              <RadioGroupItem value="all" id="scope-all" />
              <span>All rooms</span>
            </Label>
            <Label htmlFor="scope-select" className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/8 bg-slate-950/35 px-3 py-2.5 font-normal">
              <RadioGroupItem value="select" id="scope-select" />
              <span>Select rooms</span>
            </Label>
          </RadioGroup>
        </div>

        {scope === 'select' && (
          <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Rooms</div>
              <span className="text-[11px] text-muted-foreground">{rooms.length} available</span>
            </div>

            <div className="grid max-h-48 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
              {rooms.length === 0
                ? <p className="text-sm italic text-muted-foreground">Loading…</p>
                : rooms.map(r => (
                  <Label
                    key={r.id}
                    htmlFor={`room-${r.id}`}
                    className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/8 bg-slate-950/35 px-3 py-2 font-normal"
                  >
                    <Checkbox
                      id={`room-${r.id}`}
                      checked={checked.has(r.id)}
                      onCheckedChange={() => toggleRoom(r.id)}
                    />
                    <span className="min-w-0 truncate">{r.name}</span>
                  </Label>
                ))
              }
            </div>
          </div>
        )}

        <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-3">
          <div className="mb-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Overrides</div>
            <p className="mt-1 text-sm text-slate-300">Optional mode and route overrides for this run.</p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <Label className="text-[11px] text-muted-foreground">Clean Mode</Label>
              <Sel id="rooms-clean-mode" options={CLEAN_MODES} value={cleanMode} onChange={v => applyCleanMode(realVal(v))} />
            </div>
            <div>
              <Label className="text-[11px] text-muted-foreground">Fan Speed</Label>
              <Sel id="rooms-fan-speed" options={FAN_SPEEDS} value={fanSpeed} onChange={v => setFanSpeed(realVal(v))} />
            </div>
            <div>
              <Label className="text-[11px] text-muted-foreground">Mop Mode</Label>
              <Sel id="rooms-mop-mode" options={MOP_MODES} value={mopMode} onChange={v => setMopMode(realVal(v))} />
            </div>
            <div>
              <Label className="text-[11px] text-muted-foreground">Water Flow</Label>
              <Sel id="rooms-water-flow" options={WATER_FLOWS} value={waterFlow} onChange={v => setWaterFlow(realVal(v))} />
            </div>
            <div className="sm:max-w-[220px]">
              <Label className="text-[11px] text-muted-foreground">Route</Label>
              <Sel id="rooms-route" options={ROUTES} value={route} onChange={v => setRoute(realVal(v))} />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/8 bg-white/[0.04] p-3">
          <div className="flex items-center gap-2">
            <Label className="whitespace-nowrap text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Repeat</Label>
            <input
              type="number"
              value={repeat}
              min={1}
              max={3}
              onChange={e => setRepeat(parseInt(e.target.value) || 1)}
              className="w-16 rounded-lg border border-border bg-background px-2 py-1.5 text-sm text-foreground"
            />
          </div>
          <Button onClick={startClean} disabled={busy} className="rounded-xl px-4">
            {busy ? 'Starting…' : 'Start Clean'}
          </Button>
        </div>

        {feedback && (
          <p className={`text-xs ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>{feedback.msg}</p>
        )}
      </div>
    </Panel>
  )
}
