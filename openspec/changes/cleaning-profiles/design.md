## Context

The dashboard has two tiers of cleaning settings today:
1. **Device defaults** — persisted on the physical device via `POST /api/settings`, read back via `GET /api/settings`. Shown in the "Clean Settings" panel.
2. **Per-clean overrides** — dropdowns in the "Start clean" and "Room clean" panels. Ephemeral: blank on every page load.

Users who always clean with the same settings (e.g., TURBO fan + VAC_THEN_MOP) must re-select them every session. This change adds a named-profile system so a chosen bundle of settings can be recalled in one tap, cross-device (browser + mobile PWA). Profiles are stored server-side (SQLite) so they survive page refreshes and work identically on any client.

## Goals / Non-Goals

**Goals:**
- Named profiles that bundle fan_speed, mop_mode, water_flow, route overrides
- One profile can be the default — pre-populates override dropdowns on load
- "Device defaults" escape hatch (no overrides sent)
- Full CRUD in the UI: create, rename, edit settings, delete, set-default
- Mobile-friendly modal UI consistent with existing dashboard style
- Cross-device (server-side storage)

**Non-Goals:**
- Room-specific profiles (all rooms share the same profile selection)
- Syncing profiles to the Roborock app or device
- Replacing the device-level defaults system (profiles layer on top)
- Per-user accounts or multi-user profile isolation

## Decisions

### D1: SQLite storage in vacuum_schedule.db (not a new file)

The scheduler already uses `vacuum_schedule.db`. Adding a `profiles` table there avoids a second DB file and keeps all persistent app state in one place. The DB is initialised in `scheduler.init_db()` which runs at dashboard startup.

**Alternative considered**: Separate `profiles.db`. Rejected — unnecessary file proliferation.

### D2: Profiles apply at clean-start time, not profile-select time

Selecting a profile pre-fills the UI dropdowns; no MQTT commands are issued. Settings are applied when the user actually starts a clean. This avoids spurious `SET_*` MQTT commands from mere browsing and keeps the existing clean flow unchanged.

**Alternative considered**: Auto-push device defaults when profile is selected. Rejected — causes unintended device state changes while browsing, and the existing device-defaults panel already handles that.

### D3: NULL fields mean "no override for this setting"

A profile row may have NULL for any of its setting columns. NULL means "don't send a `SET_*` command for this field — let the device use its stored default." This allows profiles that only partially constrain settings (e.g., a profile that sets fan speed but not water flow).

### D4: Single `is_default` flag, enforced at write time

Only one profile can be default. When a profile is set as default (or created with `is_default=true`), all other rows are cleared first in the same transaction. A special client-side "Device defaults" option (id = null) means "no profile, no overrides."

### D5: Profile CRUD via REST, not MCP

No changes to `mcp_server.py` or `cli.py`. Profiles are a dashboard-layer feature for interactive use. MCP tools operate at the `VacuumClient` level which is unchanged.

### D6: Edit modal, not inline editing

CRUD UI uses a modal dialog (consistent with the dashboard's existing action structure). On mobile, a modal is easier to interact with than inline editable rows in a table. The modal contains name field + four setting dropdowns (each with a "— device default —" option mapping to null).

## Risks / Trade-offs

- **DB schema migration**: `init_db()` runs at startup and is additive (CREATE TABLE IF NOT EXISTS). No migration tool needed. Existing schedule data is unaffected.
- **Profile deleted mid-session**: If the active (default) profile is deleted, the UI falls back to "Device defaults" silently. No orphan references since the active profile is resolved at page load, not stored in a session.
- **VAC_THEN_MOP + explicit water flow conflict**: `WaterFlow.VAC_THEN_MOP` (code 235) is itself a water flow enum value that signals the device to vacuum first then mop. A profile using VAC_THEN_MOP cannot also specify a separate mop intensity — they are the same field. Users should be made aware via dropdown option ordering (VAC_THEN_MOP appears as a distinct entry, separate from LOW/MEDIUM/HIGH).

## Migration Plan

1. Add `profiles` table in `scheduler.init_db()` — `CREATE TABLE IF NOT EXISTS`, safe to run on existing DB
2. Add API endpoints to `dashboard.py`
3. Add UI chip bar + modal to `dashboard.py` HTML/JS
4. Wire profile selection into start-clean and room-clean JS flows
5. No data migration required; users create profiles manually after deploy
