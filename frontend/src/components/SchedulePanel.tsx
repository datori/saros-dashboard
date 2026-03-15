import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import Panel from './Panel'
import EditModal, { type EditModalRoom } from './EditModal'
import { apiGet, fmtDate } from '@/lib/api'

interface RoomSchedule {
  segment_id: number
  name: string
  last_vacuumed: string | null
  last_mopped: string | null
  vacuum_days: number | null
  mop_days: number | null
  vacuum_overdue_ratio: number | null
  mop_overdue_ratio: number | null
  priority_weight: number
  default_duration_sec: number | null
  notes: string | null
}

function dueDateStr(lastIso: string | null, intervalDays: number | null): string | null {
  if (!intervalDays) return null
  if (!lastIso) return 'Never'
  const due = new Date(new Date(lastIso).getTime() + intervalDays * 86400000)
  return due.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function overdueClass(ratio: number | null, intervalDays: number | null, lastIso: string | null): string {
  if (!intervalDays) return 'text-muted-foreground'
  if (!lastIso) return 'text-destructive font-semibold'
  if (ratio == null) return ''
  if (ratio >= 1.0) return 'text-destructive font-semibold'
  if (ratio >= 0.8) return 'text-yellow-400 font-semibold'
  return ''
}

export default function SchedulePanel({ refreshKey }: { refreshKey: number }) {
  const [rows, setRows] = useState<RoomSchedule[]>([])
  const [editRoom, setEditRoom] = useState<EditModalRoom | null>(null)

  async function load() {
    const data = await apiGet<RoomSchedule[]>('/api/schedule').catch(() => [])
    setRows(Array.isArray(data) ? data : [])
  }

  useEffect(() => { load() }, [refreshKey])

  return (
    <Panel title="Cleaning Schedule">
      {rows.length === 0 ? (
        <p className="text-muted-foreground italic text-sm">No rooms in schedule yet.</p>
      ) : (
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="text-muted-foreground">
                <th className="text-left pb-2 pr-2 font-medium">Room</th>
                <th className="text-left pb-2 pr-2 font-medium">Vac Due</th>
                <th className="text-left pb-2 pr-2 font-medium">Mop Due</th>
                <th className="text-left pb-2 pr-2 font-medium hidden md:table-cell">Every</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody>
              {rows.map(r => {
                const vDue = dueDateStr(r.last_vacuumed, r.vacuum_days)
                const mDue = dueDateStr(r.last_mopped, r.mop_days)
                const vClass = overdueClass(r.vacuum_overdue_ratio, r.vacuum_days, r.last_vacuumed)
                const mClass = overdueClass(r.mop_overdue_ratio, r.mop_days, r.last_mopped)
                const vOverdue = r.vacuum_overdue_ratio != null && r.vacuum_overdue_ratio >= 1.0 || (r.vacuum_days && !r.last_vacuumed)
                const mOverdue = r.mop_overdue_ratio != null && r.mop_overdue_ratio >= 1.0 || (r.mop_days && !r.last_mopped)
                return (
                  <tr key={r.segment_id} className="border-t border-border">
                    <td className="py-1.5 pr-2 font-medium">{r.name}</td>
                    <td className={`py-1.5 pr-2 ${vClass}`}>
                      {vDue ? `${vDue}${vOverdue ? ' ⚠' : ''}` : <span className="text-muted-foreground">—</span>}
                    </td>
                    <td className={`py-1.5 pr-2 ${mClass}`}>
                      {mDue ? `${mDue}${mOverdue ? ' ⚠' : ''}` : <span className="text-muted-foreground">—</span>}
                    </td>
                    <td className="py-1.5 pr-2 text-muted-foreground hidden md:table-cell">
                      {r.vacuum_days ? `${r.vacuum_days}d` : '—'} / {r.mop_days ? `${r.mop_days}d` : '—'}
                    </td>
                    <td className="py-1.5">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-6 px-2 text-[11px]"
                        onClick={() => setEditRoom({
                          segment_id: r.segment_id,
                          name: r.name,
                          vacuum_days: r.vacuum_days,
                          mop_days: r.mop_days,
                          notes: r.notes,
                          priority_weight: r.priority_weight ?? 1.0,
                          default_duration_sec: r.default_duration_sec,
                        })}
                      >
                        Edit
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {/* Suppress unused import warning */}
      {false && fmtDate('')}
      <EditModal
        open={editRoom != null}
        room={editRoom}
        onClose={() => setEditRoom(null)}
        onSaved={load}
      />
    </Panel>
  )
}
