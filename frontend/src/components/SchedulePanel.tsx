import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import Panel from './Panel'
import EditModal, { type EditModalRoom } from './EditModal'
import { apiGet, apiPost } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────────────────

interface RoomSchedule {
  segment_id: number
  name: string
  last_vacuumed: string | null
  last_mopped: string | null
  last_vacuum_combined: boolean
  vacuum_days: number | null
  mop_days: number | null
  vacuum_overdue_ratio: number | null
  mop_overdue_ratio: number | null
  priority_weight: number
  default_duration_sec: number | null
  notes: string | null
}

type RoomState = RoomSchedule & { busy: boolean; error: string | null }

interface GanttWindow {
  windowStart: Date
  windowEnd: Date
  windowDurationMs: number
  nowPct: number
  totalDays: number
}

// ─── Design tokens ────────────────────────────────────────────────────────────

// Blue → violet → rose: modern directional gradient (Linear/Vercel-style),
// avoids the "traffic light" association of green→amber→red.
// Gradient end matches OVERDUE_COLOR for seamless transition into overdue band
const INTERVAL_GRADIENT = 'linear-gradient(to right, #38bdf8 0%, #818cf8 50%, #fb7185 100%)'
const OVERDUE_COLOR     = '#fb7185'             // rose-400
const NOW_COLOR         = 'rgba(255,255,255,0.92)'
const NOW_GLOW          = '0 0 6px rgba(255,255,255,0.3)'
const DOT_COLOR         = '#ffffff'
const DOT_GLOW          = '0 0 5px rgba(255,255,255,0.5)'
const DOT_COMBINED      = '#38bdf8'              // sky-400 — vacuum credit from combined run
const DOT_COMBINED_GLOW = '0 0 5px rgba(56,189,248,0.7)'
const DOT_INFERRED      = 'rgba(255,255,255,0.18)'
const DIAMOND_FRESH     = '#38bdf8'             // sky-400 — matches gradient start
const DIAMOND_SOON      = '#818cf8'             // indigo-400 — matches gradient mid
const DIAMOND_GLOW_FRESH = '0 0 5px rgba(56,189,248,0.6)'
const DIAMOND_GLOW_SOON  = '0 0 5px rgba(129,140,248,0.6)'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const DAY_MS = 86_400_000

function xPct(date: Date, windowStart: Date, windowDurationMs: number): number {
  return ((date.getTime() - windowStart.getTime()) / windowDurationMs) * 100
}

function getWindowBounds(now: Date, isMobile: boolean): GanttWindow {
  const pastDays = isMobile ? 2 : 7
  const totalDays = isMobile ? 10 : 21
  const windowStart = new Date(now.getTime() - pastDays * DAY_MS)
  const windowEnd = new Date(windowStart.getTime() + totalDays * DAY_MS)
  const windowDurationMs = totalDays * DAY_MS
  const nowPct = xPct(now, windowStart, windowDurationMs)
  return { windowStart, windowEnd, windowDurationMs, nowPct, totalDays }
}

function getUrgencyScore(room: RoomSchedule): number {
  if (!room.vacuum_days && !room.mop_days) return 0
  const vRatio = room.vacuum_days != null ? (room.vacuum_overdue_ratio ?? Infinity) : -Infinity
  const mRatio = room.mop_days != null ? (room.mop_overdue_ratio ?? Infinity) : -Infinity
  return Math.max(vRatio, mRatio) * room.priority_weight
}

function useWindowWidth(): number {
  const [width, setWidth] = useState(window.innerWidth)
  useEffect(() => {
    const h = () => setWidth(window.innerWidth)
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [])
  return width
}

// Urgency accent color — used for left border on room rows
function getUrgencyColor(room: RoomSchedule): string {
  if (!room.vacuum_days && !room.mop_days) return 'rgba(255,255,255,0.06)'
  if ((room.vacuum_days && !room.last_vacuumed) || (room.mop_days && !room.last_mopped))
    return OVERDUE_COLOR
  const max = Math.max(room.vacuum_overdue_ratio ?? 0, room.mop_overdue_ratio ?? 0)
  if (max >= 1.0) return OVERDUE_COLOR
  if (max >= 0.7) return DIAMOND_SOON
  return DIAMOND_FRESH
}

// Compute tick positions for grid lines (mirrors GanttAxis logic)
function computeTickPcts(win: GanttWindow, isMobile: boolean): number[] {
  const { windowStart, windowDurationMs } = win
  const tickInterval = isMobile ? 2 : 3
  const firstDay = new Date(windowStart); firstDay.setHours(0, 0, 0, 0)
  const pcts: number[] = []
  let cur = new Date(firstDay)
  while (true) {
    const pct = xPct(cur, windowStart, windowDurationMs)
    if (pct > 100) break
    if (pct >= 0 && pct <= 100) pcts.push(pct)
    cur = new Date(cur.getTime() + tickInterval * DAY_MS)
  }
  return pcts
}

// CSS-styled urgency indicator (no emoji — consistent cross-platform rendering)
function UrgencyDot({ room }: { room: RoomSchedule }) {
  const base = 'inline-block w-2 h-2 rounded-full shrink-0'
  if (!room.vacuum_days && !room.mop_days)
    return <span className={`${base} bg-muted-foreground/25`} title="No schedule" />
  if ((room.vacuum_days && !room.last_vacuumed) || (room.mop_days && !room.last_mopped))
    return <span className={`${base} bg-rose-400`} title="Never cleaned" style={{ boxShadow: '0 0 4px rgba(251,113,133,0.7)' }} />
  const max = Math.max(room.vacuum_overdue_ratio ?? 0, room.mop_overdue_ratio ?? 0)
  if (max >= 1.0) return <span className={`${base} bg-rose-400`} title="Overdue" style={{ boxShadow: '0 0 4px rgba(251,113,133,0.7)' }} />
  if (max >= 0.7) return <span className={`${base} bg-indigo-400`} title="Due soon" style={{ boxShadow: '0 0 4px rgba(129,140,248,0.6)' }} />
  return <span className={`${base} bg-sky-400`} title="On schedule" />
}

// Colored badge for VAC / MOP track type — also shows the interval if set
function TrackLabel({ type, days }: { type: 'VAC' | 'MOP'; days: number | null }) {
  return (
    <span className={`flex flex-col items-center px-1 py-0.5 rounded border w-8 shrink-0 ${
      type === 'VAC'
        ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30'
        : 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
    }`}>
      <span className="text-[8px] font-semibold leading-tight">{type}</span>
      {days != null && <span className="text-[7px] leading-tight opacity-55">{days}d</span>}
    </span>
  )
}

// ─── Legend ───────────────────────────────────────────────────────────────────

function GanttLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-3 text-[9px] text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <span className="inline-block w-7 h-2 rounded-sm" style={{ background: INTERVAL_GRADIENT, opacity: 0.8 }} />
        interval
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block w-4 h-2 rounded-sm" style={{ backgroundColor: OVERDUE_COLOR, opacity: 0.8 }} />
        overdue
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: DOT_COLOR, boxShadow: DOT_GLOW }} />
        last cleaned
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: DOT_COMBINED, boxShadow: DOT_COMBINED_GLOW }} />
        combined run
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block w-2 h-2 rotate-45 rounded-sm" style={{ backgroundColor: DIAMOND_FRESH, boxShadow: DIAMOND_GLOW_FRESH }} />
        due date
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block w-[2px] h-3 rounded-full" style={{ backgroundColor: NOW_COLOR, boxShadow: NOW_GLOW }} />
        now
      </span>
    </div>
  )
}

// ─── Track Component ──────────────────────────────────────────────────────────

function Track({
  last, intervalDays, ratio, win, isMobile, combined,
}: {
  last: string | null
  intervalDays: number | null
  ratio: number | null
  win: GanttWindow
  isMobile: boolean
  combined?: boolean
}) {
  const { windowStart, windowEnd, windowDurationMs, nowPct } = win
  const trackH = isMobile ? 14 : 18  // px
  const dotR   = isMobile ? 4  : 5   // radius px
  const diamR  = isMobile ? 4  : 5

  // Ghost track — no schedule set for this mode
  if (!intervalDays) {
    return (
      <div style={{ height: trackH, position: 'relative', display: 'flex', alignItems: 'center' }}>
        <div style={{
          position: 'absolute', left: 0, right: 0,
          borderTop: '1px dashed rgba(68,76,86,0.6)',
        }} />
      </div>
    )
  }

  const lastDate = last ? new Date(last) : null
  const dueDate  = lastDate ? new Date(lastDate.getTime() + intervalDays * DAY_MS) : null
  const duePct   = dueDate  ? xPct(dueDate,  windowStart, windowDurationMs) : null
  const lastPct  = lastDate ? xPct(lastDate, windowStart, windowDurationMs) : null
  const now      = new Date(windowStart.getTime() + (nowPct / 100) * windowDurationMs)
  const isOverdue = ratio !== null && ratio >= 1.0

  // Back-extrapolate inferred cleans from lastDate
  const inferredDots: { pct: number; date: Date }[] = []
  if (lastDate) {
    for (let n = 1; n <= 60; n++) {
      const d = new Date(lastDate.getTime() - n * intervalDays * DAY_MS)
      const p = xPct(d, windowStart, windowDurationMs)
      if (p < 0) break
      if (p <= 100) inferredDots.push({ date: d, pct: p })
    }
  }

  // Gradient band
  const gradLeft  = Math.max(0, lastPct ?? 0)
  const gradRight = Math.min(100, duePct ?? 100)
  const gradWidth = gradRight - gradLeft

  // Overdue band
  const overdueLeft  = Math.max(0, duePct ?? 0)
  const overdueWidth = nowPct - overdueLeft

  // Beyond-window indicator
  const daysBeyond = dueDate && dueDate > windowEnd
    ? Math.ceil((dueDate.getTime() - windowEnd.getTime()) / DAY_MS) : 0

  const overdueTooltip = dueDate
    ? `Overdue since ${dueDate.toLocaleDateString()} (${Math.floor((now.getTime() - dueDate.getTime()) / DAY_MS)} days)`
    : 'Overdue'

  // Forward-extrapolate future cycle due dates
  const futureDiamonds: { pct: number; date: Date; nth: number }[] = []
  if (dueDate && intervalDays) {
    for (let n = 1; n <= 10; n++) {
      const d = new Date(dueDate.getTime() + n * intervalDays * DAY_MS)
      const p = xPct(d, windowStart, windowDurationMs)
      if (p > 100) break
      if (p >= 0) futureDiamonds.push({ date: d, pct: p, nth: n })
    }
  }

  const diamondColor = (ratio == null || ratio < 0.7) ? DIAMOND_FRESH : DIAMOND_SOON
  const diamondGlow  = (ratio == null || ratio < 0.7) ? DIAMOND_GLOW_FRESH : DIAMOND_GLOW_SOON

  return (
    <div style={{
      position: 'relative',
      height: trackH,
      marginTop: 3,
      marginBottom: 3,
      borderRadius: 4,
      backgroundColor: 'rgba(255,255,255,0.035)',
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)',
      overflow: 'visible',
    }}>
      {/* Never-cleaned band */}
      {!lastDate && (
        <div title="Never cleaned" className="animate-pulse" style={{
          position: 'absolute', top: 0, bottom: 0, left: 0,
          width: `${nowPct}%`,
          backgroundColor: OVERDUE_COLOR,
          borderRadius: 4,
        }} />
      )}

      {/* Gradient interval band */}
      {lastDate && dueDate && gradWidth > 0 && (
        <div style={{
          position: 'absolute', top: 0, bottom: 0,
          left: `${gradLeft}%`, width: `${gradWidth}%`,
          background: INTERVAL_GRADIENT,
          opacity: 0.78,
          borderRadius: 4,
        }} />
      )}

      {/* Overdue band — fades in from interval end for smooth transition */}
      {isOverdue && overdueWidth > 0 && (
        <div title={overdueTooltip} className="animate-pulse" style={{
          position: 'absolute', top: 0, bottom: 0,
          left: `${overdueLeft}%`, width: `${overdueWidth}%`,
          background: `linear-gradient(to right, transparent, ${OVERDUE_COLOR} 25%)`,
          borderRadius: 4,
        }} />
      )}

      {/* NOW vertical line */}
      <div style={{
        position: 'absolute', top: -2, bottom: -2,
        left: `${nowPct}%`,
        width: 2,
        transform: 'translateX(-50%)',
        backgroundColor: NOW_COLOR,
        boxShadow: NOW_GLOW,
        borderRadius: 2,
        zIndex: 20,
      }} />

      {/* Inferred historical dots (translucent rings) */}
      {inferredDots.map(({ date, pct }) => (
        <div
          key={`inf-${pct}`}
          title={`Est. cleaned ${date.toLocaleDateString()}`}
          style={{
            position: 'absolute',
            width: dotR * 2, height: dotR * 2,
            left: `${pct}%`, top: '50%',
            transform: `translateX(-${dotR}px) translateY(-${dotR}px)`,
            backgroundColor: DOT_INFERRED,
            border: '1px solid rgba(255,255,255,0.25)',
            borderRadius: '50%',
            zIndex: 10,
          }}
        />
      ))}

      {/* Confirmed clean dot — white normally; sky-blue when credit came from a combined run */}
      {lastDate && lastPct !== null && lastPct >= -1 && lastPct <= 101 && (
        <div
          title={combined
            ? `Cleaned ${lastDate.toLocaleString()} (combined vac + mop run)`
            : `Cleaned ${lastDate.toLocaleString()}`}
          style={{
            position: 'absolute',
            width: dotR * 2 + 2, height: dotR * 2 + 2,
            left: `${Math.max(0, Math.min(100, lastPct))}%`,
            top: '50%',
            transform: `translateX(-${dotR + 1}px) translateY(-${dotR + 1}px)`,
            backgroundColor: combined ? DOT_COMBINED : DOT_COLOR,
            boxShadow: combined ? DOT_COMBINED_GLOW : DOT_GLOW,
            outline: '2px solid rgba(255,255,255,0.18)',
            outlineOffset: 3,
            borderRadius: '50%',
            zIndex: 15,
          }}
        />
      )}

      {/* Due date diamond */}
      {dueDate && duePct !== null && duePct >= 0 && duePct <= 100 && !isOverdue && (
        <div
          title={`Due ${dueDate.toLocaleDateString()}`}
          style={{
            position: 'absolute',
            width: diamR * 2, height: diamR * 2,
            left: `${duePct}%`, top: '50%',
            transform: `translateX(-${diamR}px) translateY(-${diamR}px) rotate(45deg)`,
            backgroundColor: diamondColor,
            boxShadow: diamondGlow,
            borderRadius: 2,
            zIndex: 15,
          }}
        />
      )}

      {/* Future cycle markers — hollow muted diamonds at subsequent intervals */}
      {futureDiamonds.map(({ date, pct, nth }) => (
        <div
          key={`future-${nth}`}
          title={`Cycle ${nth + 1} due ${date.toLocaleDateString()}`}
          style={{
            position: 'absolute',
            width: diamR * 1.5, height: diamR * 1.5,
            left: `${pct}%`, top: '50%',
            transform: `translateX(-${diamR * 0.75}px) translateY(-${diamR * 0.75}px) rotate(45deg)`,
            border: '1.5px solid rgba(255,255,255,0.13)',
            borderRadius: 1,
            zIndex: 5,
          }}
        />
      ))}

      {/* Beyond-window label */}
      {daysBeyond > 0 && (
        <span style={{
          position: 'absolute', right: 0, top: '50%',
          transform: 'translateY(-50%)',
          fontSize: 8,
          color: '#768390',
          backgroundColor: 'rgba(45,51,59,0.9)',
          paddingRight: 2,
          borderRadius: 2,
          zIndex: 30,
        }}>
          →{daysBeyond}d
        </span>
      )}
    </div>
  )
}

// ─── Date Axis ────────────────────────────────────────────────────────────────

function GanttAxis({ win, isMobile }: { win: GanttWindow; isMobile: boolean }) {
  const { windowStart, windowDurationMs } = win
  const tickInterval = isMobile ? 2 : 3
  const today = new Date(); today.setHours(0, 0, 0, 0)

  const firstDay = new Date(windowStart); firstDay.setHours(0, 0, 0, 0)
  const ticks: { label: string; pct: number; isToday: boolean }[] = []
  let cur = new Date(firstDay)
  while (xPct(cur, windowStart, windowDurationMs) <= 102) {
    const pct = xPct(cur, windowStart, windowDurationMs)
    if (pct >= -2 && pct <= 102) {
      const isToday = cur.toDateString() === today.toDateString()
      ticks.push({
        label: isToday ? 'TODAY' : cur.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
        pct: Math.max(0, Math.min(100, pct)),
        isToday,
      })
    }
    cur = new Date(cur.getTime() + tickInterval * DAY_MS)
  }

  // Always ensure TODAY appears — on desktop the 3-day interval often misses it
  const todayPct = xPct(today, windowStart, windowDurationMs)
  const hasTodayTick = ticks.some(t => t.isToday || Math.abs(t.pct - Math.max(0, Math.min(100, todayPct))) < 1.5)
  if (!hasTodayTick && todayPct >= 0 && todayPct <= 100) {
    ticks.push({ label: 'TODAY', pct: todayPct, isToday: true })
    ticks.sort((a, b) => a.pct - b.pct)
  }

  return (
    <div className="relative h-6 overflow-visible">
      {ticks.map((t, i) => (
        <span
          key={i}
          className="absolute text-[9px] -translate-x-1/2 top-0 whitespace-nowrap select-none"
          style={{
            left: `${t.pct}%`,
            color: t.isToday ? NOW_COLOR : '#768390',
            fontWeight: t.isToday ? 600 : 400,
            textShadow: t.isToday ? NOW_GLOW : undefined,
          }}
        >
          {t.label}
          {/* Tick mark connecting label to tracks */}
          <span style={{
            position: 'absolute',
            bottom: -4,
            left: '50%',
            width: 1,
            height: 5,
            backgroundColor: t.isToday ? 'rgba(255,255,255,0.4)' : 'rgba(118,131,144,0.25)',
            transform: 'translateX(-50%)',
          }} />
        </span>
      ))}
    </div>
  )
}

// ─── Room Track Group ─────────────────────────────────────────────────────────

function RoomTrackGroup({
  room, win, isMobile, onEdit, onCleanNow,
}: {
  room: RoomState
  win: GanttWindow
  isMobile: boolean
  onEdit: (r: RoomState) => void
  onCleanNow: (segmentId: number) => void
}) {
  return (
    <div
      className="border-t border-border/40 pt-1.5 pb-1 rounded-r-lg hover:bg-white/[0.025] transition-colors -mx-2 px-2"
      style={{ borderLeft: `3px solid ${getUrgencyColor(room)}` }}
    >
      {/* Header row */}
      <div className="flex items-center gap-1.5 mb-1">
        <UrgencyDot room={room} />
        <span className={`font-medium ${isMobile ? 'text-[11px]' : 'text-xs'} flex-1 min-w-0 truncate`}>
          {room.name}
        </span>
        {!isMobile && (
          <Button variant="outline" size="sm" className="h-5 px-1.5 text-[10px] shrink-0" onClick={() => onEdit(room)}>
            Edit
          </Button>
        )}
        <Button
          variant="outline" size="sm"
          className="h-5 px-1.5 text-[10px] shrink-0"
          disabled={room.busy}
          onClick={() => onCleanNow(room.segment_id)}
        >
          {room.busy ? '…' : isMobile ? '▶' : 'Clean Now'}
        </Button>
      </div>

      {room.error && (
        <p className="text-[10px] mb-0.5 ml-4" style={{ color: OVERDUE_COLOR }}>{room.error}</p>
      )}

      {/* VAC + MOP tracks */}
      <div className="space-y-0.5">
        {(['VAC', 'MOP'] as const).map(type => (
          <div key={type} className="flex items-center gap-1.5">
            <TrackLabel type={type} days={type === 'VAC' ? room.vacuum_days : room.mop_days} />
            <div className="flex-1 min-w-0">
              <Track
                last={type === 'VAC' ? room.last_vacuumed : room.last_mopped}
                intervalDays={type === 'VAC' ? room.vacuum_days : room.mop_days}
                ratio={type === 'VAC' ? room.vacuum_overdue_ratio : room.mop_overdue_ratio}
                win={win}
                isMobile={isMobile}
                combined={type === 'VAC' ? room.last_vacuum_combined : false}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function SchedulePanel({ refreshKey }: { refreshKey: number }) {
  const [rows, setRows] = useState<RoomState[]>([])
  const [editRoom, setEditRoom] = useState<EditModalRoom | null>(null)
  const viewportWidth = useWindowWidth()
  const isMobile = viewportWidth < 768

  async function load() {
    const data = await apiGet<RoomSchedule[]>('/api/schedule').catch(() => [])
    setRows(Array.isArray(data) ? data.map(r => ({ ...r, busy: false, error: null })) : [])
  }

  useEffect(() => { load() }, [refreshKey])

  const now = new Date()
  const win = getWindowBounds(now, isMobile)

  const sortedRows = [...rows].sort((a, b) => {
    const sa = getUrgencyScore(a)
    const sb = getUrgencyScore(b)
    if (sa === Infinity && sb === Infinity) return a.name.localeCompare(b.name)
    if (sa === Infinity) return -1
    if (sb === Infinity) return 1
    if (sa === sb) return a.name.localeCompare(b.name)
    return sb - sa
  })

  async function handleCleanNow(segmentId: number) {
    setRows(prev => prev.map(r =>
      r.segment_id === segmentId ? { ...r, busy: true, error: null } : r
    ))
    try {
      const result = await apiPost<{ ok?: boolean; error?: string; detail?: string }>(
        '/api/rooms/clean',
        { segment_ids: [segmentId], repeat: 1 }
      )
      if (result.error || result.detail) throw new Error(result.error ?? result.detail ?? 'Failed')
      const nowIso = new Date().toISOString()
      setRows(prev => prev.map(r =>
        r.segment_id === segmentId
          ? { ...r, busy: false, last_vacuumed: nowIso, vacuum_overdue_ratio: 0 }
          : r
      ))
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to start clean'
      setRows(prev => prev.map(r =>
        r.segment_id === segmentId ? { ...r, busy: false, error: msg } : r
      ))
      setTimeout(() => {
        setRows(prev => prev.map(r =>
          r.segment_id === segmentId ? { ...r, error: null } : r
        ))
      }, 4000)
    }
  }

  return (
    <Panel title="Cleaning Schedule">
      {rows.length === 0 ? (
        <p className="text-muted-foreground italic text-sm">No rooms in schedule yet.</p>
      ) : (
        <div>
          <GanttLegend />

          {/* Gantt area — relative container for grid lines + NOW line overlay */}
          <div style={{ position: 'relative' }}>
            {/* Grid lines + NOW line overlay — spans full height */}
            <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, pointerEvents: 'none', zIndex: 10 }}>
              <div style={{ display: 'flex', gap: 6, height: '100%' }}>
                {/* Spacer matching TrackLabel w-8 (32px) */}
                <span style={{ width: 32, flexShrink: 0 }} />
                <div style={{ flex: 1, position: 'relative' }}>
                  {/* Vertical grid lines at tick positions */}
                  {computeTickPcts(win, isMobile).map(pct => (
                    <div key={pct} style={{
                      position: 'absolute', top: 0, bottom: 0,
                      left: `${pct}%`, width: 1,
                      backgroundColor: 'rgba(255,255,255,0.04)',
                    }} />
                  ))}
                </div>
              </div>
            </div>

            {/* Date axis — w-8 spacer matches TrackLabel width */}
            <div className="flex items-end gap-1.5 mb-1">
              <span className="w-8 shrink-0" />
              <div className="flex-1 min-w-0 overflow-visible">
                <GanttAxis win={win} isMobile={isMobile} />
              </div>
            </div>

            {sortedRows.map(room => (
              <RoomTrackGroup
                key={room.segment_id}
                room={room}
                win={win}
                isMobile={isMobile}
                onEdit={r => setEditRoom({
                  segment_id: r.segment_id,
                  name: r.name,
                  vacuum_days: r.vacuum_days,
                  mop_days: r.mop_days,
                  notes: r.notes,
                  priority_weight: r.priority_weight ?? 1.0,
                  default_duration_sec: r.default_duration_sec,
                })}
                onCleanNow={handleCleanNow}
              />
            ))}
          </div>
        </div>
      )}
      <EditModal
        open={editRoom != null}
        room={editRoom}
        onClose={() => setEditRoom(null)}
        onSaved={load}
      />
    </Panel>
  )
}
