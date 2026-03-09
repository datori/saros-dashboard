## Why

The scheduler tracks vacuum and mop intervals separately and builds a cross-mode priority queue, but at dispatch time it calls `clean_rooms()` with no settings — the device uses whatever defaults happen to be active. A "mop" dispatch is identical to a "vacuum" dispatch. To actually differentiate modes, the system needs per-mode device settings that are applied before dispatching.

## What Changes

- Add a `dispatch_settings` table in the scheduler DB storing per-mode device settings (fan_speed, mop_mode, water_flow, route)
- Ship sensible defaults: vacuum mode uses `fan_speed=balanced, water_flow=off`; mop mode uses `fan_speed=off, mop_mode=standard, water_flow=medium`
- Update `_check_dispatch()` to apply the configured settings when dispatching a clean
- Add API endpoints to view and update dispatch settings per mode
- Add a dashboard UI section to configure dispatch settings

## Capabilities

### New Capabilities
- `dispatch-settings`: Per-mode device settings applied by the scheduler when dispatching auto-cleans

### Modified Capabilities
- `clean-windows`: Dispatch loop applies mode-specific settings before cleaning

## Impact

- `src/vacuum/scheduler.py`: New table, CRUD functions for dispatch settings
- `src/vacuum/dashboard.py`: Updated dispatch logic, new API endpoints, new UI section
