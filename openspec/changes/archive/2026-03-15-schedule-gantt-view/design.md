## Context

`SchedulePanel` currently renders a plain HTML table. The data model (`GET /api/schedule`) already provides everything needed: `last_vacuumed`, `last_mopped`, `vacuum_days`, `mop_days`, `vacuum_overdue_ratio`, `mop_overdue_ratio`, `priority_weight`, `default_duration_sec`. No backend changes are required.

The panel lives in `frontend/src/components/SchedulePanel.tsx` and is mounted in the Info tab on mobile and the Info right-tab on desktop. The existing `EditModal` for editing intervals/notes is retained unchanged.

## Goals / Non-Goals

**Goals:**
- Replace the table with a Gantt timeline where urgency is spatially encoded
- Rooms auto-sort by urgency descending
- Inline "Clean Now" per room that calls `/api/rooms/clean` and animates the track on success
- Mobile-responsive: 10-day window on narrow viewports
- Zero new npm dependencies

**Non-Goals:**
- Changing the backend API
- Modifying CleanRoomsPanel or its advanced settings
- Full cleaning history per room (we only have `last_vacuumed`/`last_mopped` timestamps — no per-room history endpoint)
- Real-time animation between refreshes (30s polling is sufficient)

## Decisions

### Decision 1: Interval-relative x-axis (not calendar-absolute)

**Chosen**: Each track spans one full interval (0% → 100%). Overdue extends past 100% as a red overflow band.

**Alternative considered**: Fixed calendar window (e.g., Mar 8–Mar 28) where all tracks share the same date axis like a true Gantt. This is more intuitive for planning across rooms but creates a layout problem: rooms on different intervals have very different bar widths, making them hard to compare. A Kitchen on a 3-day VAC cycle and an Office on a 14-day MOP cycle become visually incomparable.

**Rationale**: The primary use case is "which rooms need cleaning now/soon?" — urgency comparison — not "what's on the calendar Tuesday?" For that use case, interval-relative (0%→100%) allows direct visual comparison of urgency across all rooms regardless of interval length. The overflow zone (>100%) creates a clear, alarming indicator for overdue rooms.

### Decision 2: Infer past clean events from interval

**Chosen**: Render inferred historical dots by back-extrapolating from `last_vacuumed`: `last - n*interval` for n=1,2,... while within the window.

**Rationale**: We only have one timestamp per room track. Without inferred events, there are no dots in the past portion of the window, which makes the tracks look empty and doesn't convey cleaning regularity. Inferred dots are rendered at lower opacity to distinguish them from confirmed events. This requires no backend changes.

**Risk**: Inferred dots are fictitious if the room's interval has changed recently, or if the room was skipped. They're presented as "approximate historical pattern" not "confirmed history." Use ~30% opacity to signal this.

### Decision 3: Pure CSS/SVG — no charting library

**Chosen**: Track area is `position: relative`. All elements (dots, bands, markers, NOW line) are `position: absolute; left: {xPct}%`.

**Alternative considered**: Recharts or D3. Neither adds meaningful value for this use case — the chart is a set of decorated horizontal bars, not a complex data visualization. Adding a library adds bundle weight, introduces version management, and reduces flexibility for custom styling.

**Rationale**: The x-position math is a single function: `(date - windowStart) / windowDurationMs * 100`. Everything else is CSS. This is maintainable and keeps the bundle lean.

### Decision 4: Gradient band from lastClean to dueDate

**Chosen**: A single `div` with `background: linear-gradient(to right, teal, amber)` spanning from the lastClean x-position to the dueDate x-position.

**Overflow (overdue)**: A second div from dueDate to the NOW position, background solid red, rendered only when overdue.

**Never-cleaned**: When `last_vacuumed` is null but `vacuum_days` is set, the gradient band has no left anchor. Render a full-width solid red band from the left edge of the window to NOW. Label the track "Never cleaned."

### Decision 5: "Clean Now" fires rooms/clean, animates locally

On button click:
1. POST `/api/rooms/clean` `{ segment_ids: [id], repeat: 1 }`
2. On success, update local state: set `last_vacuumed = new Date().toISOString()` for that room
3. Local state update causes the track to re-render with the dot at NOW, overdue band gone, gradient band reset
4. No wait for the next 30s refresh — immediate visual feedback

Use a `useState<RoomSchedule[]>` in the component so individual rooms can be mutated locally after clean actions.

### Decision 6: Urgency sort with stable secondary key

```
urgencyScore(room) =
  max(vac_ratio ?? Infinity, mop_ratio ?? Infinity) × priority_weight
```

Rooms with `ratio = null` (has interval, never cleaned): treat as `Infinity` — always float to top. Rooms with no interval: treated as score `0` — sink to bottom (no schedule = no urgency). Secondary sort key: room name (stable, alphabetical).

## Risks / Trade-offs

**Inferred dot accuracy** → Low opacity (0.3) clearly signals "approximate." Users who want precise history will use HistoryPanel.

**Interval-relative x-axis makes cross-room date comparison hard** → The date axis shows actual dates via tooltips on hover. The tradeoff (urgency comparison vs calendar planning) favors urgency for this panel's primary use case.

**"Clean Now" skips fan speed / mop mode selection** → It fires with no overrides (device defaults). Users who need specific settings use CleanRoomsPanel. The inline button is for the common case: "just clean it."

**Very long intervals (>21 days)** → Due date marker falls outside the window. Render a right-edge indicator: small arrow + "→ due in Nd" label at the right boundary of the track.

**Very short intervals (1–3 days)** → Multiple past dots and possibly multiple future due markers within the window. This is intentional — it shows frequency.

## Migration Plan

- `SchedulePanel.tsx` is a self-contained component. The rewrite is a drop-in replacement — same props (`{ refreshKey }`), same API call.
- The `EditModal` import and usage is preserved unchanged.
- No routing, no API changes, no database changes. Rollback = revert the file.
