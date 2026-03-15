import { useState, useEffect } from 'react'
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
    <div className="mb-4 rounded-xl px-4 py-2.5 text-sm" style={{ background: '#3d2b1f', border: '1px solid #7c3a1e', color: '#f97316' }}>
      {msg}
    </div>
  )
}
