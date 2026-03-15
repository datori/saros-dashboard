## 1. Core Layout & Positioning Infrastructure

- [x] 1.1 Define the `xPct(date, windowStart, windowDurationMs)` helper function that maps a Date to a 0–100 percentage position on the track
- [x] 1.2 Define `getWindowBounds(now, isMobile)` returning `{ windowStart, windowEnd, windowDurationMs, nowPct }` — 21d desktop / 10d mobile
- [x] 1.3 Implement `getUrgencyScore(room)` — `max(vac_ratio ?? Infinity, mop_ratio ?? Infinity) × priority_weight` with null-schedule rooms scoring 0
- [x] 1.4 Add responsive window detection (`window.innerWidth < 768`) with a `useWindowWidth` hook or media query, triggering re-render on resize

## 2. Date Axis

- [x] 2.1 Render the date axis row above the tracks: tick labels every 3 days (desktop) or 2 days (mobile), using `xPct` for positioning
- [x] 2.2 Highlight the "TODAY" tick with primary color; all other ticks use muted foreground
- [x] 2.3 Add the NOW vertical line: absolute-positioned 2px white/primary line at `nowPct%`, labeled "TODAY" at top, spanning all track rows

## 3. Track Band Elements

- [x] 3.1 Implement `GradientBand` — absolute div from `xPct(lastClean)` to `xPct(dueDate)`, `linear-gradient(to right, teal, amber, orange-red)`, clamped to window bounds
- [x] 3.2 Implement `OverdueBand` — solid red absolute div from `xPct(dueDate)` to `nowPct`, rendered only when `ratio >= 1.0`
- [x] 3.3 Implement `NeverCleanedBand` — full-width solid red from left edge to `nowPct`, rendered when `last_vacuumed` is null and `vacuum_days` is set
- [x] 3.4 Implement beyond-window indicator: when `xPct(dueDate) > 100`, render a `→ Nd` label at the right edge of the track
- [x] 3.5 Implement ghost track line for no-schedule mode: muted dotted horizontal rule with "No schedule" tooltip

## 4. Event Markers

- [x] 4.1 Implement confirmed clean dot: solid circle at `xPct(last_vacuumed)`, full opacity, with tooltip "Cleaned [datetime]"
- [x] 4.2 Implement inferred historical dots: back-extrapolate `lastClean - n×interval` while within window, render at 0.3 opacity with tooltip "Est. cleaned [date]"
- [x] 4.3 Implement due date diamond marker: small rotated square at `xPct(dueDate)`, color = green (ratio < 0.7) / amber (0.7–1.0) / hidden (overdue)
- [x] 4.4 Wire tooltip display for overdue band: "Overdue since [dueDate] (N days)"

## 5. Room Row Groups & Sort

- [x] 5.1 Implement `RoomTrackGroup` component: room label section (fixed width 110px desktop / 70px mobile) + two track rows (VAC + MOP)
- [x] 5.2 Room label section shows: room name, urgency dot (🔴/🟡/🟢/⚪), Edit button (opens existing EditModal)
- [x] 5.3 Apply urgency sort in the parent: sort `rows` by `getUrgencyScore` descending before rendering; never-cleaned first, no-schedule last
- [x] 5.4 Separate rooms with a subtle divider line between row groups

## 6. Inline Clean Now Action

- [x] 6.1 Add "Clean Now" button to each room label section
- [x] 6.2 On click: POST `/api/rooms/clean` `{ segment_ids: [room.segment_id], repeat: 1 }` — no setting overrides
- [x] 6.3 On success: update local `rows` state — set `last_vacuumed = new Date().toISOString()`, recompute `vacuum_overdue_ratio = 0`; track re-renders immediately
- [x] 6.4 On error: show brief error text in the room row (red, auto-dismiss after 4s)
- [x] 6.5 Disable button while request in-flight (per-room `busy` state)

## 7. Responsive Behaviour

- [x] 7.1 On mobile: switch to 10-day window, truncate room names to ~10 chars with ellipsis
- [x] 7.2 On mobile: hide Edit button from label section (or move to a tap-to-expand disclosure)
- [x] 7.3 On mobile: reduce dot size and track height to stay readable at narrow widths

## 8. Integration & Cleanup

- [x] 8.1 Replace the table + `dueDateStr` + `overdueClass` logic in `SchedulePanel.tsx` with the new Gantt components; retain `EditModal` import and usage unchanged
- [x] 8.2 Verify the `refreshKey` prop still triggers data reload (existing `useEffect` pattern)
- [x] 8.3 Verify panel renders correctly in the Info tab (mobile) and Info right-tab (desktop) — no layout overflow
- [x] 8.4 Run `npm run build` in `frontend/` and confirm no TypeScript errors
