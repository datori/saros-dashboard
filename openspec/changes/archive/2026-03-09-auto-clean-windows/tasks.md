## 1. Completion Tracking Fix (scheduler.py)

- [x] 1.1 Add `AND e.complete = 1` filter to `_get_last_cleaned()` query in `scheduler.py`
- [x] 1.2 Add `started_at TEXT`, `finished_at TEXT`, and `trigger_name TEXT` columns to `clean_events` table in `init_db()` (use ALTER TABLE IF NOT EXISTS pattern for migration)
- [x] 1.3 Add `priority_weight REAL DEFAULT 1.0` column to `room_schedules` table in `init_db()`
- [x] 1.4 Add `set_room_priority(segment_id, weight)` async function to `scheduler.py`
- [x] 1.5 Include `priority_weight` in `RoomSchedule` dataclass and `as_dict()` output
- [x] 1.6 Update `_get_schedule_sync()` to read and return `priority_weight`

## 2. Priority Scoring (scheduler.py)

- [x] 2.1 Add `TYPE_WEIGHTS` constant dict: `{"vacuum": 1.5, "mop": 1.0}`
- [x] 2.2 Add `compute_priority_score(room_weight, type_weight, overdue_ratio)` function that returns `room_weight × type_weight × overdue_ratio` (infinity if overdue_ratio is inf)
- [x] 2.3 Add `get_priority_queue()` async function that returns all overdue rooms across both modes, scored and sorted descending
- [x] 2.4 Update `_plan_clean_sync()` to sort by priority score instead of raw overdue ratio, and accept rooms from the cross-mode priority queue

## 3. Trigger Management (scheduler.py)

- [x] 3.1 Add `triggers` table to `init_db()`: `name TEXT PRIMARY KEY, budget_min REAL NOT NULL, mode TEXT DEFAULT 'vacuum', notes TEXT`
- [x] 3.2 Add `trigger_events` table to `init_db()`: `id INTEGER PRIMARY KEY, trigger_name TEXT, fired_at TEXT, returned_at TEXT, actual_min REAL, clean_event_id INTEGER`
- [x] 3.3 Add `upsert_trigger(name, budget_min, mode, notes)` async function
- [x] 3.4 Add `delete_trigger(name)` async function
- [x] 3.5 Add `get_triggers()` async function returning list of all triggers
- [x] 3.6 Add `log_trigger_event(trigger_name, clean_event_id)` async function
- [x] 3.7 Add `close_trigger_event(trigger_name)` async function that sets `returned_at` and computes `actual_min`

## 4. Completion Monitor (dashboard.py)

- [x] 4.1 Define `ActiveClean` dataclass: `event_id, segment_ids, dispatched_at, started_at, per_room_estimates, mode`
- [x] 4.2 Add `_active_clean: ActiveClean | None = None` module-level variable
- [x] 4.3 Add `_resolve_clean_success()` async function: marks all rooms complete via `update_clean_duration()`, clears `_active_clean`
- [x] 4.4 Add `_resolve_clean_failure(elapsed_sec)` async function: computes cumulative per-room milestones, creates a new complete event for credited rooms, clears `_active_clean`
- [x] 4.5 Add `_check_active_clean(status)` async function: checks vacuum state against `_active_clean`, detects started/completed/failed transitions, calls resolve functions
- [x] 4.6 Integrate `_check_active_clean()` into `_health_poll_loop()` — call after every status poll
- [x] 4.7 Update `api_rooms_clean()` to populate `_active_clean` after dispatching (segment_ids, per-room estimates, event_id)
- [x] 4.8 Update `api_action()` start handler to populate `_active_clean` for whole-home cleans

## 5. Window Dispatch Loop (dashboard.py)

- [x] 5.1 Add `_window_end: float | None = None` module-level variable (monotonic time)
- [x] 5.2 Add `_open_window(budget_min)` function: sets `_window_end = max(_window_end or 0, now + budget_min * 60)`
- [x] 5.3 Add `_close_window()` async function: sets `_window_end = None`, calls `return_to_dock()` if vacuum is cleaning, closes trigger events
- [x] 5.4 Add `_check_dispatch(status)` async function: if window is open, vacuum is idle/docked, and priority queue has rooms — select batch within remaining time, dispatch, populate `_active_clean`
- [x] 5.5 Integrate `_check_dispatch()` into `_health_poll_loop()` — call after `_check_active_clean()` when no active clean exists
- [x] 5.6 After `_resolve_clean_success()`/`_resolve_clean_failure()`, if window still open, trigger a dispatch check on next poll cycle

## 6. Trigger API Endpoints (dashboard.py)

- [x] 6.1 Add `GET /api/triggers` endpoint returning all configured triggers
- [x] 6.2 Add `PUT /api/triggers/{name}` endpoint to upsert a trigger (body: `{budget_min, mode?, notes?}`)
- [x] 6.3 Add `DELETE /api/triggers/{name}` endpoint to remove a trigger
- [x] 6.4 Add `POST /api/trigger/{name}/fire` endpoint: looks up trigger, calls `_open_window()`, logs trigger event, returns window status
- [x] 6.5 Add `POST /api/trigger/stop` endpoint: calls `_close_window()`, returns confirmation
- [x] 6.6 Add `GET /api/window` endpoint: returns `{active, ends_at, remaining_minutes, current_clean}`

## 7. Schedule API Updates (dashboard.py)

- [x] 7.1 Add `priority_weight` to schedule PATCH endpoint (`api_schedule_room_patch`)
- [x] 7.2 Update `ScheduleRoomPatch` model to include optional `priority_weight: float | None`

## 8. Dashboard UI Updates

- [x] 8.1 Add trigger buttons section to dashboard HTML: configurable trigger buttons (e.g., "Gym", "Shower", "Leaving") that fire `POST /api/trigger/{name}/fire`
- [x] 8.2 Add anti-trigger "Stop" button that fires `POST /api/trigger/stop`
- [x] 8.3 Add window status indicator showing active/inactive state, remaining time, and current clean info
- [x] 8.4 Add trigger management UI: list triggers, create/edit/delete with budget and mode fields
- [x] 8.5 Add priority weight column to room schedule table with inline editing
