## 1. Scheduler module — database and core logic

- [x] 1.1 Create `src/vacuum/scheduler.py` with SQLite schema: `room_schedules`, `clean_events`, `clean_event_rooms` tables; init function creates DB + tables if not exist
- [x] 1.2 Implement `sync_rooms(rooms: list[Room])` — upserts segment_id + name, preserves existing interval config
- [x] 1.3 Implement `set_room_interval(segment_id, mode, days)` and `set_room_notes(segment_id, notes)`
- [x] 1.4 Implement `log_clean(segment_ids, mode, source)` — inserts clean_events + clean_event_rooms rows with dispatched_at=now
- [x] 1.5 Implement `get_schedule()` — returns all rooms with last_vacuumed, last_mopped, overdue ratios (NULL interval → NULL ratio)
- [x] 1.6 Implement `get_overdue_rooms(mode)` — rooms where overdue_ratio ≥ 1.0, sorted descending; never-cleaned rooms with interval → infinity priority
- [x] 1.7 Implement `estimate_duration(segment_ids)` — three-tier: exact match avg → per-room decomposition + 300s overhead → area-based prior + 300s overhead → None
- [x] 1.8 Implement `plan_clean(max_minutes, mode)` — greedy selection by overdue ratio descending within time budget; returns selected rooms, estimated total, deferred list

## 2. MCP server — scheduling tools

- [x] 2.1 Add `get_cleaning_schedule()` MCP tool — calls `scheduler.get_schedule()`, returns full room list
- [x] 2.2 Add `get_overdue_rooms(mode="vacuum")` MCP tool — calls `scheduler.get_overdue_rooms()`
- [x] 2.3 Add `set_room_interval(room, mode, days)` MCP tool — resolves room name to segment_id via `rooms_by_name()`, calls `scheduler.set_room_interval()`; raises error if room not found
- [x] 2.4 Add `plan_clean(max_minutes=None, mode="vacuum")` MCP tool — calls `scheduler.plan_clean()`, returns recommended rooms with overdue ratios and estimated minutes
- [x] 2.5 Add `set_room_notes(room, notes)` MCP tool — resolves name to segment_id, calls `scheduler.set_room_notes()`

## 3. Dashboard — API endpoints

- [x] 3.1 On dashboard startup (lifespan), call `sync_rooms()` with rooms from device
- [x] 3.2 Add `GET /api/schedule` endpoint — calls `scheduler.get_schedule()`, returns JSON array
- [x] 3.3 Add `PATCH /api/schedule/rooms/{segment_id}` endpoint — accepts `{vacuum_days?, mop_days?, notes?}`, calls appropriate scheduler setters
- [x] 3.4 Hook `POST /api/rooms/clean` — after successful dispatch, call `scheduler.log_clean(segment_ids, mode, source="dashboard")` where mode is inferred from water_flow param
- [x] 3.5 (Optional) Hook `POST /api/action/start` for whole-home clean — if water_flow param present, log_clean with all room IDs

## 4. Dashboard — Schedule UI panel

- [x] 4.1 Add Schedule panel HTML section to dashboard template (after Settings panel)
- [x] 4.2 Implement `loadSchedule()` JS function — fetches `/api/schedule`, renders table with room, last vacuumed, last mopped, vacuum due, mop due, edit button
- [x] 4.3 Add overdue highlighting CSS — cells with overdue_ratio ≥ 1.0 styled red/orange; "Never" shown for rooms with interval but no history
- [x] 4.4 Implement inline interval edit — modal or inline form, PATCH `/api/schedule/rooms/{id}`, refresh panel on success
- [x] 4.5 Wire `loadSchedule()` into page load and 30s auto-refresh cycle

## 5. Verify

- [ ] 5.1 Confirm `sync_rooms()` populates all 7 known rooms in scheduler DB on dashboard start
- [ ] 5.2 Dispatch a room clean from dashboard, verify `clean_events` row appears in DB with correct segment_ids and mode
- [ ] 5.3 Set a vacuum interval via MCP `set_room_interval`, verify `get_cleaning_schedule` reflects it
- [ ] 5.4 Call `plan_clean(max_minutes=30)` via MCP, verify response contains rooms + estimates
- [ ] 5.5 Confirm schedule panel renders in dashboard with correct overdue indicators
