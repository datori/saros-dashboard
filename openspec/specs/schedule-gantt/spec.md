# schedule-gantt Specification

## Purpose
TBD - created by archiving change schedule-gantt-view. Update Purpose after archive.
## Requirements
### Requirement: Gantt timeline layout
The SchedulePanel SHALL render a Gantt-style timeline with a fixed date window. Desktop SHALL use a 21-day window (past 7 days + today + future 13 days). Mobile (viewport < 768px) SHALL use a 10-day window (past 2 days + today + future 7 days).

#### Scenario: Desktop window renders 21 days
- **WHEN** the viewport is ≥ 768px wide
- **THEN** the track area spans 21 days with the NOW line positioned at day 8 from the left

#### Scenario: Mobile window condenses to 10 days
- **WHEN** the viewport is < 768px wide
- **THEN** the track area spans 10 days with the NOW line at day 3 from the left

---

### Requirement: Per-room track rows
The panel SHALL render one row group per room in the schedule. Each row group SHALL contain a room label section (left, fixed width) and two track rows: one for VAC (vacuum) and one for MOP. Tracks with no schedule set for that mode SHALL render as a muted ghost line.

#### Scenario: Room with both VAC and MOP schedules
- **WHEN** a room has both `vacuum_days` and `mop_days` set
- **THEN** two active tracks are rendered, one labeled VAC and one labeled MOP

#### Scenario: Room with VAC only
- **WHEN** a room has `vacuum_days` set but `mop_days` is null
- **THEN** the VAC track is active and the MOP track renders as a dotted ghost line with "No schedule" indicator

#### Scenario: Room with no schedules
- **WHEN** a room has both `vacuum_days` and `mop_days` null
- **THEN** both tracks render as ghost lines; the room appears at the bottom of the urgency sort

---

### Requirement: Urgency sort
Rooms SHALL be sorted by descending urgency score. Urgency score = `max(vacuum_overdue_ratio, mop_overdue_ratio) × priority_weight`. Rooms where either ratio is null (has interval but never cleaned) SHALL sort first. Rooms with no schedule intervals SHALL sort last. Secondary sort key is room name (alphabetical, ascending).

#### Scenario: Never-cleaned room sorts first
- **WHEN** a room has `vacuum_days` set and `last_vacuumed` is null
- **THEN** that room appears before rooms with partial overdue ratios

#### Scenario: No-schedule rooms sink to bottom
- **WHEN** a room has no interval set for either mode
- **THEN** it appears below all rooms that have any schedule interval

---

### Requirement: Gradient interval band
For each track with a schedule, the panel SHALL render a gradient band from the last clean date to the due date. The gradient SHALL transition from teal-green at the left anchor to amber at 70% through the interval to orange-red at 100% (the due date).

#### Scenario: Band renders between clean and due
- **WHEN** `last_vacuumed` is set and `vacuum_days` is set
- **THEN** a gradient div spans from xPct(lastClean) to xPct(dueDate) on the track

#### Scenario: Due date outside window — band exits right edge
- **WHEN** the due date is beyond the right edge of the window
- **THEN** the band extends to the right edge; a `→ Nd` label appears at the right boundary

---

### Requirement: Overdue red band
When the due date has passed (overdue), the panel SHALL render a solid red band from the due date position to the NOW line. This band SHALL appear in addition to (or replacing) the gradient band if the entire interval is already past.

#### Scenario: Overdue band visible when past due
- **WHEN** `vacuum_overdue_ratio` ≥ 1.0
- **THEN** a red band spans from xPct(dueDate) to xPct(now) on the VAC track

#### Scenario: Never-cleaned track is entirely red
- **WHEN** `last_vacuumed` is null and `vacuum_days` is set
- **THEN** the entire track from the left window edge to NOW is rendered in solid red; no gradient band is shown

---

### Requirement: Past clean dots
The panel SHALL render a solid dot at the position of the most recent confirmed clean event (`last_vacuumed` / `last_mopped`). Additional inferred historical dots SHALL be rendered by back-extrapolating: `lastClean - n × intervalDays` for n = 1, 2, … while within the window. Inferred dots SHALL render at reduced opacity (≤ 0.35) to distinguish them from the confirmed dot.

#### Scenario: Confirmed dot at last clean position
- **WHEN** `last_vacuumed` is within the window
- **THEN** a full-opacity dot appears at xPct(last_vacuumed) on the VAC track

#### Scenario: Inferred dots extrapolated backward
- **WHEN** `last_vacuumed - 1 × vacuum_days` is within the window
- **THEN** a low-opacity dot appears at that x position

#### Scenario: Last clean outside window — no confirmed dot
- **WHEN** `last_vacuumed` is before the window start
- **THEN** no confirmed dot is rendered; inferred dots may still appear if they fall within the window

#### Scenario: Combined-run dot on VAC track
- **WHEN** `last_vacuum_combined` is true (vacuum credit came from a mode='both' run)
- **THEN** the VAC track's confirmed dot SHALL render in sky-blue (`#38bdf8`) instead of white, signaling the credit came from a simultaneous vac + mop run rather than a dedicated vacuum pass

---

### Requirement: Due date diamond marker
When the due date falls within the window, the panel SHALL render a small diamond marker at xPct(dueDate). The marker color SHALL match the urgency: green if ratio < 0.7, amber if 0.7 ≤ ratio < 1.0, red if overdue.

#### Scenario: Green diamond for upcoming due date
- **WHEN** due date is within the window and ratio < 0.7
- **THEN** a green diamond marker appears at the due date position

#### Scenario: Red diamond (or no marker) when overdue
- **WHEN** ratio ≥ 1.0
- **THEN** no future diamond is shown (due date is in the past); the overdue band conveys urgency instead

---

### Requirement: NOW vertical line
The panel SHALL render a single vertical line at the current date/time position, spanning all track rows. The line SHALL be visually prominent (white or primary color, 2px). A "TODAY" label SHALL appear at the top of the line.

#### Scenario: NOW line spans all rows
- **WHEN** the panel renders
- **THEN** a vertical line at xPct(now) is visible across all room track rows

---

### Requirement: Inline Clean Now action
Each room row group SHALL include a "Clean Now" button. Clicking it SHALL POST to `/api/rooms/clean` with `{ segment_ids: [room.segment_id], repeat: 1 }` and no setting overrides. On success, the component SHALL update local state: set `last_vacuumed` (or `last_mopped` if MOP-only) to the current timestamp, causing the track to re-render immediately without waiting for the next refresh cycle.

#### Scenario: Clean Now fires rooms/clean
- **WHEN** user clicks "Clean Now" on a room
- **THEN** POST `/api/rooms/clean` is called with the room's segment_id

#### Scenario: Track animates after successful clean
- **WHEN** the API returns success
- **THEN** the room's track re-renders with `last_vacuumed` = now: confirmed dot at NOW, overdue band cleared, gradient band reset

#### Scenario: Error feedback on failure
- **WHEN** the API returns an error
- **THEN** a brief error message is shown in the room row; the track is not updated

---

### Requirement: Hover tooltips
Track elements SHALL show tooltips on hover revealing exact dates: confirmed dot → "Cleaned [date]", inferred dot → "Est. cleaned [date]", due marker → "Due [date]", overdue band → "Overdue since [date] ([N] days)".

#### Scenario: Confirmed dot tooltip
- **WHEN** user hovers over the confirmed clean dot
- **THEN** a tooltip shows the exact clean datetime

#### Scenario: Combined-run dot tooltip
- **WHEN** user hovers over a sky-blue combined-run dot on the VAC track
- **THEN** the tooltip SHALL read "Cleaned [datetime] (combined vac + mop run)"

#### Scenario: Overdue band tooltip
- **WHEN** user hovers over the red overdue band
- **THEN** a tooltip shows "Overdue since [due date] (N days)"

---

### Requirement: Date axis
The panel SHALL render a date axis at the top of the track area. Tick marks SHALL appear every 3 days for the 21-day window (7 ticks) and every 2 days for the 10-day window (5 ticks). The current date tick SHALL be labeled "TODAY" and visually distinguished.

#### Scenario: Date axis ticks rendered
- **WHEN** the panel renders on desktop
- **THEN** 7 date labels appear above the track area, evenly spaced

#### Scenario: TODAY label distinguished
- **WHEN** the tick for the current date is rendered
- **THEN** it is labeled "TODAY" and uses the primary color instead of muted foreground

