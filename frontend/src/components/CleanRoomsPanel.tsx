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
    if (mode === 'vacuum') { setFanSpeed(''); setWaterFlow('OFF') }
    else if (mode === 'mop') { setFanSpeed('OFF'); setWaterFlow('') }
    else if (mode === 'vac_then_mop') { setFanSpeed(''); setWaterFlow('VAC_THEN_MOP') }
    else { setFanSpeed(''); setWaterFlow('') }
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

  return (
    <Panel title="Clean Rooms">
      {/* Scope toggle */}
      <RadioGroup
        value={scope}
        onValueChange={(v) => setScope(v as Scope)}
        className="flex gap-4 mb-4"
      >
        <div className="flex items-center gap-1.5">
          <RadioGroupItem value="all" id="scope-all" />
          <Label htmlFor="scope-all" className="cursor-pointer font-normal">All rooms</Label>
        </div>
        <div className="flex items-center gap-1.5">
          <RadioGroupItem value="select" id="scope-select" />
          <Label htmlFor="scope-select" className="cursor-pointer font-normal">Select rooms</Label>
        </div>
      </RadioGroup>

      {/* Room list */}
      {scope === 'select' && (
        <div className="flex flex-col gap-1.5 max-h-44 overflow-y-auto mb-4">
          {rooms.length === 0
            ? <p className="text-muted-foreground italic text-sm">Loading…</p>
            : rooms.map(r => (
              <div key={r.id} className="flex items-center gap-2">
                <Checkbox
                  id={`room-${r.id}`}
                  checked={checked.has(r.id)}
                  onCheckedChange={() => toggleRoom(r.id)}
                />
                <Label htmlFor={`room-${r.id}`} className="cursor-pointer font-normal">{r.name}</Label>
              </div>
            ))
          }
        </div>
      )}

      {/* Override settings */}
      <div className="text-[11px] text-muted-foreground mb-2">Override settings (optional)</div>
      <div className="grid grid-cols-2 gap-2 mb-4">
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
        <div>
          <Label className="text-[11px] text-muted-foreground">Route</Label>
          <Sel id="rooms-route" options={ROUTES} value={route} onChange={v => setRoute(realVal(v))} />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Label className="text-muted-foreground whitespace-nowrap">Repeat:</Label>
        <input
          type="number"
          value={repeat}
          min={1}
          max={3}
          onChange={e => setRepeat(parseInt(e.target.value) || 1)}
          className="w-16 bg-background border border-border rounded px-2 py-1 text-sm text-foreground"
        />
        <Button onClick={startClean} disabled={busy} size="sm">Start Clean</Button>
      </div>
      {feedback && (
        <p className={`text-xs mt-2 ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>{feedback.msg}</p>
      )}
    </Panel>
  )
}
