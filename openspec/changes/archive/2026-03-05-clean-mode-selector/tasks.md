## 1. Client: Add VAC_THEN_MOP enum member

- [x] 1.1 Add `VAC_THEN_MOP = 235` to `WaterFlow` enum in `src/vacuum/client.py`

## 2. Dashboard: Mode inference helper

- [x] 2.1 Add `_infer_clean_mode(fan_speed_str: str | None, water_flow_str: str | None) -> str` helper in `dashboard.py` — returns `"mop"` if fan_speed is `"OFF"`, `"both"` if water_flow is non-None and not `"OFF"`, else `"vacuum"`
- [x] 2.2 Replace the inline mode inference in `api_rooms_clean` with a call to `_infer_clean_mode`
- [x] 2.3 Replace the inline mode inference in `api_action` (start branch) with a call to `_infer_clean_mode`

## 3. Dashboard: Add VAC_THEN_MOP to water flow selects

- [x] 3.1 Add `<option>VAC_THEN_MOP</option>` to the rooms clean water flow `<select>` in the HTML
- [x] 3.2 Add `VAC_THEN_MOP` to the `populateSelect` call for `set-water-flow` in `loadSettings()` (Clean Settings panel)

## 4. Dashboard: Clean mode selector — Clean Rooms panel

- [x] 4.1 Add a "Clean Mode" `<select>` row to the Clean Rooms panel override settings grid (above fan speed), with options: `""` (no preference), `vacuum`, `mop`, `both`, `vac_then_mop`
- [x] 4.2 Add `onchange="applyCleanMode('rooms', this.value)"` to the clean mode select
- [x] 4.3 Implement `applyCleanMode(prefix, mode)` JS function that maps mode to fan_speed/water_flow select values:
  - `vacuum` → water_flow = `"OFF"`, fan_speed cleared
  - `mop` → fan_speed = `"OFF"`, water_flow cleared
  - `both` → both cleared
  - `vac_then_mop` → water_flow = `"VAC_THEN_MOP"`, fan_speed cleared

## 5. Dashboard: Clean mode selector — Start Clean action

- [x] 5.1 Add an inline override section below the action buttons in the Actions panel (similar structure to Clean Rooms overrides): Clean Mode, Fan Speed, Water Flow selects
- [x] 5.2 Wire the clean mode select to `applyCleanMode('start', this.value)` (reuse the same function with a prefix)
- [x] 5.3 Update `doAction('start')` to read fan_speed and water_flow from the start-panel selects and include them in the POST body when non-empty
