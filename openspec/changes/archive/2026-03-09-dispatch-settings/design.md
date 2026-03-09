## Context

The Roborock Saros 10R is a combo vacuum+mop. Device behavior is controlled by settings:
- `fan_speed`: OFF disables vacuuming; BALANCED/TURBO/etc. for vacuum power
- `water_flow`: OFF disables mopping; LOW/MEDIUM/HIGH/etc. for mop water
- `mop_mode`: STANDARD/DEEP/etc. for mop pattern
- `route`: STANDARD/DEEP/etc. for navigation pattern

The scheduler's `_check_dispatch()` calls `client.clean_rooms(segment_ids)` with no settings, so the device uses whatever was last set manually.

## Goals / Non-Goals

**Goals:**
- Store per-mode (vacuum/mop) device settings in SQLite
- Apply settings automatically at dispatch time
- Ship sensible defaults so it works out of the box
- Dashboard UI to view and change dispatch settings

**Non-Goals:**
- Per-room settings overrides (global per-mode is sufficient for now)
- Per-trigger settings (triggers select mode via their config, settings come from the mode)
- Changing settings for manual dashboard-initiated cleans (those use whatever the user picks)

## Decisions

### 1. Simple key-value storage per mode

A `dispatch_settings` table with `mode TEXT PRIMARY KEY` and columns for each setting. Two rows: `vacuum` and `mop`. Settings are nullable — `NULL` means "use device default / don't send."

**Why not a generic key-value store?** The settings are a fixed, known set. Typed columns are simpler to query and validate.

### 2. Defaults seeded on first init

`init_db()` inserts default rows if they don't exist:
- `vacuum`: `fan_speed=balanced, mop_mode=NULL, water_flow=off, route=NULL`
- `mop`: `fan_speed=off, mop_mode=standard, water_flow=medium, route=NULL`

NULL means "don't set this parameter" — the device keeps its current value for that setting.

### 3. Settings applied in `_check_dispatch()` only

Manual cleans from the dashboard (POST /api/rooms/clean, POST /api/action/start) continue to use whatever settings the user passes. Only auto-dispatch from the window system applies dispatch settings.

### 4. Settings passed through `clean_rooms()` kwargs

The dispatch code reads settings from the DB, converts string names to enum values, and passes them as kwargs to `client.clean_rooms()`. The client's `_apply_settings()` handles the actual device commands.

## Risks / Trade-offs

- **Device state pollution**: Dispatch settings change device defaults (that's how `_apply_settings` works — it sends SET_* commands). After an auto-clean, the device's "default" fan speed may differ from what the user set manually. → Acceptable: the dashboard's manual controls always send explicit settings, overriding whatever dispatch set.
- **NULL ambiguity**: NULL means "don't change this setting." If a user wants to explicitly use the device's SMART mode, they set it. If they want "whatever was last set," they leave it NULL. This is clear enough for two modes.
