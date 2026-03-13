## 1. Scheduler: seed "both" dispatch settings

- [ ] 1.1 Add `INSERT OR IGNORE INTO dispatch_settings` for `mode='both'` in `init_db()` with `fan_speed='balanced', mop_mode='standard', water_flow='vac_then_mop'`

## 2. Dashboard: wire window mode through

- [ ] 2.1 Add `_window_mode: str | None = None` module-level global in `dashboard.py` alongside `_window_end`
- [ ] 2.2 Update `_open_window(budget_min)` to accept a `mode: str = "vacuum"` parameter and set `_window_mode = mode`
- [ ] 2.3 Update `_close_window()` (or wherever `_window_end = None` is set) to also reset `_window_mode = None`
- [ ] 2.4 Update the trigger-fire endpoint (`POST /api/trigger/{name}/fire`) to pass `trigger["mode"]` to `_open_window()`
- [ ] 2.5 Update `WindowOpenRequest` model and `api_window_open` endpoint to accept an optional `mode: str = "vacuum"` field, passing it to `_open_window()`

## 3. Dashboard: "both" dispatch logic in `_check_dispatch`

- [ ] 3.1 Replace `target_mode = queue[0].mode` with `target_mode = _window_mode or queue[0].mode` so the window mode takes precedence
- [ ] 3.2 For the room-selection loop: when `target_mode == "both"`, filter `queue` to entries where `entry.mode == "mop"` (same as mop selection) — the existing filter `entry.mode != target_mode` would otherwise exclude all entries since no queue entries have `mode="both"`
- [ ] 3.3 Verify `ds.get(target_mode, {})` and `scheduler.log_clean(segment_ids, target_mode, ...)` already work correctly for `target_mode="both"` (no further changes needed if dispatch_settings has a "both" row)

## 4. Dashboard: API validation

- [ ] 4.1 Update `api_dispatch_settings_patch()` to allow `mode` ∈ `{"vacuum", "mop", "both"}` (currently rejects "both" with 400)

## 5. HTML/JS: trigger modal

- [ ] 5.1 Add `<option value="both">Both (vac+mop)</option>` to the `#trigger-mode` select in the trigger create/edit modal

## 6. HTML/JS: dispatch settings panel

- [ ] 6.1 Update `loadDispatchSettings()` JS to iterate `['vacuum', 'mop', 'both']` instead of `['vacuum', 'mop']` so the "both" row is rendered
