## Why

There's no visual way to see the vacuum's current state or available capabilities at a glance. A local web dashboard provides a live, comprehensive view of all data the API exposes and a UI surface for all supported actions — useful for exploration, debugging, and ad-hoc control.

## What Changes

- New `web-dashboard` Python module (`src/vacuum/dashboard.py`) serving a FastAPI app
- New `vacuum-dashboard` CLI entry point to launch the server
- Single-page HTML dashboard (served inline, no build step) with:
  - Live status panel (state, battery, dock status, error code)
  - Rooms panel (list all rooms with IDs)
  - Routines panel (list all routines, run button per routine)
  - Consumables panel (brush life, filter life, sensor status)
  - Clean history panel (recent jobs: time, duration, area)
  - Actions panel (start, stop, pause, dock, locate)
  - Room clean form (multi-select rooms + repeat count)
- Auto-refresh of data panels on a configurable interval
- All actions return JSON responses; UI shows success/error feedback

## Capabilities

### New Capabilities
- `web-dashboard`: FastAPI server + single-page HTML UI exposing all vacuum data and actions

### Modified Capabilities
- `vacuum-client`: Add `get_consumables()` and `get_clean_history()` methods to surface additional data in the dashboard

## Impact

- New dependency: `fastapi`, `uvicorn`
- New entry point: `vacuum-dashboard` in `pyproject.toml`
- Extends `VacuumClient` with two new read methods
- No changes to existing CLI commands or MCP server
