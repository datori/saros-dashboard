## Context

The Roborock Saros 10R supports a rich set of cleaning parameters (fan speed, mop mode, water flow, route pattern) that are configurable in the official app. The `python-roborock` library exposes all of these via `SET_CUSTOM_MODE`, `SET_MOP_MODE`, `SET_WATER_BOX_CUSTOM_MODE` commands, and device-specific enums (`RoborockFanSpeedSaros10R`, `RoborockMopModeSaros10R`, `RoborockMopIntensitySaros10R`). Currently, our wrapper ignores all of these, so every clean runs with whatever settings were last set via the official app.

The approach is: introduce our own typed enums that wrap the device-specific library values, wire them into existing clean methods and new setter methods, expose them through the API, and surface them in the dashboard and CLI.

## Goals / Non-Goals

**Goals:**
- Expose fan speed, mop mode, water flow, and route pattern in `VacuumClient` with typed enums
- Let clean commands (`start_clean`, `clean_rooms`, `clean_zones`) accept inline settings that are applied before the clean command is sent
- Add standalone setters that persist device-level defaults
- Add `get_current_settings()` to read what the device currently has active
- Expose settings via dashboard UI panel and API endpoints
- Enrich `CleanRecord` with fields already available from the library (`start_type`, `clean_type`, `finish_reason`, `avoid_count`, `wash_count`)
- Add CLI flags for all settings on clean/rooms/zones subcommands

**Non-Goals:**
- MCP server changes (nice-to-have, deferred)
- Local event log / analytics layer (separate change)
- Continuous 0–30 water flow slider (API is discrete levels only)
- Persisting settings to our own config file (device stores its own defaults)

## Decisions

### Decision: Own enums wrapping library enums

**Choice**: Define `FanSpeed`, `MopMode`, `WaterFlow`, `CleanRoute` as Python `IntEnum` in `client.py`, mapping friendly names to the device-specific integer codes.

**Rationale**: The library's enums are device-specific (`RoborockFanSpeedSaros10R`) and may change across library versions. Our enums form a stable API surface. Mapping is straightforward since we only target the Saros 10R.

**Alternative considered**: Pass raw integers — rejected because it's opaque to callers and breaks if library codes change.

### Decision: Inline settings applied via SET commands before the clean command

**Choice**: When `clean_rooms(fan_speed=FanSpeed.TURBO, ...)` is called, issue the `SET_CUSTOM_MODE` command before `APP_SEGMENT_CLEAN`. The device retains these settings, so they persist for subsequent cleans until changed.

**Rationale**: The Roborock protocol doesn't support per-command settings inline; parameters are set as device state before issuing the clean command. This matches how the official app works.

**Alternative considered**: A separate "configure then clean" two-step in the caller — rejected because it's error-prone and verbose.

### Decision: `None` means "don't change"

**Choice**: All settings parameters default to `None`. When `None`, no `SET_*` command is issued and the device's current setting is used.

**Rationale**: Callers who only care about rooms (not mode) shouldn't be forced to specify all settings. Matches the principle of least surprise — if you don't say, the robot uses what it already has.

### Decision: Enrich CleanRecord in-place, no new data class

**Choice**: Add optional fields to the existing `CleanRecord` dataclass (defaulting to `None`).

**Rationale**: No breaking change for existing callers. Fields are optional since older records or library versions may not have them.

### Decision: `GET /api/settings` + `POST /api/settings`

**Choice**: Expose a settings endpoint that reads/writes fan speed, mop mode, water flow, and route as string identifiers matching our enum names.

**Alternative considered**: Embed settings directly in every clean endpoint body — retained as an option but settings endpoint is cleaner for the dashboard "configure then clean" UX.

## Risks / Trade-offs

- **Command ordering sensitivity**: If `SET_*` and `APP_*` commands arrive out of order due to network issues, the wrong settings may be used. Mitigation: issue commands sequentially (await each), which is already how the client works.
- **Device retains settings**: Applying settings inline permanently changes the device defaults. Mitigation: document this behavior clearly; `get_current_settings()` lets callers inspect state.
- **Library enum coverage gaps**: `custom` and `smart_mode` codes exist in the library but have unclear behavior. Mitigation: expose them in our enums but mark in docstrings that behavior is device-defined.
- **`wash_count`/`avoid_count` may be 0 or None for old records**: Library may not populate these for all history entries. Mitigation: `CleanRecord` fields default to `None`; callers treat `None` as unavailable.

## Open Questions

- Does the Saros 10R support a numeric water intensity within `custom` (code 204), or is it only the 5 discrete levels? If numeric, we may want a `water_flow_level: int` parameter in a future change.
- Should `POST /api/settings` also trigger a re-read to confirm the device accepted the values?
