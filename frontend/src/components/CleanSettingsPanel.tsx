import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import Panel from './Panel'
import { apiGet, apiPost } from '@/lib/api'

interface Settings { fan_speed: string; mop_mode: string; water_flow: string; _stale?: boolean; error?: string }

const FAN_SPEEDS  = ['QUIET','BALANCED','TURBO','MAX','MAX_PLUS','OFF','SMART']
const MOP_MODES   = ['STANDARD','FAST','DEEP','DEEP_PLUS','SMART']
const WATER_FLOWS = ['OFF','LOW','MEDIUM','HIGH','EXTREME','VAC_THEN_MOP','SMART']

function SettingSelect({ id, label, options, value, onChange }: {
  id: string; label: string; options: string[]; value: string; onChange: (v: string) => void
}) {
  return (
    <div className="space-y-1">
      <Label htmlFor={id} className="text-[11px] text-muted-foreground">{label}</Label>
      <Select value={value || '__default__'} onValueChange={v => onChange(v == null || v === '__default__' ? '' : v)}>
        <SelectTrigger id={id} className="h-8 text-xs"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="__default__">— device default —</SelectItem>
          {options.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
        </SelectContent>
      </Select>
    </div>
  )
}

export default function CleanSettingsPanel({ refreshKey }: { refreshKey: number }) {
  const [fanSpeed, setFanSpeed] = useState('')
  const [mopMode, setMopMode] = useState('')
  const [waterFlow, setWaterFlow] = useState('')
  const [stale, setStale] = useState(false)
  const [feedback, setFeedback] = useState<{ msg: string; ok: boolean } | null>(null)

  useEffect(() => {
    apiGet<Settings>('/api/settings').then(s => {
      if (s.error) { setFeedback({ msg: `Could not load settings: ${s.error}`, ok: false }); return }
      setFanSpeed(s.fan_speed ?? '')
      setMopMode(s.mop_mode ?? '')
      setWaterFlow(s.water_flow ?? '')
      setStale(!!s._stale)
    }).catch(() => {})
  }, [refreshKey])

  async function saveSettings() {
    const body: Record<string, string> = {}
    if (fanSpeed) body.fan_speed = fanSpeed
    if (mopMode) body.mop_mode = mopMode
    if (waterFlow) body.water_flow = waterFlow
    const res = await apiPost<{ ok?: boolean; detail?: string }>('/api/settings', body)
    setFeedback({ msg: res.ok ? 'Settings saved!' : (res.detail ?? 'Error'), ok: !!res.ok })
    setTimeout(() => setFeedback(null), 4000)
  }

  return (
    <Panel title="Clean Settings" stale={stale}>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <SettingSelect id="set-fan-speed"  label="Fan Speed"  options={FAN_SPEEDS}  value={fanSpeed}  onChange={setFanSpeed} />
        <SettingSelect id="set-mop-mode"   label="Mop Mode"   options={MOP_MODES}   value={mopMode}   onChange={setMopMode} />
        <SettingSelect id="set-water-flow" label="Water Flow" options={WATER_FLOWS} value={waterFlow} onChange={setWaterFlow} />
      </div>
      <Button onClick={saveSettings}>Save Settings</Button>
      {feedback && (
        <p className={`text-xs mt-2 ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>{feedback.msg}</p>
      )}
    </Panel>
  )
}
