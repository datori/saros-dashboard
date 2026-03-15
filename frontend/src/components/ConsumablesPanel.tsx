import { useState, useEffect } from 'react'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import Panel from './Panel'
import { apiGet } from '@/lib/api'

interface ConsumablesData {
  main_brush_pct: number | null
  side_brush_pct: number | null
  filter_pct: number | null
  sensor_pct: number | null
  _stale?: boolean
  error?: string
}

const ITEMS: { label: string; key: keyof ConsumablesData; attr: string }[] = [
  { label: 'Main brush', key: 'main_brush_pct', attr: 'main_brush_work_time' },
  { label: 'Side brush', key: 'side_brush_pct', attr: 'side_brush_work_time' },
  { label: 'Filter',     key: 'filter_pct',     attr: 'filter_work_time' },
  { label: 'Sensors',   key: 'sensor_pct',      attr: 'sensor_dirty_time' },
]

function progressColor(pct: number | null): React.CSSProperties {
  if (pct == null || pct > 50) return {}
  if (pct > 20) return { '--progress-color': 'oklch(75% 0.18 85)' } as React.CSSProperties
  return { '--progress-color': 'var(--destructive)' } as React.CSSProperties
}

export default function ConsumablesPanel({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<ConsumablesData | null>(null)

  useEffect(() => {
    apiGet<ConsumablesData>('/api/consumables').then(setData).catch(() => {})
  }, [refreshKey])

  async function resetConsumable(attr: string, label: string) {
    if (!confirm(`Reset ${label} timer? This cannot be undone.`)) return
    const res = await fetch(`/api/consumables/reset/${attr}`, { method: 'POST' }).then(r => r.json())
    if (res.ok) {
      const fresh = await apiGet<ConsumablesData>('/api/consumables')
      setData(fresh)
    } else {
      alert(`Reset failed: ${res.detail ?? 'Unknown error'}`)
    }
  }

  return (
    <Panel title="Consumables" stale={data?._stale}>
      {!data ? (
        <p className="text-muted-foreground italic text-sm">Loading…</p>
      ) : data.error ? (
        <p className="text-destructive text-sm">Unavailable: {data.error}</p>
      ) : (
        <div className="space-y-3">
          {ITEMS.map(item => {
            const pct = data[item.key] as number | null
            return (
              <div key={item.key}>
                <div className="flex justify-between items-center mb-1 text-sm">
                  <span>{item.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">{pct != null ? `${pct}%` : '—'}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-6 px-2 text-[11px]"
                      onClick={() => resetConsumable(item.attr, item.label)}
                    >
                      Reset
                    </Button>
                  </div>
                </div>
                <Progress value={pct ?? 0} className="h-2" style={progressColor(pct)} />
              </div>
            )
          })}
        </div>
      )}
    </Panel>
  )
}
