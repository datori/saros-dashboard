import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { apiPatch } from '@/lib/api'

export interface EditModalRoom {
  segment_id: number
  name: string
  vacuum_days: number | null
  mop_days: number | null
  notes: string | null
  priority_weight: number
  default_duration_sec: number | null
}

interface EditModalProps {
  open: boolean
  room: EditModalRoom | null
  onClose: () => void
  onSaved: () => void
}

export default function EditModal({ open, room, onClose, onSaved }: EditModalProps) {
  const [vacuumDays, setVacuumDays] = useState('')
  const [mopDays, setMopDays] = useState('')
  const [priorityWeight, setPriorityWeight] = useState('')
  const [durationMin, setDurationMin] = useState('')
  const [notes, setNotes] = useState('')

  useEffect(() => {
    if (room) {
      setVacuumDays(room.vacuum_days != null ? String(room.vacuum_days) : '')
      setMopDays(room.mop_days != null ? String(room.mop_days) : '')
      setPriorityWeight(room.priority_weight != null ? String(room.priority_weight) : '')
      setDurationMin(room.default_duration_sec != null ? String(Math.round(room.default_duration_sec / 60)) : '')
      setNotes(room.notes ?? '')
    }
  }, [room, open])

  async function save() {
    if (!room) return
    const body: Record<string, number | string | null> = {
      vacuum_days: vacuumDays !== '' ? parseFloat(vacuumDays) : null,
      mop_days: mopDays !== '' ? parseFloat(mopDays) : null,
      notes: notes || null,
      default_duration_min: durationMin !== '' ? parseFloat(durationMin) : null,
    }
    if (priorityWeight !== '') body.priority_weight = parseFloat(priorityWeight)
    const res = await apiPatch<{ ok?: boolean; detail?: string }>(`/api/schedule/rooms/${room.segment_id}`, body)
    if (res.ok) { onSaved(); onClose() }
    else alert('Save failed: ' + (res.detail ?? 'Unknown error'))
  }

  return (
    <Dialog open={open} onOpenChange={o => !o && onClose()}>
      <DialogContent className="bg-card border-border">
        <DialogHeader>
          <DialogTitle>{room?.name ?? 'Edit Intervals'}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 pt-2">
          {([
            { label: 'Vacuum every (days) — clear to unschedule', value: vacuumDays, set: setVacuumDays, step: '0.5', min: '0.5' },
            { label: 'Mop every (days) — clear to unschedule',    value: mopDays,    set: setMopDays,    step: '0.5', min: '0.5' },
            { label: 'Priority weight (default 1.0)',              value: priorityWeight, set: setPriorityWeight, step: '0.1', min: '0.1' },
            { label: 'Est. duration (min) — clear for auto',       value: durationMin, set: setDurationMin, step: '1',   min: '1' },
          ]).map(f => (
            <div key={f.label} className="space-y-1">
              <Label className="text-xs text-muted-foreground">{f.label}</Label>
              <input
                type="number"
                value={f.value}
                onChange={e => f.set(e.target.value)}
                min={f.min}
                step={f.step}
                className="w-full bg-background border border-border rounded px-3 py-1.5 text-sm text-foreground"
              />
            </div>
          ))}
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Notes (optional)</Label>
            <input
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Pets sleep here"
              className="w-full bg-background border border-border rounded px-3 py-1.5 text-sm text-foreground"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={save}>Save</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
