import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import Panel from './Panel'
import { apiGet, fmtDuration } from '@/lib/api'

interface CleanRecord {
  start_time: string | null
  duration_seconds: number | null
  area_m2: number | null
  complete: boolean
  start_type: string | null
  clean_type: string | null
  finish_reason: string | null
}

export default function HistoryPanel({ refreshKey }: { refreshKey: number }) {
  const [records, setRecords] = useState<CleanRecord[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiGet<CleanRecord[] | { error: string }>('/api/history').then(r => {
      if (Array.isArray(r)) { setRecords(r); setError(null) }
      else setError(r.error ?? 'Unavailable')
    }).catch(e => setError(String(e)))
  }, [refreshKey])

  return (
    <Panel title="Clean History (last 10)">
      {error ? (
        <p className="text-destructive text-sm">Unavailable: {error}</p>
      ) : records.length === 0 ? (
        <p className="text-muted-foreground italic text-sm">No clean history found.</p>
      ) : (
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="text-muted-foreground">
                <th className="text-left pb-2 pr-2 font-medium">Start</th>
                <th className="text-left pb-2 pr-2 font-medium">Duration</th>
                <th className="text-left pb-2 pr-2 font-medium">Area</th>
                <th className="text-left pb-2 pr-2 font-medium">Done</th>
                <th className="text-left pb-2 pr-2 font-medium hidden md:table-cell">By</th>
                <th className="text-left pb-2 pr-2 font-medium hidden md:table-cell">Type</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={i} className="border-t border-border">
                  <td className="py-1.5 pr-2">
                    {r.start_time ? new Date(r.start_time).toLocaleString() : '—'}
                  </td>
                  <td className="py-1.5 pr-2">{fmtDuration(r.duration_seconds)}</td>
                  <td className="py-1.5 pr-2">{r.area_m2 != null ? `${r.area_m2} m²` : '—'}</td>
                  <td className="py-1.5 pr-2">
                    {r.complete
                      ? <Badge variant="secondary" className="bg-green-900/40 text-green-400 border-green-800 text-[10px] px-1.5 py-0">Yes</Badge>
                      : <Badge variant="secondary" className="bg-yellow-900/40 text-yellow-400 border-yellow-800 text-[10px] px-1.5 py-0">No</Badge>
                    }
                  </td>
                  <td className="py-1.5 pr-2 text-muted-foreground hidden md:table-cell">
                    {r.start_type?.replace(/_/g, ' ') ?? '—'}
                  </td>
                  <td className="py-1.5 pr-2 text-muted-foreground hidden md:table-cell">
                    {r.clean_type?.replace(/_/g, ' ') ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  )
}
