import { useState } from 'react'
import { Button } from '@/components/ui/button'
import Panel from './Panel'
import { apiPost } from '@/lib/api'

const ACTIONS = [
  { name: 'start',  label: '▶ Start',   variant: 'default'     as const },
  { name: 'stop',   label: '■ Stop',    variant: 'destructive' as const },
  { name: 'pause',  label: '⏸ Pause',  variant: 'secondary'   as const },
  { name: 'dock',   label: '⏏ Dock',   variant: 'outline'     as const },
  { name: 'locate', label: '🔔 Locate', variant: 'outline'     as const },
]

interface ActionsResponse { ok?: boolean; detail?: string }

export default function ActionsPanel({ onStatusChange }: { onStatusChange: () => void }) {
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<{ msg: string; ok: boolean } | null>(null)

  async function doAction(name: string) {
    setBusy(true)
    setFeedback(null)
    try {
      const res = await apiPost<ActionsResponse>(`/api/action/${name}`, {})
      setFeedback({ msg: res.ok ? `${name} sent!` : (res.detail ?? 'Error'), ok: !!res.ok })
      if (res.ok && name !== 'locate') setTimeout(onStatusChange, 2000)
    } catch (e) {
      setFeedback({ msg: String(e), ok: false })
    } finally {
      setBusy(false)
      setTimeout(() => setFeedback(null), 4000)
    }
  }

  return (
    <Panel title="Actions">
      <div className="flex flex-wrap gap-2">
        {ACTIONS.map(a => (
          <Button
            key={a.name}
            variant={a.variant}
            size="sm"
            disabled={busy}
            onClick={() => doAction(a.name)}
            className={a.name === 'pause' ? 'bg-yellow-600 hover:bg-yellow-500 text-black border-0' : undefined}
          >
            {a.label}
          </Button>
        ))}
      </div>
      {feedback && (
        <p className={`text-xs mt-2 ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>
          {feedback.msg}
        </p>
      )}
    </Panel>
  )
}
