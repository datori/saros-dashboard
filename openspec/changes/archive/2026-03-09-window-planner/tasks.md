## 1. Preview API Endpoint (dashboard.py)

- [x] 1.1 Add `GET /api/window/preview` endpoint that calls `scheduler.get_priority_queue()` and returns `{"queue": [entry.as_dict() for entry in queue]}`

## 2. Direct Window Open Endpoint (dashboard.py)

- [x] 2.1 Add `POST /api/window/open` endpoint accepting `{budget_min: float}`, calling `_open_window(budget_min)`, and returning the updated window status (same shape as `GET /api/window`)

## 3. Planner Panel HTML/CSS (dashboard.py)

- [x] 3.1 Add "Window Planner" panel HTML with `data-tab="clean"`: slider input (range 5–90, default 30, step 1), budget label, room list container, summary line, refresh button, and "Open Window" button
- [x] 3.2 Add CSS for planner: slider styling, room list with filled/hollow indicators, cumulative time bars, divider between selected/excluded rooms

## 4. Planner JavaScript (dashboard.py)

- [x] 4.1 Add `loadPlannerPreview()` function that fetches `GET /api/window/preview` and stores the queue in a module-level variable
- [x] 4.2 Add `renderPlanner()` function that takes the cached queue and current slider value, runs client-side batch selection (mode from top entry, greedy fill by score), and renders the room list with selected/excluded sections, cumulative bars, and summary
- [x] 4.3 Wire slider `input` event to call `renderPlanner()` (no API call — purely client-side re-render)
- [x] 4.4 Wire refresh button to call `loadPlannerPreview()` then `renderPlanner()`
- [x] 4.5 Wire "Open Window" button to `POST /api/window/open` with the slider's current value, then refresh window status display
- [x] 4.6 Call `loadPlannerPreview()` in `refreshAll()` so the planner loads on page open

## 5. Manual Duration Estimates (scheduler.py)

- [x] 5.1 Add `default_duration_sec REAL` column to `room_schedules` table in `init_db()` (ALTER TABLE migration pattern)
- [x] 5.2 Add `set_room_duration(segment_id, seconds)` async function
- [x] 5.3 Update `_estimate_duration_sync()` to check `default_duration_sec` first (Tier 0) — if all requested rooms have a value, return sum + 300s overhead; otherwise fall through to existing tiers
- [x] 5.4 Include `default_duration_sec` in `RoomSchedule` dataclass, `as_dict()`, and `_get_schedule_sync()`

## 6. Duration in Dashboard UI (dashboard.py)

- [x] 6.1 Add `default_duration_sec` to `ScheduleRoomPatch` model and `api_schedule_room_patch()` handler
- [x] 6.2 Add "Est. duration (min)" field to the schedule edit modal HTML
- [x] 6.3 Update `openEditModal()` to populate the duration field, and `saveEditModal()` to send it (converting min→sec)
- [x] 6.4 Add duration column to the schedule table showing the manual estimate (or "—" if unset)
