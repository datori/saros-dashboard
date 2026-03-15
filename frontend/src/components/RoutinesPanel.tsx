import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import Panel from './Panel'
import { apiGet } from '@/lib/api'

export default function RoutinesPanel({ refreshKey }: { refreshKey: number }) {
  const [routines, setRoutines] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [runningIdx, setRunningIdx] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<{ msg: string; ok: boolean } | null>(null)

  useEffect(() => {
    setLoading(true)
    apiGet<string[] | { error: string }>('/api/routines').then(r => {
      if (Array.isArray(r)) { setRoutines(r); setError(null) }
      else setError(r.error ?? 'Unavailable')
    }).catch(e => setError(String(e))).finally(() => setLoading(false))
  }, [refreshKey])

  async function runRoutine(name: string, idx: number) {
    setRunningIdx(idx)
    setFeedback(null)
    try {
      const res = await fetch(`/api/routine/${encodeURIComponent(name)}`, { method: 'POST' }).then(r => r.json())
      setFeedback({ msg: res.ok ? `'${name}' started!` : (res.detail ?? 'Error'), ok: !!res.ok })
    } catch (e) {
      setFeedback({ msg: String(e), ok: false })
    } finally {
      setRunningIdx(null)
      setTimeout(() => setFeedback(null), 4000)
    }
  }

  return (
    <Panel title="Routines">
      {loading ? (
        <p className="text-muted-foreground italic text-sm">Loading…</p>
      ) : error ? (
        <p className="text-destructive text-sm">Error: {error}</p>
      ) : routines.length === 0 ? (
        <p className="text-muted-foreground italic text-sm">No routines found.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {routines.map((name, idx) => (
            <div key={name} className="flex justify-between items-center">
              <span>{name}</span>
              <Button
                size="sm"
                onClick={() => runRoutine(name, idx)}
                disabled={runningIdx !== null}
                className="bg-violet-700 hover:bg-violet-600 text-white border-0"
              >
                {runningIdx === idx ? '…' : 'Run'}
              </Button>
            </div>
          ))}
        </div>
      )}
      {feedback && (
        <p className={`text-xs mt-2 ${feedback.ok ? 'text-green-400' : 'text-destructive'}`}>{feedback.msg}</p>
      )}
    </Panel>
  )
}
