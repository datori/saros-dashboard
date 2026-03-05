## 1. Dependencies and Entry Point

- [x] 1.1 Add `fastapi` and `uvicorn[standard]` to dependencies in `pyproject.toml`
- [x] 1.2 Add `vacuum-dashboard` entry point in `pyproject.toml` pointing to `vacuum.dashboard:main`

## 2. VacuumClient Extensions

- [x] 2.1 Add `Consumables` dataclass to `client.py` (main_brush_pct, side_brush_pct, filter_pct)
- [x] 2.2 Add `CleanRecord` dataclass to `client.py` (start_time, duration_seconds, area_cm2)
- [x] 2.3 Implement `get_consumables()` method on `VacuumClient` using `v1.consumable`
- [x] 2.4 Implement `get_clean_history(limit=10)` method on `VacuumClient` using clean summary/record commands

## 3. FastAPI Server

- [x] 3.1 Create `src/vacuum/dashboard.py` with FastAPI app and uvicorn lifespan holding a single `VacuumClient`
- [x] 3.2 Implement `GET /api/status` endpoint returning `VacuumStatus` as JSON
- [x] 3.3 Implement `GET /api/rooms` endpoint returning list of `{id, name}`
- [x] 3.4 Implement `GET /api/routines` endpoint returning list of routine names
- [x] 3.5 Implement `GET /api/consumables` endpoint returning consumables with graceful fallback
- [x] 3.6 Implement `GET /api/history` endpoint returning last 10 clean records with graceful fallback
- [x] 3.7 Implement `POST /api/action/{name}` for start/stop/pause/dock/locate
- [x] 3.8 Implement `POST /api/routine/{name}` to trigger a named routine
- [x] 3.9 Implement `POST /api/rooms/clean` accepting `{segment_ids, repeat}` body
- [x] 3.10 Implement `GET /` returning the full single-page HTML dashboard

## 4. Frontend HTML/CSS/JS

- [x] 4.1 Write the HTML shell: grid layout with panels for Status, Actions, Rooms, Room Clean, Routines, Consumables, History
- [x] 4.2 Implement status panel JS: fetch `/api/status` and render state, battery bar, dock badge
- [x] 4.3 Implement actions panel JS: buttons for Start, Stop, Pause, Dock, Locate with in-flight disable + feedback
- [x] 4.4 Implement rooms panel JS: fetch `/api/rooms` and render table
- [x] 4.5 Implement room clean form JS: multi-select checkboxes from rooms list + repeat input + submit to `/api/rooms/clean`
- [x] 4.6 Implement routines panel JS: fetch `/api/routines`, render list with Run buttons, POST on click
- [x] 4.7 Implement consumables panel JS: fetch `/api/consumables`, render progress bars per consumable
- [x] 4.8 Implement history panel JS: fetch `/api/history`, render table of recent jobs
- [x] 4.9 Add 30-second auto-refresh for all data panels
- [x] 4.10 Add CSS styling: clean dark or light theme, progress bars for battery/consumables, loading states

## 5. CLI Entry Point

- [x] 5.1 Implement `main()` in `dashboard.py` using Typer: `--port` option (default 8080), `--no-browser` flag
- [x] 5.2 On start, open browser to `http://localhost:{port}` unless `--no-browser` is passed

## 6. Verification

- [x] 6.1 Run `pip install -e .` to pick up new entry point and dependencies
- [x] 6.2 Launch `vacuum-dashboard` and verify all panels load with live data
- [x] 6.3 Test each action button (start is optional — just verify the API call fires)
- [x] 6.4 Verify consumables and history panels degrade gracefully if data is unavailable
