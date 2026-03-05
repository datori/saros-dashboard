## Why

The dashboard displays consumable life percentages (main brush, side brush, filter, sensor) but provides no way to reset them after maintenance. The sensor is currently at ~0% and needs a reset after cleaning; the same will be needed for other consumables over time.

## What Changes

- Add `reset_consumable(attribute)` async method to `VacuumClient` using `ConsumableTrait.reset_consumable`
- Add `POST /api/consumables/reset/{attribute}` endpoint to the dashboard API
- Add reset buttons next to each consumable progress bar in the dashboard UI

## Capabilities

### New Capabilities
- `consumable-reset`: Reset individual consumable timers (sensor_dirty_time, filter_work_time, side_brush_work_time, main_brush_work_time) via the dashboard UI and REST API

### Modified Capabilities
- `web-dashboard`: Add reset button UI to the consumables panel and expose the new reset API endpoint

## Impact

- `src/vacuum/client.py`: New `reset_consumable` method
- `src/vacuum/dashboard.py`: New API endpoint + UI button per consumable
- No new dependencies
