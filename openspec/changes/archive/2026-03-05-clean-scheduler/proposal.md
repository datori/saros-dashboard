## Why

The vacuum system currently has no memory of when rooms were last cleaned or how frequently they should be cleaned. Adding a local scheduling layer enables smarter, AI-assisted cleaning plans — prioritizing the most overdue rooms and estimating run durations to fit available time windows.

## What Changes

- New `scheduler.py` module with a SQLite-backed store for per-room schedules and clean event history
- New `vacuum-scheduler` CLI entry point (or subcommands under `vacuum`) for inspecting and configuring schedules
- New MCP tools for the AI assistant to read schedule state, adjust intervals, plan cleaning sessions, and dispatch cleans
- Dashboard gets a new "Schedule" panel showing overdue status per room with interval configuration
- `POST /api/rooms/clean` and `POST /api/action/start` automatically log a clean event on dispatch

## Capabilities

### New Capabilities

- `clean-scheduler`: SQLite-backed scheduler — room interval config, clean event logging (dispatched = cleaned), overdue ratio computation, run-time estimation, and time-budget planning

### Modified Capabilities

- `mcp-server`: New scheduling tools added — `get_cleaning_schedule`, `set_room_interval`, `plan_clean`, `get_overdue_rooms`
- `web-dashboard`: New Schedule panel in dashboard UI; clean dispatch endpoints auto-log to scheduler

## Impact

- **New file**: `src/vacuum/scheduler.py` — owns SQLite schema, all scheduler logic
- **New dependency**: `aiosqlite` (or stdlib `sqlite3` wrapped in `asyncio.to_thread`)
- **Modified**: `src/vacuum/mcp_server.py` — new MCP tools
- **Modified**: `src/vacuum/dashboard.py` — schedule panel + dispatch hooks
- **DB file**: `vacuum_schedule.db` in project directory (alongside `.roborock_session.json`)
