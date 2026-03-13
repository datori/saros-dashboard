## Why

Cleaning settings chosen in the dashboard (fan speed, water flow, mop mode) are ephemeral — they reset to blank on every page load and must be re-entered for every clean. Users who always vacuum at TURBO or always mop with VAC_THEN_MOP have no way to save those preferences. The dashboard needs a named-profile system so common cleaning configurations are one tap away, from any device (browser or mobile PWA).

## What Changes

- New **profiles** concept: named bundles of cleaning settings (fan_speed, mop_mode, water_flow, route) stored server-side in SQLite
- A profile can be marked as the **default** — it pre-populates override dropdowns on every page load
- A special **Device defaults** option (no overrides) is always available as an escape hatch
- Profile selector UI (chip/pill bar) added to the "Start clean" and "Room clean" panels
- Basic CRUD UI (create, edit, delete, set-default) accessible from the same bar — mobile-friendly modals
- New API endpoints: `GET/POST /api/profiles`, `PUT/DELETE /api/profiles/{id}`
- Profiles apply settings at clean-start time (not at profile-select time); no extra MQTT commands on selection

## Capabilities

### New Capabilities

- `cleaning-profiles`: Server-side named cleaning profiles — SQLite storage, REST API, chip-bar UI with edit modals, default-profile selection, integration with start-clean and room-clean flows

### Modified Capabilities

- `cleaning-settings`: The existing device-defaults settings panel is unchanged, but the start-clean and room-clean override dropdowns now receive initial values from the active profile instead of being blank

## Impact

- `src/vacuum/dashboard.py` — new API endpoints, new HTML/JS UI components, profile integration into start/room clean flows
- `vacuum_schedule.db` — new `profiles` table (schema migration on startup)
- No changes to `client.py`, `scheduler.py`, `cli.py`, or `mcp_server.py`
