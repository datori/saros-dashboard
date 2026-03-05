## 1. Client Enums

- [x] 1.1 Add `FanSpeed` IntEnum to `client.py` mapping OFF/QUIET/BALANCED/TURBO/MAX/MAX_PLUS/SMART to Saros 10R codes (101–110)
- [x] 1.2 Add `MopMode` IntEnum to `client.py` mapping STANDARD/FAST/DEEP/DEEP_PLUS/SMART to codes (300–306)
- [x] 1.3 Add `WaterFlow` IntEnum to `client.py` mapping OFF/LOW/MEDIUM/HIGH/EXTREME/SMART to codes (200–250)
- [x] 1.4 Add `CleanRoute` IntEnum to `client.py` (same codes as MopMode — controls route for both vac and mop)

## 2. Client Setters and Getter

- [x] 2.1 Add `set_fan_speed(speed: FanSpeed)` method — sends `SET_CUSTOM_MODE` with enum value
- [x] 2.2 Add `set_mop_mode(mode: MopMode)` method — sends `SET_MOP_MODE` with enum value
- [x] 2.3 Add `set_water_flow(flow: WaterFlow)` method — sends `SET_WATER_BOX_CUSTOM_MODE` with enum value
- [x] 2.4 Add `get_current_settings()` method — reads `custom_mode`, `mop_mode`, `water_box_custom_mode` from status, returns `CleanSettings` dataclass with `fan_speed`, `mop_mode`, `water_flow` as enum members or `None`
- [x] 2.5 Add `CleanSettings` dataclass to `client.py` with `fan_speed`, `mop_mode`, `water_flow` fields and `as_dict()` method

## 3. Inline Settings on Clean Commands

- [x] 3.1 Update `start_clean()` to accept `fan_speed`, `mop_mode`, `water_flow`, `route` optional params; issue SET commands for non-None values before `APP_START`
- [x] 3.2 Update `clean_rooms()` to accept same params; issue SET commands before `APP_SEGMENT_CLEAN`
- [x] 3.3 Update `clean_zones()` to accept same params; issue SET commands before `APP_ZONED_CLEAN`

## 4. Enriched CleanRecord

- [x] 4.1 Add `start_type`, `clean_type`, `finish_reason` optional `str | None` fields to `CleanRecord`
- [x] 4.2 Add `avoid_count`, `wash_count` optional `int | None` fields to `CleanRecord`
- [x] 4.3 Update `get_clean_history()` to populate new fields from library record (use `.name` on enums, catch AttributeError → None)
- [x] 4.4 Update `CleanRecord.as_dict()` to include new fields

## 5. Dashboard API

- [x] 5.1 Add `GET /api/settings` endpoint — calls `client.get_current_settings()`, returns JSON
- [x] 5.2 Add `POST /api/settings` endpoint — accepts `{fan_speed, mop_mode, water_flow}` string names, validates against enums (400 on invalid), calls appropriate setters
- [x] 5.3 Update `POST /api/action/start` to accept optional JSON body with `fan_speed`, `mop_mode`, `water_flow`, `route` fields and pass to `start_clean()`
- [x] 5.4 Update `POST /api/rooms/clean` to accept optional `fan_speed`, `mop_mode`, `water_flow`, `route` in body and pass to `clean_rooms()`
- [x] 5.5 Update `GET /api/history` response to include new `CleanRecord` fields

## 6. Dashboard UI

- [x] 6.1 Add "Clean Settings" panel to `dashboard.py` HTML with dropdowns for fan speed, mop mode, water flow, and route
- [x] 6.2 Populate dropdowns from `GET /api/settings` on page load
- [x] 6.3 Wire "Save Settings" button to `POST /api/settings`
- [x] 6.4 Update clean history table to show `start_type`, `clean_type`, `finish_reason` columns
- [x] 6.5 Update room clean form to include optional settings dropdowns (fan speed, mop mode, water flow, route) that POST inline settings with the clean request

## 7. CLI

- [x] 7.1 Add `--fan-speed`, `--mop-mode`, `--water-flow`, `--route` options to `vacuum clean` subcommand; validate against enum names (case-insensitive)
- [x] 7.2 Add same four options to `vacuum rooms` subcommand
- [x] 7.3 Add `vacuum settings` subcommand: no flags → print current settings table; with flags → call setters and confirm
- [x] 7.4 Add valid-value error messages for all new options (list accepted values on bad input)

## 8. CLAUDE.md Update

- [x] 8.1 Update `CLAUDE.md` VacuumClient API section to document `FanSpeed`, `MopMode`, `WaterFlow`, `CleanRoute` enums and new method signatures
- [x] 8.2 Update `CLAUDE.md` Dashboard API section to document new and updated endpoints
