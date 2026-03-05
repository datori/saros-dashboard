# Vacuum — CLAUDE.md

Python CLI, MCP server, and web dashboard for the **Roborock Saros 10R** robot vacuum, built on top of `python-roborock` (cloud API, not local).

## Project Structure

```
src/vacuum/
  cli.py          # `vacuum` CLI entry point (Typer)
  mcp_server.py   # `vacuum-mcp` MCP server for Claude Desktop
  dashboard.py    # `vacuum-dashboard` FastAPI web dashboard
  client.py       # VacuumClient — all device logic lives here
  config.py       # Credentials + session management
```

**Entry points** (defined in `pyproject.toml`):
- `vacuum` — CLI
- `vacuum-mcp` — MCP server
- `vacuum-dashboard` — web dashboard (default port 8080; port 8080 is occupied on this machine by another process, use `--port 8181`)

**Install**: `pip3 install -e .` (system Python, no venv — `python3-venv` not installed)

## Authentication

Credentials live in `.env`:
```
ROBOROCK_USERNAME=...
ROBOROCK_PASSWORD=...   # optional if session token exists
ROBOROCK_DEVICE_NAME=... # optional, selects device by name
```

Session token cached at `.roborock_session.json` after first login. Includes the IOT base URL to skip a network round-trip on subsequent calls. Run `vacuum login` if password login doesn't work (email code flow).

## VacuumClient API

All methods are `async`. The client must be authenticated before use:

```python
async with VacuumClient() as client:
    status = await client.get_status()
```

Or manually:
```python
client = VacuumClient()
await client.authenticate()
# ...
await client.close()
```

### Status

```python
status = await client.get_status()
# VacuumStatus(state, battery, in_dock, error_code)
```

- `state`: human-readable string from `RoborockStateCode` (e.g. `"charging"`, `"charging_complete"`, `"sweeping"`)
- `in_dock`: derived — true when state code is 8 (charging) or 100 (charging_complete)
- `error_code`: integer, 0 = no error

### Cleaning Parameter Enums

```python
from vacuum.client import FanSpeed, MopMode, WaterFlow, CleanRoute
```

| Enum | Members | Device command |
|------|---------|---------------|
| `FanSpeed` | `OFF`, `QUIET`, `BALANCED`, `TURBO`, `MAX`, `MAX_PLUS`, `SMART` | `SET_CUSTOM_MODE` |
| `MopMode` | `STANDARD`, `FAST`, `DEEP`, `DEEP_PLUS`, `SMART` | `SET_MOP_MODE` |
| `WaterFlow` | `OFF`, `LOW`, `MEDIUM`, `HIGH`, `EXTREME`, `SMART` | `SET_WATER_BOX_CUSTOM_MODE` |
| `CleanRoute` | `STANDARD`, `FAST`, `DEEP`, `DEEP_PLUS`, `SMART` | `SET_MOP_MODE` (same command as MopMode) |

### Control

```python
# All settings params are optional — None means "use device default"
await client.start_clean(fan_speed=FanSpeed.TURBO, water_flow=WaterFlow.HIGH)
await client.pause()
await client.stop()
await client.return_to_dock()
await client.locate()           # plays locate sound
```

### Cleaning Settings

```python
# Read current device defaults
settings = await client.get_current_settings()
# CleanSettings(fan_speed=FanSpeed.BALANCED, mop_mode=MopMode.STANDARD, water_flow=WaterFlow.MEDIUM)

# Persist device-level defaults (without starting a clean)
await client.set_fan_speed(FanSpeed.MAX)
await client.set_mop_mode(MopMode.DEEP)
await client.set_water_flow(WaterFlow.HIGH)
```

### Rooms

```python
rooms = await client.get_rooms()
# [Room(id=1, name='Bedroom'), Room(id=2, name='Closet'), ...]

mapping = await client.rooms_by_name()
# {'bedroom': 1, 'closet': 2, ...}
```

**Known room segment IDs on this device:**

| ID | Name        |
|----|-------------|
| 1  | Bedroom     |
| 2  | Closet      |
| 3  | Bathroom    |
| 4  | Kitchen     |
| 5  | Living room |
| 6  | Study       |
| 7  | Hall        |

### Room / Zone Cleaning

```python
# All settings params optional; SET_* commands are issued before the clean command
await client.clean_rooms([1, 4], repeat=1, fan_speed=FanSpeed.TURBO, mop_mode=MopMode.DEEP)
await client.clean_zones([(x1,y1,x2,y2)], repeat=1, water_flow=WaterFlow.HIGH)
```

### Routines (Scenes)

```python
routines = await client.get_routines()    # list[HomeDataScene]
await client.run_routine("Morning Clean") # case-insensitive
# raises RoutineNotFoundError if not found
```

Routines are user-created "scenes" in the Roborock app. Each has an `id` (int) and `name` (str).

### Consumables

```python
c = await client.get_consumables()
# Consumables(main_brush_pct, side_brush_pct, filter_pct, sensor_pct)
```

- All values are **percentage remaining** (0–100), or `None` if unavailable
- Calculated from `work_time` (seconds) against replace-time constants from `roborock.data`:
  - Main brush: 300h (`MAIN_BRUSH_REPLACE_TIME`)
  - Side brush: 200h (`SIDE_BRUSH_REPLACE_TIME`)
  - Filter: 150h (`FILTER_REPLACE_TIME`)
  - Sensor: 30h (`SENSOR_DIRTY_REPLACE_TIME`)
- **Live readings**: main brush ~80%, side brush ~66%, filter ~59%, sensor ~0% (needs cleaning)

### Clean History

```python
records = await client.get_clean_history(limit=10)
# [CleanRecord(start_time, duration_seconds, area_m2, complete,
#              start_type, clean_type, finish_reason, avoid_count, wash_count), ...]
```

- `start_time`: ISO 8601 UTC string (from Unix timestamp `r.begin`)
- `area_m2`: from `r.square_meter_area` (already in m²)
- `complete`: bool (False = interrupted)
- `start_type`: string name e.g. `"app"`, `"schedule"`, `"routines"` (or `None`)
- `clean_type`: string name e.g. `"all_zone"`, `"select_zone"` (or `None`)
- `finish_reason`: string name e.g. `"finished_cleaning"`, `"manual_interrupt"` (or `None`)
- `avoid_count`, `wash_count`: ints (or `None`)
- The library returns `records` as a list of integer record IDs from `clean_summary` — each must be fetched individually via `get_clean_record(id)`

## Dashboard API Endpoints

The FastAPI dashboard (`dashboard.py`) exposes these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the HTML dashboard |
| GET | `/api/status` | `{state, battery, in_dock, error_code}` |
| GET | `/api/rooms` | `[{id, name}, ...]` |
| GET | `/api/routines` | `["name", ...]` |
| GET | `/api/consumables` | `{main_brush_pct, side_brush_pct, filter_pct, sensor_pct}` |
| GET | `/api/history` | `[{start_time, duration_seconds, area_m2, complete, start_type, clean_type, finish_reason, avoid_count, wash_count}, ...]` |
| GET | `/api/settings` | `{fan_speed, mop_mode, water_flow}` as enum name strings |
| POST | `/api/settings` | Body: `{fan_speed?, mop_mode?, water_flow?}` — sets device defaults |
| POST | `/api/action/{name}` | `name` ∈ {start, stop, pause, dock, locate}; `start` accepts optional body `{fan_speed?, mop_mode?, water_flow?, route?}` |
| POST | `/api/routine/{name}` | Run named routine |
| POST | `/api/rooms/clean` | Body: `{segment_ids: int[], repeat: int, fan_speed?, mop_mode?, water_flow?, route?}` |

## Key Discoveries / Gotchas

**Cloud-only API**: `python-roborock` communicates via Roborock's cloud. No local network control. All commands go through the cloud even when the device is on the same LAN.

**Consumable times are in seconds**: The library stores `work_time` in seconds, not hours. The replace-time constants are also in seconds (e.g. `MAIN_BRUSH_REPLACE_TIME = 1080000` = 300h × 3600).

**Clean history IDs, not records**: `v1.clean_summary.records` is a `list[int]` of record IDs. Each must be fetched individually with `get_clean_record(id)`. Wrap in try/except — some IDs may fail.

**Room IDs are segment IDs**: The `id` field on `Room` is `r.segment_id` from the library. These are stable and correspond to the map segments in the Roborock app.

**in_dock is derived**: The library doesn't expose a direct `in_dock` boolean — it's inferred from `state` codes 8 (charging) and 100 (charging_complete).

**LAN IP detection**: `socket.gethostbyname(socket.gethostname())` returns 127.x on this machine. Use the UDP connect trick instead:
```python
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
lan_ip = s.getsockname()[0]  # → "192.168.0.180"
```

**Port 8080 conflict**: Port 8080 is occupied by another process (`finance-dashboa`, pid ~866531). Default dashboard port works fine at 8181.

**No `fuser` command**: `fuser` is not installed. Use `pkill -f vacuum-dashboard` to kill dashboard processes, or `ps aux | grep vacuum-dashboard` to find PIDs.

**Session base URL caching**: After first auth, the resolved IOT base URL is stored in `.roborock_session.json` under `_base_url`. This skips a `_get_iot_login_info()` round-trip on subsequent connections, noticeably speeding up startup.

## Development Environment

- **Python**: system Python 3 (`/usr/bin/python3`), no venv
- **Install**: `pip3 install -e .`
- **OS**: Linux (Proxmox VE host, kernel 6.8.12)
- **LAN IP**: 192.168.0.180
