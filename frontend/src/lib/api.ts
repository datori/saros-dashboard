export async function apiGet<T>(url: string): Promise<T> {
  const r = await fetch(url)
  return r.json()
}

export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, {
    method: 'POST',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  return r.json()
}

export async function apiPatch<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return r.json()
}

export async function apiDelete(url: string): Promise<void> {
  await fetch(url, { method: 'DELETE' })
}

export function fmt(val: unknown, fallback = '—'): string {
  return val != null ? String(val) : fallback
}

export function fmtDate(iso: string | null | undefined): string | null {
  if (!iso) return null
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '—'
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
}
