import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import Panel from './Panel'
import { apiGet, fmt } from '@/lib/api'

interface StatusData {
  state: string | null
  battery: number | null
  in_dock: boolean
  error_code: number
  _stale?: boolean
  error?: string
}

function stateVariant(state: string | null): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (!state) return 'secondary'
  if (state.toLowerCase().includes('clean')) return 'default'
  if (state === 'charging' || state === 'charging_complete') return 'secondary'
  if (state === 'error') return 'destructive'
  return 'outline'
}

export default function StatusPanel({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<StatusData | null>(null)
  const [updated, setUpdated] = useState<string>('')

  useEffect(() => {
    apiGet<StatusData>('/api/status').then(d => {
      setData(d)
      setUpdated('Updated ' + new Date().toLocaleTimeString())
    }).catch(() => {})
  }, [refreshKey])

  const battery = data?.battery ?? 0
  const batteryColor = battery > 50 ? '' : battery > 20 ? 'warning' : 'danger'

  return (
    <Panel title="Status" stale={data?._stale}>
      {!data ? (
        <p className="text-muted-foreground italic text-sm">Loading…</p>
      ) : data.error ? (
        <p className="text-destructive text-sm">Error: {data.error}</p>
      ) : (
        <div className="space-y-0">
          <div className="flex justify-between items-center py-1.5 border-b border-border">
            <span className="text-muted-foreground">State</span>
            <Badge variant={stateVariant(data.state)}>{fmt(data.state)}</Badge>
          </div>
          <div className="flex justify-between items-center py-1.5 border-b border-border">
            <span className="text-muted-foreground">Dock</span>
            {data.in_dock
              ? <Badge variant="secondary" className="bg-green-900/40 text-green-400 border-green-800">In dock</Badge>
              : <Badge variant="secondary" className="bg-yellow-900/40 text-yellow-400 border-yellow-800">Away</Badge>
            }
          </div>
          {data.error_code ? (
            <div className="flex justify-between items-center py-1.5 border-b border-border">
              <span className="text-muted-foreground">Error</span>
              <Badge variant="destructive">{data.error_code}</Badge>
            </div>
          ) : null}
          <div className="pt-3">
            <div className="flex justify-between text-sm mb-1.5">
              <span>Battery</span>
              <span>{fmt(data.battery, '?')}%</span>
            </div>
            <Progress
              value={battery}
              className="h-3"
              style={batteryColor === 'danger' ? { '--progress-color': 'var(--destructive)' } as React.CSSProperties
                : batteryColor === 'warning' ? { '--progress-color': 'oklch(75% 0.18 85)' } as React.CSSProperties
                : undefined}
            />
          </div>
          {updated && <p className="text-[11px] text-muted-foreground mt-3">{updated}</p>}
        </div>
      )}
    </Panel>
  )
}
