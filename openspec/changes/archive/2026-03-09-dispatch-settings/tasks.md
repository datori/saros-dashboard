## 1. Dispatch Settings Storage (scheduler.py)

- [x] 1.1 Add `dispatch_settings` table to `init_db()`: `mode TEXT PRIMARY KEY, fan_speed TEXT, mop_mode TEXT, water_flow TEXT, route TEXT`
- [x] 1.2 Seed default rows in `init_db()` if not present: vacuum (`fan_speed=balanced, water_flow=off`) and mop (`fan_speed=off, mop_mode=standard, water_flow=medium`)
- [x] 1.3 Add `get_dispatch_settings()` async function returning dict keyed by mode
- [x] 1.4 Add `update_dispatch_settings(mode, **kwargs)` async function that updates only provided fields

## 2. Apply Settings at Dispatch (dashboard.py)

- [x] 2.1 Update `_check_dispatch()` to load dispatch settings for `target_mode` via `scheduler.get_dispatch_settings()` and pass them as kwargs to `client.clean_rooms()`
- [x] 2.2 Add helper `_parse_dispatch_settings(settings_row)` that converts string setting names to enum values (FanSpeed, MopMode, WaterFlow, CleanRoute), skipping None values

## 3. Dispatch Settings API (dashboard.py)

- [x] 3.1 Add `GET /api/dispatch-settings` endpoint returning settings for both modes
- [x] 3.2 Add `PATCH /api/dispatch-settings/{mode}` endpoint accepting partial settings object, calling `scheduler.update_dispatch_settings()`

## 4. Dispatch Settings UI (dashboard.py)

- [x] 4.1 Add "Dispatch Settings" section to the triggers/auto-clean panel showing current vacuum and mop mode settings with dropdown selectors for fan_speed, mop_mode, water_flow, and route
- [x] 4.2 Add `loadDispatchSettings()` JS function that fetches and renders the settings
- [x] 4.3 Add `saveDispatchSetting(mode, field, value)` JS function that PATCHes individual settings on change
- [x] 4.4 Add `loadDispatchSettings` to `refreshAll()` loaders
