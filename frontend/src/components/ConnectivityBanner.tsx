import { useState, useEffect } from 'react'
import { WifiOff } from 'lucide-react'
import { apiGet } from '@/lib/api'

interface HealthData { ok: boolean; last_contact_seconds_ago: number | null }

export default function ConnectivityBanner({ refreshKey }: { refreshKey: number }) {
  const [msg, setMsg] = useState<string | null>(null)

  useEffect(() => {
    apiGet<HealthData>('/api/health').then(h => {
      if (!h.ok && h.last_contact_seconds_ago !== null) {
        const mins = Math.round(h.last_contact_seconds_ago / 60)
        setMsg(`⚠ Device unreachable — last contact ${mins}m ago`)
      } else {
        setMsg(null)
      }
    }).catch(() => {})
  }, [refreshKey])

  if (!msg) return null
  return (
    <div className="mb-4 flex items-center gap-3 rounded-[1.35rem] border border-amber-500/30 bg-amber-950/40 px-4 py-3 text-sm text-amber-200 shadow-[0_18px_45px_rgba(120,53,15,0.18)] backdrop-blur-xl">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-amber-400/20 bg-amber-400/10 text-amber-300">
        <WifiOff size={16} />
      </div>
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-300/75">Connectivity Warning</div>
        <div>{msg}</div>
      </div>
    </div>
  )
}
