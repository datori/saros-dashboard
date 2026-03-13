## Why

Trigger mode is stored in the database but never actually wired through to dispatch — `_check_dispatch` derives `target_mode` from the top of the priority queue, ignoring the trigger's configuration entirely. Additionally, users who run "vac+mop" cleans manually have no way to auto-dispatch in that combined mode.

## What Changes

- **Wire trigger mode through dispatch**: store the active window's mode in a `_window_mode` global; pass it from the trigger-fire endpoint into `_open_window()`; use it in `_check_dispatch()` to drive room selection and dispatch settings lookup
- **Add "both" as a valid trigger mode**: when `_window_mode == "both"`, select mop-overdue rooms (same pool as mop dispatch), apply `dispatch_settings["both"]` settings, and log the event as `mode="both"` — giving rooms credit for both vacuum and mop
- **Seed "both" dispatch settings**: add a third row to `dispatch_settings` table on `init_db()` with sensible defaults (`fan_speed=balanced, mop_mode=standard, water_flow=vac_then_mop`)
- **Expose "both" in API and UI**: allow `mode="both"` on `PATCH /api/dispatch-settings/{mode}`, add "Both" option to the trigger-mode dropdown, and render the "both" row in the dispatch settings panel

## Capabilities

### New Capabilities

*(none — all changes are modifications to existing capabilities)*

### Modified Capabilities

- `clean-triggers`: Trigger mode is now wired through to the cleaning window and influences dispatch; `mode="both"` is a valid trigger mode
- `dispatch-settings`: A third mode row (`both`) is seeded on init; API and UI support all three modes
- `clean-windows`: The window now carries a mode; `_check_dispatch` uses window mode to select rooms and apply dispatch settings instead of reading the priority queue's top entry mode

## Impact

- `src/vacuum/scheduler.py` — `init_db()`: seed `dispatch_settings` "both" row
- `src/vacuum/dashboard.py` — new `_window_mode` global; `_open_window()` accepts `mode`; trigger-fire endpoint passes trigger mode; `api_window_open` accepts optional mode; `_check_dispatch()` uses `_window_mode` for room selection and settings lookup; `api_dispatch_settings_patch()` allows "both"
- Dashboard HTML/JS — trigger-mode `<select>` gains "Both" option; dispatch settings panel renders "both" row
- No changes to `client.py`, `cli.py`, or `mcp_server.py`
