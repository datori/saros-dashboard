import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface Trigger { name: string; budget_min: number; mode: string; notes: string }

interface TriggerModalProps {
  open: boolean
  editing: Trigger | null
  onClose: () => void
  onSaved: () => void
}

export default function TriggerModal({ open, editing, onClose, onSaved }: TriggerModalProps) {
  const [name, setName] = useState('')
  const [budget, setBudget] = useState('')
  const [mode, setMode] = useState('vacuum')
  const [notes, setNotes] = useState('')

  useEffect(() => {
    if (editing) {
      setName(editing.name)
      setBudget(String(editing.budget_min))
      setMode(editing.mode)
      setNotes(editing.notes ?? '')
    } else {
      setName(''); setBudget(''); setMode('vacuum'); setNotes('')
    }
  }, [editing, open])

  async function save() {
    if (!name.trim()) { alert('Name is required'); return }
    const budgetNum = parseFloat(budget)
    if (!budgetNum || budgetNum <= 0) { alert('Budget must be positive'); return }
    const res = await fetch(`/api/triggers/${encodeURIComponent(name.trim())}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget_min: budgetNum, mode, notes: notes || null }),
    }).then(r => r.json())
    if (res.ok) { onSaved(); onClose() }
    else alert('Save failed: ' + (res.detail ?? 'Unknown error'))
  }

  return (
    <Dialog open={open} onOpenChange={o => !o && onClose()}>
      <DialogContent className="bg-card border-border">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit Trigger' : 'Add Trigger'}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-1">
            <Label>Name</Label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              readOnly={!!editing}
              placeholder="e.g. Gym, Shower, Leaving"
              className="w-full bg-background border border-border rounded px-3 py-1.5 text-sm text-foreground"
            />
          </div>
          <div className="space-y-1">
            <Label>Budget (minutes)</Label>
            <input
              type="number"
              value={budget}
              onChange={e => setBudget(e.target.value)}
              min={5}
              step={5}
              placeholder="e.g. 25"
              className="w-full bg-background border border-border rounded px-3 py-1.5 text-sm text-foreground"
            />
          </div>
          <div className="space-y-1">
            <Label>Mode</Label>
            <Select value={mode} onValueChange={v => setMode(v ?? 'vacuum')}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="vacuum">Vacuum</SelectItem>
                <SelectItem value="mop">Mop</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>Notes (optional)</Label>
            <input
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Quick clean while at gym"
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
