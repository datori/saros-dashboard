## Why

The current SchedulePanel shows cleaning schedule data as a static text table — due dates as strings, overdue status as colored text. This format requires reading and mental arithmetic to assess urgency. A time-based Gantt visualization makes urgency immediately scannable: overdue rooms break their visual boundary, room priority sorts to the top automatically, and the relationship between "last cleaned" and "next due" is spatial rather than textual.

## What Changes

- Replace the `SchedulePanel` table with a Gantt-style timeline track component
- Each room gets two horizontal tracks (VAC and MOP), positioned on a 21-day window (past 7 + future 14)
- Visual elements: gradient interval band (green→amber as due date approaches), overdue red band, past clean dots, inferred historical dots, due date diamond marker, prominent NOW vertical line
- Rooms sorted by urgency descending (`max(vac_ratio, mop_ratio) × priority_weight`)
- Each room header includes an inline "Clean Now" button that fires `POST /api/rooms/clean` and animates the track on success (dot slides to NOW, overdue band clears)
- Mobile: condense to 10-day window with truncated labels
- No changes to CleanRoomsPanel (retained for multi-room / advanced settings)
- No backend changes required — all data comes from existing `GET /api/schedule`

## Capabilities

### New Capabilities

- `schedule-gantt`: Gantt timeline visualization for the cleaning schedule panel — track layout, event positioning, gradient bands, overdue indicators, NOW line, urgency sort, and inline clean action

### Modified Capabilities

- `dashboard-ui`: The SchedulePanel visual is replaced; tab placement (Info tab) is unchanged

## Impact

- `frontend/src/components/SchedulePanel.tsx` — fully rewritten
- No API changes
- No new npm dependencies (pure CSS/SVG, no charting library)
- Tailwind v4 / shadcn/ui patterns used throughout
