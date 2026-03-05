## Why

The vacuum client, CLI, and dashboard currently expose only basic start/stop/dock commands with no way to configure cleaning parameters (suction power, mop mode, water flow, route pattern). Every clean runs with whatever settings are currently saved on the device. Adding explicit parameter control unlocks the full capability of the Saros 10R that users already configure in the Roborock app.

## What Changes

- **VacuumClient**: Add `fan_speed`, `mop_mode`, `water_flow`, and `route` parameters to `clean_rooms()`, `clean_zones()`, and `start_clean()`; expose `FanSpeed`, `MopMode`, `WaterFlow`, `CleanRoute` enums
- **VacuumClient**: Add standalone `set_fan_speed()`, `set_mop_mode()`, `set_water_flow()`, `set_route()` methods for persistent device-level settings
- **VacuumClient**: Enrich `CleanRecord` with `start_type`, `clean_type`, `finish_reason`, `avoid_count`, `wash_count` fields
- **VacuumClient**: Add `get_current_settings()` to retrieve active fan speed, mop mode, and water flow from device status
- **Dashboard**: Add a "Clean Settings" panel to configure all parameters before triggering cleans
- **Dashboard API**: Add `GET /api/settings` and `POST /api/settings` endpoints; extend `POST /api/rooms/clean` and `POST /api/action/start` to accept optional settings payload
- **CLI**: Add `--fan-speed`, `--mop-mode`, `--water-flow`, `--route` flags to `clean`, `rooms`, and `zones` subcommands

## Capabilities

### New Capabilities
- `cleaning-settings`: Fan speed, mop mode, water flow, and route pattern control — enums, client methods, API endpoints, dashboard UI, and CLI flags

### Modified Capabilities
- `vacuum-client`: `clean_rooms()`, `clean_zones()`, `start_clean()` signatures extended; `CleanRecord` gains new fields; new getter/setter methods added
- `web-dashboard`: New settings panel, enriched history table, extended clean endpoints
- `cli`: New flags on `clean`, `rooms`, `zones` subcommands

## Impact

- `src/vacuum/client.py`: New enums, updated method signatures, new methods, updated `CleanRecord`
- `src/vacuum/dashboard.py`: New `/api/settings` endpoints, updated clean endpoints to accept settings
- `src/vacuum/mcp_server.py`: May want to expose settings as tool parameters (scope: nice-to-have, not required)
- `src/vacuum/cli.py`: New option flags on existing subcommands
- No new dependencies — all enum values already exist in `python-roborock`
