## Why

The dashboard currently exposes fan speed, mop mode, water flow, and route as raw knobs — but provides no way to express the high-level intent of a clean: vacuum only, mop only, both at once, or vacuum followed by mopping. Users must know that `FanSpeed=OFF` means mop-only and `WaterFlow=OFF` means vacuum-only; this is non-obvious and error-prone. Additionally, `WaterFlow.VAC_THEN_MOP` (value 235, the Saros 10R's sequential vacuum-then-mop mode) is not in the client enum at all, making that mode unreachable from the dashboard.

## What Changes

- Add `WaterFlow.VAC_THEN_MOP = 235` to `client.py` (the Roborock-native sequential mode)
- Add a **Clean Mode** dropdown to the **Clean Rooms** panel: Vacuum only / Mop only / Both / Vacuum then Mop
- Add a **Clean Mode** dropdown to the **Start Clean** action (which currently uses device defaults with no overrides)
- Selecting a clean mode pre-populates `fan_speed` and `water_flow` fields; individual overrides remain editable
- Fix scheduler mode inference: add `"mop"` as a logged mode when `fan_speed=OFF`; currently all non-mop dispatches log as `"vacuum"` even when mop-only

## Capabilities

### New Capabilities

_(none — this extends existing capabilities)_

### Modified Capabilities

- `web-dashboard`: New clean mode selector UI in Clean Rooms panel and Start Clean; updated auto-log mode inference to support "mop" alongside "vacuum" and "both"
- `vacuum-client`: New `WaterFlow.VAC_THEN_MOP` enum member

## Impact

- `src/vacuum/client.py`: Add one enum member
- `src/vacuum/dashboard.py`: Clean mode dropdown HTML/JS in two panels; mode inference logic in `api_rooms_clean` and `api_action`; `VAC_THEN_MOP` in water-flow select options
- No changes to `scheduler.py`, `mcp_server.py`, or `cli.py`
- No new API endpoints; no breaking changes to existing API contracts
